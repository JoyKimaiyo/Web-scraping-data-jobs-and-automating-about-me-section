import asyncio
from playwright.async_api import async_playwright
from db.mysql_connector import insert_job
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
COOKIE_PATH = Path("../config/linkedin_cookies.json")

async def scrape_linkedin_jobs(keyword="data analyst", location="remote"):
    """Scrape LinkedIn jobs and store in MySQL"""
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=COOKIE_PATH)
            page = await context.new_page()

            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}"
            await page.goto(search_url)
            await page.wait_for_timeout(5000)

            jobs = await page.query_selector_all(".jobs-search__results-list li")

            for job in jobs[:10]:  # Limit to 10 jobs for testing
                try:
                    title = await job.eval_on_selector("h3", "el => el.innerText")
                    company = await job.eval_on_selector("h4", "el => el.innerText")
                    location = await job.eval_on_selector(".job-search-card__location", "el => el.innerText", None)
                    link = await job.eval_on_selector("a", "el => el.href")

                    if title and company and link:
                        insert_job((
                            title.strip(),
                            company.strip(),
                            location.strip() if location else None,
                            link,
                            'linkedin',
                            None  # date_posted can be None
                        ))
                        logger.info(f"Found job: {title} at {company}")

                except Exception as e:
                    logger.warning(f"Failed to process a job listing: {e}")

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_linkedin_jobs())