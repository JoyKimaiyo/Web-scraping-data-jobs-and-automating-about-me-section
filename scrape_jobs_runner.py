import os
import json
import pandas as pd
import mysql.connector
import logging
from jobspy import scrape_jobs
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load config
def load_config(config_file):
    with open(config_file) as file:
        return json.load(file)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Timmy@2013"),
        database=os.getenv("DB_NAME", "job_scraper")
    )

# General sanitization
def sanitize(value):
    if pd.isna(value) or value in [None, "nan", "NaN"]:
        return "N/A"
    return str(value).strip()

# Date sanitization
def sanitize_date(value):
    try:
        if pd.isna(value) or value in ["N/A", "nan", "NaN", None]:
            return None
        if isinstance(value, str):
            try:
                parsed_date = datetime.fromisoformat(value)
            except ValueError:
                parsed_date = datetime.strptime(value, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
        return str(value)
    except Exception as e:
        logger.warning(f"⚠️ Date parsing failed for value '{value}': {e}")
        return None

# Save to MySQL
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
            job.get("source"),
            sanitize_date(job.get("date_posted")),
            job.get("work_type"),
            job.get("employment_type"),
            job.get("description")
        )

        cursor.execute(query, values)
        conn.commit()
        logger.info(f"✅ Inserted: {job['title']} at {job['company']} from {job['source']}")
    except Exception as e:
        logger.error(f"❌ Failed to insert into DB: {e}")
    finally:
        cursor.close()
        conn.close()

# Main scraping logic
def scrape_and_store(config):
    sites = ['linkedin', 'indeed']

    for site in sites:
        for keyword in config['keywords']:
            for location in config['locations']:
                try:
                    logger.info(f"🔎 Scraping {site} for '{keyword}' in '{location}'")

                    jobs = scrape_jobs(
                        site_name=[site],
                        search_term=keyword,
                        location=location,
                        results_wanted=20,
                        hours_old=int(config['days_to_scrape']) * 24,
                        country_indeed='USA',
                        linkedin_fetch_description=True
                    )

                    logger.info(f"📊 Found {len(jobs)} jobs for '{keyword}' in '{location}' on {site}")

                    if jobs.empty:
                        continue

                    df = jobs.copy()

                    # Filter by description keywords if provided
                    if config.get("desc_words"):
                        desc_words = config["desc_words"]
                        df = df[df["description"].str.contains('|'.join(desc_words), case=False, na=False)]
                        logger.info(f"📉 Filtered down to {len(df)} jobs after description keyword filtering")

                    for _, row in df.iterrows():
                        job = {
                            "title": sanitize(row.get("title")),
                            "company": sanitize(row.get("company")),
                            "location": sanitize(row.get("location")),
                            "job_url": sanitize(row.get("job_url")),
                            "source": site,
                            "date_posted": row.get("date_posted"),
                            "work_type": sanitize(row.get("work_type")),
                            "employment_type": sanitize(row.get("employment_type")),
                            "description": sanitize(row.get("description"))
                        }
                        save_to_db(job)

                except Exception as e:
                    logger.error(f"❌ Error scraping for '{keyword}' in '{location}' on {site}: {e}")

    logger.info("🎯 All jobs inserted successfully.")

# Entry point
if __name__ == "__main__":
    config_path = "config.json"
    config = load_config(config_path)
    scrape_and_store(config)



