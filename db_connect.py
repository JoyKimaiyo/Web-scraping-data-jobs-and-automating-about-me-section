import mysql.connector
import logging
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('../config/.env')

def get_connection():
    """Create and return MySQL database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Timmy@2013"),
            database=os.getenv("DB_NAME", "job_scraper")
        )
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        raise

def insert_job(data):
    """Insert job data into MySQL database"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO jobs (title, company, location, link, source, date_posted)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title)
        """
        cursor.execute(sql, data)
        conn.commit()
        logger.info(f"Inserted job: {data[0]} at {data[1]}")
        
    except mysql.connector.Error as err:
        logger.error(f"Failed to insert job: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
