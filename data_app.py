import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# Load environment variables
load_dotenv()

# --- Gemini API Function ---
def generate_with_gemini(prompt):
    api_key = st.secrets["GM_API_TOKEN"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "⚠️ Error: Empty response from Gemini API"

    except requests.exceptions.HTTPError as http_err:
        return f"⚠️ HTTP Error: {http_err} | Response: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"⚠️ API Connection Error: {str(e)}"
    except Exception as e:
        return f"⚠️ Unexpected Error: {str(e)}"

# --- Load & Clean Jobs from CSV (Cached) ---
@st.cache_data
def simplify_title(title):
    title_lower = str(title).lower()
    if 'data scientist' in title_lower:
        return 'Data Scientist'
    elif 'data engineer' in title_lower:
        return 'Data Engineer'
    elif 'data analyst' in title_lower or 'data analytics' in title_lower:
        return 'Data Analyst'
    elif 'machine learning' in title_lower or 'ml engineer' in title_lower:
        return 'Machine Learning Engineer'
    else:
        return title

@st.cache_data
def fetch_and_clean_jobs(role):
    try:
        df = pd.read_csv("clean_jobs.csv")
        df.drop(columns=['work_type', 'employment_type'], inplace=True, errors='ignore')
        df['title'] = df['title'].apply(simplify_title)
        df = df[df['title'].str.contains(role, case=False, na=False)]
        df = df.dropna(subset=['description'])
        df['description'] = df['description'].str.strip()
        df.drop_duplicates(subset=['title', 'description'], inplace=True)
        return df
    except Exception as e:
        st.error(f"CSV Load Error: {str(e)}")
        return pd.DataFrame()

# --- NLP Keyword Extraction (Cached) ---
@st.cache_data
def extract_keywords(texts, n=10):
    try:
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
    except Exception as e:
        st.error(f"Keyword Extraction Error: {str(e)}")
        return []

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

    *Powered by Gemini AI and NLP analysis*
    """)
    if 'last_api_response' in st.session_state:
        with st.expander("Last API Response"):
            st.json(st.session_state.last_api_response)
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Select your target role and experience level")
    st.markdown("2. Click 'Generate' to create content")
    st.markdown("3. Copy the results to your resume")

st.title("AI-Powered CV Builder 📝")
st.markdown("---")

# Role Selection
col1, col2 = st.columns(2)
with col1:
    role = st.selectbox("Select Role", ["Data Engineer", "Data Analyst", "Data Scientist", "Machine Learning Engineer"])
with col2:
    level = st.selectbox("Select Level", ["Entry Level", "Junior", "Senior"])

# Main Generation
if st.button("Generate Professional About Me", type="primary"):
    jobs_df = fetch_and_clean_jobs(role)

    if not jobs_df.empty:
        job_descriptions = jobs_df["description"].dropna().tolist()
        combined_descriptions = " ".join(job_descriptions)

        with st.spinner("Analyzing job descriptions and generating content..."):
            st.subheader("☁️ Word Cloud for This Role")
            # Generate and display word cloud
            wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords='english').generate(combined_descriptions)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

            st.markdown("---")

            # About Me Generation
            prompt = f"""You are a professional CV writer. Generate a compelling 'About Me' section for a {level} {role} based on these job requirements:

Job Descriptions:
{combined_descriptions}

Guidelines:
1. Length: 3-4 sentences
2. Style: Professional but approachable
3. Include: Core skills, achievements, and value proposition
4. Format: Complete sentences, no bullet points
5. Avoid: Generic phrases like "team player"
"""
            about_me = generate_with_gemini(prompt)
            st.subheader("✨ Your AI-Tailored 'About Me'")
            st.success(about_me)

            skill_prompt = f"""
Extract the top 5 technical skills for a {level} {role} from these job descriptions:

{combined_descriptions}

Format:
- Markdown bullet list
- Each skill should include a 1-sentence explanation
"""
            skills = generate_with_gemini(skill_prompt)

            soft_skill_prompt = f"""
Based on the job descriptions, list 4 soft skills that are most valuable for a {level} {role}.

Format:
- Markdown bullet list
- Each soft skill should include a 1-sentence explanation
"""
            soft_skills = generate_with_gemini(soft_skill_prompt)

            st.subheader("💼 Top Skills for This Role")
            st.markdown("#### 🛠️ Technical Skills")
            st.info(skills)

            st.markdown("#### 🤝 Soft Skills")
            st.info(soft_skills)
    else:
        st.error("No job descriptions found for this role.")

# Cover Letter Generator
st.markdown("---")
if st.checkbox("Generate a Full Cover Letter"):
    cover_prompt = f"""
Write a professional cover letter for a {level} {role} position.

Requirements:
- Length: 3-4 paragraphs
- Tone: Confident but not arrogant
- Structure:
  1. Opening: Express enthusiasm for the role
  2. Body: Match skills to job requirements
  3. Closing: Call to action + contact info
- Include: 2-3 specific achievements
- Avoid: Generic phrases like "I'm perfect for this role"

Job Context:
{combined_descriptions if 'combined_descriptions' in locals() else 'No job descriptions loaded'}
"""
    cover_letter = generate_with_gemini(cover_prompt)
    st.subheader("📝 Cover Letter")
    st.write(cover_letter)

