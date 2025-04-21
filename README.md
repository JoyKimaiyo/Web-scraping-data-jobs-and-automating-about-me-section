# 📊 Web Scraping Data Jobs & Automating Cover Letter Generation

This project scrapes data jobs (Data Analyst, Data Scientist, Data Engineer, etc.) from **LinkedIn** using `web.py` and stores the data in **MySQL**. It also includes a **Streamlit app** that uses **Hugging Face AI** to generate a professional cover letter and "About Me" section.

---

## 🔧 Features

- 🔍 Scrape LinkedIn job listings based on keywords, location, and filters
- 🧠 Use Hugging Face models to generate cover letters and About Me content
- 📊 Simple UI via Streamlit (`data_app.py`)
- 💾 Data saved in MySQL for easy querying and analysis

---

## ⚙️ Configuration

Update your `config.json` with your preferred settings:

```json
{
  "keywords": ["data analyst", "data scientist", "data engineer"],
  "locations": ["", "Remote", "Onsite", "Hybrid"],
  "date_range": "604800", 
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  "languages": ["en"],
  "desc_words": ["senior", "principal"],
  "days_to_scrape": 7
}
```

---

## 🗃️ MySQL Setup

Create a MySQL database and table for storing scraped jobs:

```sql
-- Log in to MySQL
mysql -u your_username -p

-- Create database and table
CREATE DATABASE job_scraper;

USE job_scraper;

CREATE TABLE jobs (
    title TEXT,
    company TEXT,
    location TEXT,
    link TEXT,
    source TEXT,
    date_posted TEXT,
    work_type TEXT,
    employment_type TEXT,
    description TEXT
);
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/JoyKimaiyo/Web-scraping-data-jobs-and-automating-about-me-section
cd Web-scraping-data-jobs-and-automating-about-me-section
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Scraper

```bash
python main.py
```

### 4. Launch the Streamlit App

```bash
streamlit run data_app.py
```

---

## 🤖 Streamlit App Features

After scraping jobs, open the Streamlit app (`data_app.py`) to:

- ✉️ Generate a **custom cover letter**
- 🧍‍♂️ Auto-generate an **About Me** section
- 🧠 Powered by Hugging Face models

---

## 📌 Notes

- Use environment variables for storing your MySQL credentials securely
- LinkedIn may block frequent scrapers — implement delays and use responsibly
- This project is for educational and personal use only

---

## 🧑‍💻 Author

**Joy Kimaiyo**

- GitHub: [@JoyKimaiyo](https://github.com/JoyKimaiyo)
- Medium: [@joykimaiyo](https://medium.com/@joykimaiyo)

---
