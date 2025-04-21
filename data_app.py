import streamlit as st
import pymysql
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import plotly.express as px
import numpy as np

# Load environment variables
load_dotenv()

# --- Hugging Face Inference Function ---
def generate_with_huggingface(prompt):
    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"}

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 250}  # Limit to 250 to avoid errors
    }

    response = requests.post(api_url, headers=headers, json=payload)
    try:
        result = response.json()
    except ValueError:
        return "⚠️ Error: Unable to decode Hugging Face response."

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

# --- NLP Keyword Analysis ---
def extract_keywords(texts, n=10):
    combined_text = " ".join(texts)
    words = [word.lower() for word in combined_text.split() if word.isalpha() and len(word) > 2]
    word_freq = Counter(words)

    vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = np.sum(tfidf_matrix, axis=0).A1

    keywords = {word: score * 5 + word_freq.get(word, 0) for word, score in zip(feature_names, tfidf_scores)}
    sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    return [word[0] for word in sorted_keywords[:n]]

# --- Streamlit UI ---
st.set_page_config(page_title="AI CV Builder", page_icon="📝", layout="wide")

with st.sidebar:
    st.title("📝 AI-Powered CV Builder")
    st.markdown("""
    **Create the perfect resume** using AI and real job market data!

    This tool:
    - Analyzes job descriptions for your target role
    - Identifies key skills and keywords
    - Generates tailored content for your CV

    *Powered by Hugging Face AI and NLP analysis*
    """)

    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Select your target role and experience level")
    st.markdown("2. Click 'Generate' to create content")
    st.markdown("3. Copy the results to your resume")
    st.markdown("---")
    st.markdown("🔍 *The keyword analysis shows what terms appear most frequently in real job postings*")

st.title("AI-Powered CV Builder (Hugging Face Edition) 🤖")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    role = st.selectbox("Select Role", ["Data Engineer", "Data Analyst", "Data Scientist"])
with col2:
    level = st.selectbox("Select Level", ["Entry Level", "Junior", "Senior"])

if st.button("Generate Professional About Me", type="primary"):
    jobs_df = fetch_jobs(role)

    if not jobs_df.empty:
        job_descriptions = jobs_df["description"].tolist()
        combined_descriptions = " ".join(job_descriptions)

        with st.spinner("Analyzing job descriptions and generating content..."):
            st.subheader("🔍 Top Keywords for This Role")
            keywords = extract_keywords(job_descriptions)

            fig = px.bar(x=keywords[::-1], y=list(range(1, len(keywords)+1))[::-1], orientation='h',
                         labels={'x': 'Keyword', 'y': 'Importance Rank'}, title='Most Important Keywords')
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("**Keywords to include in your resume:**")
            cols = st.columns(5)
            for i, keyword in enumerate(keywords[:10]):
                cols[i%5].markdown(f"🔹 `{keyword}`")

            st.markdown("---")

            prompt = f"""
            You are a professional CV writer. Generate a compelling and concise 'About Me' section for a {level} {role}.
            Style it like this example:

            '''Driven marketing analyst, passionate about leveraging data to solve real-world challenges. Proficient in Python, Power BI, Excel, SQL, Apache Kafka, Airflow, and Bash scripting for data analysis, streaming, automation, and machine learning. Skilled in data visualization using Power BI, Streamlit, and Matplotlib, with experience in building interactive BI dashboards and managing databases like MySQL and PostgreSQL. In addition to Git and GitHub for version control. Committed to transforming data into actionable insights that drive organizational success.'''

            Now generate a similar About Me tailored to a {level} {role} based on this job description:
            {combined_descriptions}
            """
            about_me = generate_with_huggingface(prompt)

            st.subheader("✨ Your AI-Tailored 'About Me'")
            st.success(about_me)

            st.subheader("💼 Top Skills for This Role")
            skill_prompt = f"Extract top 5 technical skills from this job description: {combined_descriptions}"
            skills = generate_with_huggingface(skill_prompt)
            st.info(skills)
    else:
        st.error("No job descriptions found for this role.")

st.markdown("---")
if st.checkbox("Generate a Full Cover Letter"):
    cover_prompt = f"Write a full professional cover letter for a {level} {role} applying to a data-focused company. Be concise, results-driven, and enthusiastic."
    cover_letter = generate_with_huggingface(cover_prompt)
    st.subheader("📝 Cover Letter")
    st.write(cover_letter)

