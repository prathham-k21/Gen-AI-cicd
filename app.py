import os
import time
import logging
import streamlit as st
from dotenv import load_dotenv

# ==============================================================================
# Logging Configuration (Task 7: Monitoring and Logging)
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("TaskAutomationAgent")

# Load local environment variables if available (.env)
load_dotenv()

# ==============================================================================
# App Setup & Configuration
# ==============================================================================
st.set_page_config(
    page_title="AI Research Brief Agent",
    page_icon="🤖",
    layout="centered"
)

# Fetch API Key from environment or Streamlit secrets
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    if not API_KEY:
        st.warning("⚠️ GEMINI_API_KEY not found in environment.")
        user_key = st.text_input("Enter Gemini API Key:", type="password")
        if user_key:
            API_KEY = user_key
    else:
        st.success("✅ Gemini API Key detected.")
    
    st.markdown("---")
    st.markdown("### 📌 Experiment 10: MLOps")
    st.markdown(
        "- **Framework**: Streamlit & Gemini API\n"
        "- **Workflow**: Search -> Summarize\n"
        "- **Container**: Docker\n"
        "- **CI/CD**: GitHub Actions"
    )

# ==============================================================================
# Agent Workflow Functions
# ==============================================================================
def search_duckduckgo(topic: str, max_results: int = 5) -> str:
    """Queries DuckDuckGo and formats raw text results."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
            
        ddgs = DDGS()
        results = list(ddgs.text(topic, max_results=max_results))
        
        if not results:
            return "No search results found."
            
        formatted_snippets = []
        for i, item in enumerate(results, start=1):
            title = item.get("title", "")
            body = item.get("body", "")
            formatted_snippets.append(f"Source {i}: {title}\nSnippet: {body}")
            
        return "\n\n".join(formatted_snippets)
    except Exception as e:
        logger.error(f"Search failed for topic '{topic}': {str(e)}")
        raise RuntimeError(f"Error during search: {str(e)}")

def summarize_with_gemini(topic: str, raw_search_results: str, api_key: str) -> str:
    """Uses Gemini API to synthesize results into a 3-bullet-point brief."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)

    prompt = f"""
You are an expert research analyst assistant.
Based strictly on the web search results provided below, create a concise research brief on the topic: "{topic}".

Guidelines:
1. Provide EXACTLY THREE concise bullet points.
2. Focus on the most important, factual, and recent information.
3. Keep the tone professional, direct, and informative.
4. Do not include introductory text or conclusions—only the 3 bullet points.

Search Results:
{raw_search_results}
"""
    # Candidate Gemini models in priority order
    candidate_models = ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"temperature": 0.3}
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            last_err = e
            logger.warning(f"Model {model_name} failed: {e}. Trying next candidate...")

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")

# ==============================================================================
# Streamlit UI
# ==============================================================================
st.title("🤖 Task-Automation Agent")
st.caption("Experiment 10 — MLOps Deployment of Task-Automation Agent")
st.write("Enter any topic below to run the automated Web Search + Gemini Summarizer agent.")

topic = st.text_input("Enter Topic / Research Question:", placeholder="e.g. Recent breakthroughs in Quantum Computing")

if st.button("🚀 Generate Research Brief", type="primary"):
    if not topic.strip():
        st.error("Please enter a valid topic.")
    elif not API_KEY:
        st.error("Missing Gemini API Key! Provide it via environment variables or the sidebar.")
    else:
        logger.info(f"Received request for topic: '{topic}'")
        start_time = time.time()
        
        status_box = st.status("Executing Agent Workflow...", expanded=True)
        try:
            # Stage 1: Search
            status_box.write("🔍 Stage 1/2: Searching DuckDuckGo...")
            t_search_start = time.time()
            search_data = search_duckduckgo(topic)
            t_search = time.time() - t_search_start
            logger.info(f"DuckDuckGo search completed in {t_search:.2f}s for topic: '{topic}'")
            
            # Stage 2: Summarize
            status_box.write("✍️ Stage 2/2: Generating 3-point brief using Gemini API...")
            t_sum_start = time.time()
            summary = summarize_with_gemini(topic, search_data, API_KEY)
            t_sum = time.time() - t_sum_start
            logger.info(f"Gemini summarization completed in {t_sum:.2f}s for topic: '{topic}'")
            
            total_duration = time.time() - start_time
            logger.info(f"Successfully processed topic '{topic}' in {total_duration:.2f}s")
            status_box.update(label=f"Completed in {total_duration:.2f}s!", state="complete", expanded=False)
            
            st.subheader("📋 Three-Point Research Brief")
            st.markdown(summary)
            
            with st.expander("⏱️ Latency & Telemetry Details"):
                st.write(f"- **Search Latency**: {t_search:.2f} seconds")
                st.write(f"- **LLM Summarization Latency**: {t_sum:.2f} seconds")
                st.write(f"- **Total End-to-End Latency**: {total_duration:.2f} seconds")

        except Exception as err:
            total_duration = time.time() - start_time
            logger.error(f"Error processing topic '{topic}' after {total_duration:.2f}s: {str(err)}")
            status_box.update(label="Workflow Failed!", state="error", expanded=True)
            st.error(f"Agent failed to execute: {str(err)}")
