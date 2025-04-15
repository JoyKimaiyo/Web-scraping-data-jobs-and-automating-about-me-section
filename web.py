import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))
from db_connect import insert_job
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COOKIE_PATH = Path(__file__).resolve().parent / "config" / "linkedin_cookies.json"

async def scrape_linkedin_jobs(keyword="data analyst", location_type="remote"):
    """Modern LinkedIn scraper with adaptive selectors"""
    async with async_playwright() as p:
        browser = None
        try:
            # Launch with visible browser for debugging
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ],
                slow_mo=1000  # Slow execution for observation
            )
            
            context = await browser.new_context(
                storage_state=COOKIE_PATH if COOKIE_PATH.exists() else None,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            
            page = await context.new_page()
            
            # Build search URL
            location_filters = {
                "remote": "&f_WT=2",
                "hybrid": "&f_WT=3",
                "on site": "&f_WT=1"
            }
            location_filter = location_filters.get(location_type.lower(), "")
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}{location_filter}"
            
            logger.info(f"Navigating to: {search_url}")
            await page.goto(search_url, timeout=60000)
            
            # Check for blocking mechanisms
            if await page.query_selector('input#username'):
                logger.error("⚠️ Login page detected - your cookies may be expired")
                return
            if await page.query_selector('#captcha-internal'):
                logger.error("⚠️ CAPTCHA detected - LinkedIn is blocking you")
                return

            # Wait for page to fully load
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # DEBUG: Save full page HTML for inspection
            html_content = await page.content()
            with open("linkedin_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("Saved page HTML to linkedin_page.html")

            # New approach to find jobs - using more generic selectors
            jobs = await find_jobs_adaptively(page)
            
            if not jobs:
                logger.error("❌ No jobs found after trying multiple approaches")
                await page.screenshot(path="debug_no_jobs.png", full_page=True)
                logger.info("Saved full page screenshot to debug_no_jobs.png")
                logger.info("Please inspect linkedin_page.html and debug_no_jobs.png")
                logger.info("Then update the selectors in the script accordingly")
                return

            logger.info(f"✅ Found {len(jobs)} job listings")
            
            # Process job listings
            for job in jobs[:10]:  # Process first 10 jobs
                try:
                    # Use more generic selectors that are less likely to change
                    title = await job.evaluate('''el => {
                        const titleEl = el.querySelector('a[href*="/jobs/view/"]') || 
                                       el.querySelector('a[data-tracking-control-name*="job-card"]') ||
                                       el.querySelector('a[data-tracking-id*="job-card-title"]');
                        return titleEl ? titleEl.innerText.trim() : null;
                    }''')
                    
                    company = await job.evaluate('''el => {
                        const companyEl = el.querySelector('span[class*="company"]') || 
                                         el.querySelector('a[data-tracking-control-name*="company"]') ||
                                         el.querySelector('span[class*="employer"]');
                        return companyEl ? companyEl.innerText.trim() : null;
                    }''')
                    
                    location = await job.evaluate('''el => {
                        const locEl = el.querySelector('span[class*="location"]') || 
                                      el.querySelector('span[class*="workplace"]') ||
                                      el.querySelector('span[class*="geo"]');
                        return locEl ? locEl.innerText.trim() : null;
                    }''')
                    
                    link = await job.evaluate('''el => {
                        const linkEl = el.querySelector('a[href*="/jobs/view/"]') || 
                                       el.querySelector('a[data-tracking-control-name*="job-card"]');
                        return linkEl ? linkEl.href : null;
                    }''')
                    
                    if title and company and link:
                        logger.info(f"Found job: {title} at {company} ({location})")
                        insert_job((
                            title,
                            company,
                            location if location else None,
                            link,
                            'linkedin',
                            None
                        ))
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process job: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Scraping failed: {str(e)}")
            if browser:
                await page.screenshot(path="final_error.png", full_page=True)
                logger.info("Saved full page screenshot to final_error.png")
        finally:
            if browser:
                await browser.close()

async def find_jobs_adaptively(page):
    """Try multiple approaches to find job listings"""
    # List of container selectors to try (ordered by likelihood)
    container_selectors = [
        'main.scaffold-layout__main',  # Main content area
        'div.jobs-search-results-list',  # Jobs list container
        'div.scaffold-layout__list-container',  # Alternative container
        'ul.jobs-search__results-list',  # Older container
        'div.jobs-search-results'  # Another alternative
    ]
    
    # List of job item selectors to try
    job_selectors = [
        'div.job-card-container',  # Newest job card
        'li.jobs-search-results__list-item',  # List item
        'div.job-search-card',  # Older card
        'div.base-card',  # Generic card
        'section.job-card'  # Alternative
    ]
    
    for container_selector in container_selectors:
        container = await page.query_selector(container_selector)
        if container:
            logger.info(f"Found container with: {container_selector}")
            
            # Scroll within container to load more jobs
            await container.evaluate('''container => {
                container.scrollTop = container.scrollHeight;
            }''')
            await page.wait_for_timeout(2000)  # Wait for loading
            
            for job_selector in job_selectors:
                jobs = await container.query_selector_all(job_selector)
                if jobs:
                    logger.info(f"Found {len(jobs)} jobs with: {job_selector}")
                    return jobs
    
    # Fallback: Try finding any job-like elements
    logger.info("Trying fallback selectors...")
    fallback_jobs = await page.query_selector_all('''
        a[href*="/jobs/view/"], 
        div[data-tracking-id*="job-card"],
        section[class*="job-card"]
    ''')
    
    if fallback_jobs:
        logger.info(f"Found {len(fallback_jobs)} jobs with fallback selectors")
        return fallback_jobs
    
    return []

if __name__ == "__main__":
    asyncio.run(scrape_linkedin_jobs())