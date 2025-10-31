"""
Configuration module - handles API keys for local and Streamlit Cloud deployment
"""

import os

def get_openai_api_key():
    """
    Get OpenAI API key from Streamlit secrets (cloud) or .env (local).

    This works in both environments:
    - Streamlit Cloud: Uses st.secrets
    - Local development: Uses .env file
    """
    # Try Streamlit secrets first (for deployment)
    try:
        import streamlit as st
        return st.secrets["OPENAI_API_KEY"]
    except:
        # Fallback to .env (for local development)
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")
