# 📝 AI CV and Cover Letter Builder

Crafting a compelling cover letter and summary for a job application can be intimidating. It requires distilling your skills, experience, and personality into a concise narrative that stands out — especially in a world where companies use keyword-driven AI to screen candidates.

This project simplifies the process by:
- Scraping job data (Data Analyst, Data Scientist, Data Engineer, etc.) from **LinkedIn** using `web.py`
- Storing the data in a **MySQL** database
- Analyzing job descriptions using **Natural Language Processing (NLP)** to extract and weigh keywords
- Using **Gemini AI** in a **Streamlit** app to generate tailored cover letters and "About Me" sections

---

## 🔧 Features

- 🔍 Scrape LinkedIn job listings based on keyword, location, and filters
- 🧠 Extract key skills using NLP and TF-IDF
- ✨ Generate cover letters and About Me sections using **Gemini AI**
- 📊 Interactive UI built with **Streamlit**
- 💾 Store job data in **MySQL** for reuse and analysis

---

## ⚙️ Configuration

Customize your scraping behavior by editing `config.json`:

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
- 🧠 Powered by Gemini

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
