import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Timmy@2013',
    database='job_scraper'
)

df = pd.read_sql("SELECT * FROM jobs", conn)
df.to_csv("clean_jobs.csv", index=False)
print("Exported to clean_jobs.csv")
