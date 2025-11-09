import streamlit as st
import pandas as pd
from final_recommend_eng import SHLRecommendationEngine
import json

# Page config
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="https://www.linkedin.com/in/shashi-kumar-banoth-a0a287276/",
    layout="wide"
)

# Initialize engine (cached)
@st.cache_resource
def load_engine():
    return SHLRecommendationEngine()

engine = load_engine()

# Session state for query
if 'current_query' not in st.session_state:
    st.session_state.current_query = ""

# Header
st.title("🎯 SHL Assessment Recommendation System")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    This system recommends relevant SHL assessments based on:
    - Job descriptions
    - Natural language queries
    - Skill requirements
    """)
    
    st.header("📊 Statistics")
    try:
        with open('preprocessed_assessments.json', 'r') as f:
            assessments = json.load(f)
        st.metric("Total Assessments", len(assessments))
    except:
        st.metric("Total Assessments", "N/A")

# Main input
query = st.text_area(
    "Enter your query or job description:",
    value=st.session_state.current_query,
    height=150,
    placeholder="Example: I am hiring for Java developers who can also collaborate effectively with my business teams."
)

# Number of recommendations
top_k = st.slider("Number of recommendations:", 5, 10, 10)

# Get recommendations button
if st.button("🔍 Get Recommendations", type="primary"):
    if not query.strip():
        st.error("⚠️ Please enter a query!")
    else:
        with st.spinner("Finding best assessments..."):
            recommendations = engine.get_recommendations(query, top_k=top_k)
        
        if recommendations:
            st.success(f"✅ Found {len(recommendations)} relevant assessments")
            
            # Display as table (WITHOUT duration)
            df = pd.DataFrame(recommendations)
            
            # Format for display - NO DURATION COLUMN
            display_df = pd.DataFrame({
                '№': range(1, len(df) + 1),
                'Assessment Name': df['name'],
                'Test Types': df['test_type'].apply(lambda x: ', '.join(x)),
                'URL': df['url'].apply(lambda x: f'[View Assessment]({x})')
            })
            
            st.markdown("### 📋 Recommended Assessments")
            st.markdown(display_df.to_markdown(index=False))
            
            # Detailed view in expanders
            st.markdown("### 📖 Detailed Information")
            for i, rec in enumerate(recommendations, 1):
                with st.expander(f"{i}. {rec['name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Test Types:**", ', '.join(rec['test_type']))
                        st.write("**Adaptive Support:**", "✅" if rec['adaptive_support'] else "❌")
                    with col2:
                        st.write("**Remote Support:**", "✅" if rec['remote_support'] else "❌")
                        if rec.get('duration'):
                            st.write("**Duration:**", f"{rec['duration']} minutes")
                    
                    st.write("**Description:**")
                    st.write(rec['description'][:300] + "..." if len(rec['description']) > 300 else rec['description'])
                    st.markdown(f"**🔗 [Open Assessment Page]({rec['url']})**")
        else:
            st.warning("No recommendations found. Try a different query.")

# Example queries
st.markdown("---")
st.markdown("### 💡 Try These Example Queries")

col1, col2 = st.columns(2)

examples = [
    "I am hiring for Java developers who can also collaborate effectively with my business teams.",
    "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript.",
    "I want to hire a Senior Data Analyst with 5 years of experience and expertise in SQL, Excel and Python.",
    "Need a QA Engineer with experience in Selenium, Java, and SQL.",
    "Looking for a COO who is culturally a right fit for our company.",
    "Content Writer required, expert in English and SEO."
]

for i, example in enumerate(examples):
    col = col1 if i % 2 == 0 else col2
    with col:
        if st.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.current_query = example
            st.rerun()

# Footer
st.markdown("---")
st.markdown("Built for SHL AI Intern Assignment | Powered by TF-IDF + Training Boost")
