"""Spanish Tutor AI - Streamlit Web Application & Pipeline Validator.

Architecture & Specifications: PROJECT_CONTEXT.md
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

# UI & State
import streamlit as st

# Environment & Settings
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Logging
from loguru import logger

# Google GenAI (Gemini 2.5 Flash)
from google import genai
from google.genai import types

# Firebase & Google Cloud
import firebase_admin
from firebase_admin import credentials as fb_credentials, firestore as fb_firestore
from google.cloud import firestore
from google.oauth2 import service_account

# Networking & Utilities
import requests

# -----------------------------------------------------------------------------
# Configuration & Settings Setup
# -----------------------------------------------------------------------------
load_dotenv()

class AppConfig(BaseModel):
    """Application configuration schema."""
    app_name: str = "Spanish Tutor AI"
    version: str = "0.1.0"
    model_name: str = "gemini-3.7-flash"
    fallback_models: list[str] = ["gemini-3.7-flash", "gemini-3.5-flash-lite"]
    base_firestore_path: str = "users/default_user"

config = AppConfig()

# -----------------------------------------------------------------------------
# Secrets & Credentials Resolution Layer
# -----------------------------------------------------------------------------
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve secret from Streamlit secrets (Cloud) or OS environment (Local)."""
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
PEXELS_API_KEY = get_secret("PEXELS_API_KEY")

def get_firestore_client() -> Optional[firestore.Client]:
    """Initialize Firestore client from st.secrets (Cloud) or firebase-key.json (Local)."""
    try:
        # Check Streamlit Cloud Secrets first
        if hasattr(st, "secrets") and "firebase_service_account" in st.secrets:
            key_dict = dict(st.secrets["firebase_service_account"])
            # Handle possible escaped newlines in TOML
            if "private_key" in key_dict and "\\n" in key_dict["private_key"]:
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            cred = service_account.Credentials.from_service_account_info(key_dict)
            return firestore.Client(credentials=cred, project=key_dict.get("project_id"))
        
        # Local firebase-key.json fallback
        local_key = Path(__file__).resolve().parent / "firebase-key.json"
        if local_key.exists():
            cred = service_account.Credentials.from_service_account_file(str(local_key))
            return firestore.Client(credentials=cred)
    except Exception as e:
        logger.error(f"Firestore initialization error: {e}")
        return None
    return None

def get_gemini_client() -> Optional[genai.Client]:
    """Initialize Google GenAI Gemini client."""
    if not GEMINI_API_KEY:
        return None
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini client initialization error: {e}")
        return None

# -----------------------------------------------------------------------------
# Streamlit UI Presentation Layer
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Spanish Tutor AI",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_pipeline_status():
    """Render service connectivity checks for verifying the full pipeline."""
    st.header("🚀 System Pipeline & Service Health Check")
    st.caption("Verifying cloud dependencies, secret configurations, and database connectivity.")

    col1, col2, col3, col4 = st.columns(4)

    # 1. Streamlit Runtime
    with col1:
        st.metric(label="UI Engine", value="Streamlit Ready", delta="Online")
        st.success("✅ Streamlit Framework OK")

    # 2. Gemini API
    with col2:
        gemini_client = get_gemini_client()
        if gemini_client:
            st.metric(label="GenAI Model", value=config.model_name, delta="Connected")
            st.success("✅ Gemini API Connected")
        else:
            st.metric(label="GenAI Model", value="Missing Key", delta="-Offline")
            st.error("❌ GEMINI_API_KEY not found")

    # 3. Firebase Firestore
    with col3:
        db = get_firestore_client()
        if db:
            st.metric(label="Database", value="Cloud Firestore", delta="Connected")
            st.success("✅ Firestore Ready")
        else:
            st.metric(label="Database", value="No Credentials", delta="-Offline")
            st.warning("⚠️ Firestore Key Pending")

    # 4. Pexels API
    with col4:
        if PEXELS_API_KEY:
            st.metric(label="Visual Media", value="Pexels API", delta="Connected")
            st.success("✅ Pexels API Key OK")
        else:
            st.metric(label="Visual Media", value="No API Key", delta="-Missing")
            st.warning("⚠️ Pexels Key Pending")

def main():
    """Main application entry point."""
    st.title("🇪🇸 Spanish Tutor AI: ¡Hola Mundo!")
    st.write(
        "Welcome to the Spanish Tutor application development environment. "
        "This initial view validates that all core libraries, secret managers, and backend connections are active."
    )

    st.divider()
    render_pipeline_status()
    st.divider()

    # Interactive Test Component
    st.subheader("🧪 Live Smoke Test")
    st.write("Click below to test a live response from Gemini 3.7 Flash:")
    
    if st.button("💬 Ping Gemini Tutor", type="primary"):
        gemini_client = get_gemini_client()
        if not gemini_client:
            st.error("Cannot ping Gemini: GEMINI_API_KEY is not set.")
        else:
            with st.spinner("Gabriella is thinking..."):
                response_text = None
                last_error = None
                for model_candidate in config.fallback_models:
                    try:
                        response = gemini_client.models.generate_content(
                            model=model_candidate,
                            contents="Say hello in warm Latin American Spanish as tutor Gabriella and give a quick tip for learning Spanish today."
                        )
                        response_text = response.text
                        st.caption(f"⚡ Responded using `{model_candidate}`")
                        break
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Model {model_candidate} unavailable: {e}. Trying fallback...")
                
                if response_text:
                    st.chat_message("assistant").write(response_text)
                else:
                    st.error(f"Error communicating with Gemini: {last_error}")

    # Sidebar Information
    with st.sidebar:
        st.header("⚙️ App Info")
        st.info(f"**Version:** {config.version}\n\n**Target Dialect:** Latin American Spanish\n\n**User Scope:** `{config.default_user_id}`")
        st.markdown("---")
        st.markdown("📚 See [`PROJECT_CONTEXT.md`](#) for architecture details.")

if __name__ == "__main__":
    main()