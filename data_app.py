import streamlit as st
import pymysql
import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Hugging Face Inference Function ---
def generate_with_huggingface(prompt):
    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"}

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 200}
    }

    response = requests.post(api_url, headers=headers, json=payload)
    result = response.json()

    if isinstance(result, list) and 'generated_text' in result[0]:
        return result[0]['generated_text']
    elif isinstance(result, dict) and 'error' in result:
        return f"⚠️ Hugging Face Error: {result['error']}"
    else:
        return "⚠️ Unexpected response format."

# --- Fetch Jobs from MySQL ---
def fetch_jobs(role):
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Timmy@2013"),
        database=os.getenv("DB_NAME", "job_scraper")
    )
    query = f"""
        SELECT description FROM jobs
        WHERE title LIKE '%{role}%'
    """
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# --- Streamlit UI ---
st.title("AI-Powered CV Builder (Hugging Face Edition) 🤖")
role = st.selectbox("Select Role", ["Data Engineer", "Data Analyst", "Data Scientist"])
level = st.selectbox("Select Level", ["Entry Level", "Junior", "Senior"])

if st.button("Generate Professional About Me"):
    jobs_df = fetch_jobs(role)

    if not jobs_df.empty:
        job_descriptions = " ".join(jobs_df["description"].tolist())

        # Generate About Me
        prompt = f"""
        You are a professional CV writer. Generate a concise, compelling "About Me" section for a {level} {role} based on these job requirements:
        {job_descriptions}
        Focus on:
        - 3 key skills (technical + soft)
        - Industry-relevant achievements
        - Tailored to {level} level
        """
        about_me = generate_with_huggingface(prompt)

        st.subheader("Your AI-Tailored 'About Me'")
        st.write(about_me)

        # Skill Extraction
        st.subheader("Top Skills for This Role")
        skill_prompt = f"Extract top 5 technical skills from this job description: {job_descriptions}"
        skills = generate_with_huggingface(skill_prompt)
        st.write(skills)
    else:
        st.error("No job descriptions found for this role.")

# Optional: Cover Letter Generator
if st.checkbox("Generate a Cover Letter Snippet"):
    cover_prompt = f"Write a 3-sentence cover letter snippet for a {level} {role} applying to a data-focused company."
    cover_letter = generate_with_huggingface(cover_prompt)
    st.subheader("Cover Letter Snippet")
    st.write(cover_letter)
