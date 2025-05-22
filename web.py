import os
import time as tm
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import logging
import random
import mysql.connector
import asyncio
from asyncio import Semaphore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

sem = Semaphore(6)  # Increased concurrency

# --- CONFIGURATION ---
def load_config(config_file):
    with open(config_file) as file:
        return json.load(file)

# --- DATABASE CONNECTION ---
def get_db_connection():
    return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Timmy@2013"),
            database=os.getenv("DB_NAME", "job_scraper")
    )

# --- SAVE JOB TO DATABASE ---
def save_to_db(job):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO jobs (title, company, location, link, source, date_posted, work_type, employment_type, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE description = VALUES(description)
        """

        values = (
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("job_url"),
            "LinkedIn",
            job.get("date"),
            job.get("work_type", "N/A"),
            job.get("employment_type", "N/A"),
            job.get("description", "N/A")
        )

        cursor.execute(query, values)
        conn.commit()
        logger.info(f"✅ Inserted: {job['title']} at {job['company']}")
    except Exception as e:
        logger.error(f"❌ Failed to insert into DB: {e}")
    finally:
        cursor.close()
        conn.close()

# --- JOB CARD SCRAPER ---
def get_job_cards(config):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    jobs = []
    session = requests.Session()

    for keyword in config['keywords']:
        for location in config['locations']:
            location_param = f"&location={location}" if location else ""
            url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}{location_param}&f_TPR=r{config['date_range']}&position=1&pageNum=0"

            try:
                tm.sleep(random.uniform(1, 2))
                response = session.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                job_elements = soup.find_all("div", class_="base-card")

                for job_elem in job_elements:
                    try:
                        link_tag = job_elem.find("a", class_="base-card__full-link")
                        if not link_tag or not link_tag.get("href"):
                            continue

                        title = job_elem.find("h3", class_="base-search-card__title")
                        company = job_elem.find("h4", class_="base-search-card__subtitle")
                        location_span = job_elem.find("span", class_="job-search-card__location")
                        time_tag = job_elem.find("time")

                        work_type = "N/A"
                        if location_span:
                            location_text = location_span.text.strip().lower()
                            if "remote" in location_text:
                                work_type = "Remote"
                            elif "onsite" in location_text:
                                work_type = "Onsite"
                            elif "hybrid" in location_text:
                                work_type = "Hybrid"

                        job = {
                            "job_url": link_tag["href"].split("?")[0],
                            "title": title.text.strip() if title else "N/A",
                            "company": company.text.strip() if company else "N/A",
                            "location": location_span.text.strip() if location_span else "N/A",
                            "date": time_tag["datetime"] if time_tag else str(datetime.today().date()),
                            "work_type": work_type
                        }
                        jobs.append(job)

                    except Exception as e:
                        logger.error(f"Error parsing job element: {e}")
                        continue

            except requests.RequestException as e:
                logger.error(f"Error fetching jobs for {keyword} in {location or 'global'}: {e}")
                continue

    return jobs

# --- RETRY GOTO ---
async def try_goto(page, url, retries=1):
    for attempt in range(retries + 1):
        try:
            await page.goto(url, timeout=90000, wait_until='domcontentloaded')
            return True
        except Exception as e:
            if attempt == retries:
                raise
            await page.wait_for_timeout(random.randint(1000, 3000))

# --- JOB DETAILS SCRAPER ---
async def scrape_job_details(page, url):
    await try_goto(page, url)

    if "captcha" in page.url or await page.locator("input[name=captcha]").count() > 0:
        logger.warning(f"🛑 CAPTCHA detected at {url}")
        return {
            "description": "CAPTCHA Blocked",
            "work_type": "N/A",
            "employment_type": "N/A"
        }

    try:
        await page.wait_for_selector("div.description__text", timeout=5000)
        description = await page.locator("div.description__text").inner_text()
    except:
        description = "N/A"

    job_info = {"description": description.strip()}

    try:
        job_info["work_type"] = await page.locator("span:has-text('Work type') + span").inner_text()
    except:
        job_info["work_type"] = "N/A"

    try:
        job_info["employment_type"] = await page.locator("span:has-text('Employment type') + span").inner_text()
    except:
        job_info["employment_type"] = "N/A"

    return job_info

# --- JOB HANDLER ---
async def process_job(job, context):
    async with sem:
        try:
            page = await context.new_page()
            details = await scrape_job_details(page, job["job_url"])
            job.update(details)
            save_to_db(job)
            await page.close()
        except Exception as e:
            logger.error(f"❌ Error processing job {job['job_url']}: {e}")

# --- MAIN SCRAPER FUNCTION ---
async def run_scraper(config_path):
    start_time = tm.perf_counter()

    try:
        config = load_config(config_path)
        logger.info(f"Starting scraper with config: {config}")

        logger.info("Fetching job listings from LinkedIn...")
        all_jobs = get_job_cards(config)
        logger.info(f"Found {len(all_jobs)} total jobs in initial search")

        if not all_jobs:
            logger.warning("No jobs found. Possible issues:")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True
            )

            await stealth_async(context)

            tasks = [process_job(job, context) for job in all_jobs]
            await asyncio.gather(*tasks)

            await browser.close()

    except Exception as e:
        logger.error(f"Fatal error in scraper: {e}")
    finally:
        end_time = tm.perf_counter()
        logger.info(f"Scraping completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total jobs processed: {len(all_jobs)}")

# --- ENTRY POINT ---
if __name__ == "__main__":
    asyncio.run(run_scraper("config.json"))