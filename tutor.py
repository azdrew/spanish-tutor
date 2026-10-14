"""Spanish Tutor AI - Streamlit Web Application (Praktika-Inspired MVP).

Architecture & Specifications: PROJECT_CONTEXT.md & PROJECT_DESIGN.md
"""

import os
import re
import json
import base64
import urllib.request
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# UI & State
import streamlit as st
import streamlit.components.v1 as components

# Environment & Settings
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel

# Logging
from loguru import logger

# Google GenAI (Gemini 3.7 Flash)
from google import genai
from google.genai import types

# Firebase & Google Cloud
from google.cloud import firestore
from google.oauth2 import service_account

# -----------------------------------------------------------------------------
# Configuration & Settings Setup
# -----------------------------------------------------------------------------
load_dotenv()

CONFIG_FILE = Path(__file__).resolve().parent / "config.yaml"

def load_app_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

yaml_config = load_app_config()

class AppConfig(BaseModel):
    """Application configuration schema."""
    app_name: str = "Spanish Tutor AI"
    version: str = "0.2.0"
    model_name: str = "gemini-2.5-flash"
    fallback_models: list[str] = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-3.7-flash",
        "gemini-flash-lite-latest"
    ]
    default_user_id: str = "default_user"
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

@st.cache_resource
def get_firestore_client() -> Optional[firestore.Client]:
    """Initialize cached Firestore client from st.secrets (Cloud) or firebase-key.json (Local)."""
    try:
        # Check Streamlit Cloud Secrets first
        if hasattr(st, "secrets") and "firebase_service_account" in st.secrets:
            key_dict = dict(st.secrets["firebase_service_account"])
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

@st.cache_resource
def get_gemini_client() -> Optional[genai.Client]:
    """Initialize cached Google GenAI Gemini client."""
    if not GEMINI_API_KEY:
        return None
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini client initialization error: {e}")
        return None

# -----------------------------------------------------------------------------
# Firestore Data Helpers
# -----------------------------------------------------------------------------
def save_word_to_firestore(spanish: str, english: str = "") -> bool:
    """Save or update a vocabulary card in Firestore."""
    db = get_firestore_client()
    if not db:
        return False
    try:
        doc_id = spanish.strip().lower()
        word_ref = db.collection("users").document(config.default_user_id).collection("words").document(doc_id)
        
        doc = word_ref.get()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        if doc.exists:
            # Update last reviewed
            word_ref.update({"last_reviewed": now_iso})
        else:
            # Create new card in Box 1
            word_ref.set({
                "spanish": spanish.strip(),
                "english": english.strip(),
                "box": 1,
                "last_reviewed": now_iso,
                "next_review": now_iso,
                "image_url": ""
            })
        return True
    except Exception as e:
        logger.error(f"Error saving word '{spanish}' to Firestore: {e}")
        return False

def parse_and_save_vocabulary(text: str) -> str:
    """Parse hidden [SAVE: spanish_word | english] tags, persist to Firestore, and return clean text."""
    pattern = r"\[SAVE:\s*([^\]|]+)(?:\|([^\]]+))?\]"
    matches = re.findall(pattern, text)
    for spanish, english in matches:
        save_word_to_firestore(spanish.strip(), english.strip() if english else "")
    
    # Strip tags from display text
    cleaned_text = re.sub(pattern, "", text).strip()
    return cleaned_text

def extract_turn_json(raw_text: str) -> dict:
    """Extract structured JSON containing transcription and reply from Gemini output."""
    clean = raw_text.strip()
    # Strip markdown code blocks ```json ... ``` if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL)
    if match:
        clean = match.group(1)
    else:
        # Search for first JSON object enclosed in braces
        brace_match = re.search(r"(\{.*\})", clean, re.DOTALL)
        if brace_match:
            clean = brace_match.group(1)
    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return data
    except Exception as e:
        logger.warning(f"Failed to parse JSON from Gemini response: {e}. Raw: {raw_text[:200]}")
    return {"transcription": "", "reply": raw_text}

def synthesize_speech(text: str, persona_name: str = "Gabby", speed_str: str = "1.0x") -> Optional[bytes]:
    """Generate spoken audio for tutor response using Gemini 3.8 Flash Lite TTS API."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY missing for TTS generation.")
        return None

    # Strip bracketed tags, markdown symbols, and excess whitespace
    clean = re.sub(r"\[.*?\]", "", text)
    clean = re.sub(r"[*_#`~]", "", clean).strip()
    if not clean:
        return None

    # Select voice based on persona (Gabby -> female 'Kore', Mateo -> male 'Puck')
    voice_name = "Kore" if persona_name.lower().startswith("gabb") else "Puck"

    # Adapt pacing description based on selected speech speed
    if "0.8" in speed_str:
        style_desc = "clear and deliberate Latin American Spanish tutor speaking slowly and clearly"
    elif "1.2" in speed_str:
        style_desc = "fluent and lively Latin American Spanish tutor speaking at an energetic pace"
    else:
        style_desc = "warm, friendly, and natural Latin American Spanish tutor speaking conversationally"

    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={GEMINI_API_KEY}"
    payload = {
        "model": "gemini-3.8-flash-lite-tts",
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": clean,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": style_desc
                }]
            }]
        }],
        "response_format": {
            "type": "audio",
            "mime_type": "audio/wav"
        },
        "generation_config": {
            "speech_config": [
                {"voice": voice_name}
            ]
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                for step in data.get("steps", []):
                    for item in step.get("content", []):
                        if item.get("type") == "audio" and "data" in item:
                            return base64.b64decode(item["data"])
    except Exception as e:
        logger.error(f"Error synthesizing speech audio: {e}")
    return None

def translate_to_english(text: str) -> Optional[str]:
    """Translate Spanish tutor response into natural English."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY missing for translation.")
        return None

    clean = re.sub(r"\[.*?\]", "", text)
    clean = re.sub(r"[*_#`~]", "", clean).strip()
    if not clean:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Translate the following Spanish conversational text into clear, natural English for a language student. Return ONLY the English translation without quotes or conversational commentary:\n\n{clean}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 200
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip().strip('"').strip("'")
    except Exception as e:
        logger.error(f"Error translating Spanish to English: {e}")
    return None

# -----------------------------------------------------------------------------
# Streamlit UI Setup
# -----------------------------------------------------------------------------
# Streamlit UI Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Spanish Tutor AI",
    page_icon="🇪🇸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern Praktika-style mobile layout
st.markdown("""
<style>
    /* 1. Header & Viewport Reset - Retain hamburger menu & sidebar controls */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem !important;
        z-index: 50 !important;
    }
    .main .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 7.5rem !important;
        max-width: 42rem !important;
        margin: 0 auto !important;
        scroll-behavior: smooth !important;
    }
    /* Hide component iframe space */
    iframe[title="streamlit.components.v1.html"] {
        display: none !important;
        height: 0 !important;
    }
    .element-container:has(> iframe[title="streamlit.components.v1.html"]) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 2. Banner & Images */
    [data-testid="stImage"] img {
        border-radius: 20px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        object-fit: cover !important;
    }

    /* 3. Global Dividers - NO horizontal lines */
    hr, [data-testid="stDivider"], .stDivider {
        display: none !important;
    }

    /* 4. Chat Messages Styling (Praktika mobile bubbles) */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 4px 0 !important;
        gap: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    /* Hide all avatar containers */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarCustom"],
    [data-testid="stChatMessage"] > div:first-child:has(img),
    [data-testid="stChatMessage"] > div:first-child:has(svg) {
        display: none !important;
    }

    /* User Message - RIGHT Aligned, Vibrant Purple (#7026ED) */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        display: flex !important;
        flex-direction: row-reverse !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #7026ED !important;
        color: #FFFFFF !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 10px 18px !important;
        max-width: 80% !important;
        margin-left: auto !important;
        box-shadow: 0 2px 8px rgba(112, 38, 237, 0.25) !important;
    }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
        color: #FFFFFF !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        line-height: 1.4 !important;
        margin: 0 !important;
    }

    /* Tutor Message - LEFT Aligned, Light Gray / Off-white (#F3F4F6) */
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) {
        display: flex !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) [data-testid="stChatMessageContent"] {
        background-color: #F3F4F6 !important;
        color: #1F2937 !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 12px 18px !important;
        max-width: 84% !important;
        margin-right: auto !important;
    }
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) [data-testid="stChatMessageContent"] p {
        color: #1F2937 !important;
        font-size: 1rem !important;
        line-height: 1.45 !important;
        margin-bottom: 0.25rem !important;
    }

    /* Highlighted vocabulary tags in tutor messages */
    .vocab-hl {
        background-color: #EDE9FE !important;
        color: #7026ED !important;
        border-radius: 6px !important;
        padding: 1px 6px !important;
        font-weight: 600 !important;
    }

    /* Tutor action buttons (Replay & Translate) */
    div[data-testid="stChatMessage"] div[class*="st-key-audio_btn_"] button,
    div[data-testid="stChatMessage"] div[class*="st-key-trans_btn_"] button {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #6B7280 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        width: 30px !important;
        height: 30px !important;
        min-width: 30px !important;
        min-height: 30px !important;
        max-width: 30px !important;
        max-height: 30px !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 6px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }
    div[data-testid="stChatMessage"] div[class*="st-key-audio_btn_"] button:hover,
    div[data-testid="stChatMessage"] div[class*="st-key-trans_btn_"] button:hover {
        background-color: rgba(112, 38, 237, 0.1) !important;
        color: #7026ED !important;
    }
    /* Google Translate icon in purple */
    div[data-testid="stChatMessage"] div[class*="st-key-trans_btn_"] button {
        color: #7026ED !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        letter-spacing: -0.5px !important;
    }

    /* Typing indicator bubble */
    .typing-bubble {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 16px;
        background-color: #F3F4F6;
        border-radius: 18px;
        margin: 4px 0;
        width: fit-content;
    }
    .typing-dot {
        width: 7px;
        height: 7px;
        background-color: #9CA3AF;
        border-radius: 50%;
        display: inline-block;
        animation: typing-pulse 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }
    @keyframes typing-pulse {
        0%, 80%, 100% {
            transform: scale(0.4);
            opacity: 0.3;
        }
        40% {
            transform: scale(1.0);
            opacity: 1.0;
        }
    }

    /* 5. Bottom Action Bar - At the very bottom of the screen, floating and transparent */
    [data-testid="stBottom"],
    .stBottom {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        border-top: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        padding: 0 0 0.5rem 0 !important;
        margin: 0 !important;
        bottom: 0 !important;
        z-index: 100 !important;
    }
    [data-testid="stBottom"] > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 1rem !important;
        margin: 0 auto !important;
        max-width: 44rem !important;
    }
    [data-testid="stBottom"] > div > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Completely strip all boxes, borders, outlines, and backgrounds from stAudioInput */
    div[data-testid="stAudioInput"],
    div[data-testid="stAudioInput"] *,
    .stAudioInput,
    .stAudioInput * {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    div[data-testid="stAudioInput"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important;
        margin: 0 auto !important;
        width: 100% !important;
    }
    div[data-testid="stAudioInput"] > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 0 !important;
        margin: 0 auto !important;
        gap: 0 !important;
    }
    [data-testid="stAudioInput"] label,
    .stAudioInput label {
        display: none !important;
    }
    /* Hide waveform, timecode, and helper instructions completely */
    [data-testid="stAudioInputWaveSurfer"],
    [data-testid="stAudioInputWaveformTimeCode"],
    [data-testid="stAudioInput"] [data-testid="stAudioInputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Large Purple Push-to-Talk button - Centered */
    button[data-testid="stAudioInputActionButton"] {
        width: 72px !important;
        height: 72px !important;
        min-width: 72px !important;
        min-height: 72px !important;
        border-radius: 50% !important;
        background-color: #7026ED !important;
        background: #7026ED !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(112, 38, 237, 0.45) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: transform 0.15s ease, background-color 0.2s ease !important;
        margin: 0 auto !important;
    }
    button[data-testid="stAudioInputActionButton"]:hover {
        background-color: #5B1BD0 !important;
        transform: scale(1.05) !important;
    }
    button[data-testid="stAudioInputActionButton"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        width: 32px !important;
        height: 32px !important;
    }

    /* Left (+) button - Aligned Left */
    .st-key-btn_plus,
    .st-key-toggle_text_mode {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
    }
    .st-key-btn_plus button,
    .st-key-toggle_text_mode button {
        border-radius: 50% !important;
        width: 52px !important;
        height: 52px !important;
        min-width: 52px !important;
        min-height: 52px !important;
        padding: 0 !important;
        margin: 0 !important;
        margin-left: 0 !important;
        margin-right: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.5rem !important;
        font-weight: 400 !important;
        border: 1px solid #E5E7EB !important;
        background-color: #F3F4F6 !important;
        color: #1F2937 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
    }
    .st-key-btn_plus button:hover,
    .st-key-toggle_text_mode button:hover {
        background-color: #E5E7EB !important;
    }

    /* Return to voice button in text mode */
    .st-key-toggle_voice_mode button {
        border-radius: 50% !important;
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        min-height: 44px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.25rem !important;
        border: none !important;
        background-color: #7026ED !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(112, 38, 237, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# Client-Side Virtual Keyboard & Auto-Scroll Helper for Mobile
components.html("""
<script>
(function() {
    const parentDoc = window.parent.document;

    function scrollToBottom() {
        const mainContainer = parentDoc.querySelector('.main') || parentDoc.documentElement;
        const chatInput = parentDoc.querySelector('[data-testid="stChatInput"]');
        if (chatInput) {
            chatInput.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
        if (mainContainer) {
            mainContainer.scrollTo({
                top: mainContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
    }

    // 1. Detect mobile visual viewport resizing (on-screen keyboard popping up)
    if (window.parent.visualViewport) {
        window.parent.visualViewport.addEventListener('resize', () => {
            const vv = window.parent.visualViewport;
            if (vv.height < window.parent.innerHeight * 0.82) {
                // Keyboard has opened
                setTimeout(scrollToBottom, 150);
            }
        });
    }

    // 2. Attach focus listener to the chat textarea
    function setupInputListener() {
        const textarea = parentDoc.querySelector('[data-testid="stChatInput"] textarea');
        if (textarea && !textarea.dataset.scrollBound) {
            textarea.dataset.scrollBound = "true";
            textarea.addEventListener('focus', () => {
                setTimeout(scrollToBottom, 250);
                setTimeout(scrollToBottom, 500);
            });
        }
    }
    setInterval(setupInputListener, 800);
})();
</script>
""", height=0, width=0)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = yaml_config.get("app_settings", {}).get("default_persona", "Gabby")

if "show_text_input" not in st.session_state:
    st.session_state.show_text_input = False

# -----------------------------------------------------------------------------
# Sidebar: Settings & Controls
# -----------------------------------------------------------------------------
personas_data = yaml_config.get("personas", {
    "Gabby": {
        "gender": "female",
        "avatar_path": "assets/gabby.jpg",
        "banner_path": "assets/gabby-banner.jpg",
        "desc": "Warm & encouraging Latin American Spanish practice.",
        "system_instruction": "You are Gabriella 'Gabby', a warm, supportive Latin American Spanish tutor."
    }
})

with st.sidebar:
    st.title("🇪🇸 Configuración")
    
    # Persona Selector
    persona_names = list(personas_data.keys())
    selected_persona_name = st.selectbox(
        "Tutor Persona",
        options=persona_names,
        index=persona_names.index(st.session_state.selected_persona) if st.session_state.selected_persona in persona_names else 0
    )
    st.session_state.selected_persona = selected_persona_name
    current_persona = personas_data.get(selected_persona_name, {})

    # Avatar Preview
    avatar_path = current_persona.get("avatar_path", "assets/gabby.jpg")
    if Path(avatar_path).exists():
        st.image(avatar_path, width=120)
    st.caption(current_persona.get("desc", ""))

    st.divider()

    # Feedback Rigor
    feedback_style = st.radio(
        "Tutor Feedback Rigor",
        options=["Balanced", "Soft", "Strict"],
        index=0,
        help="Balanced: Corrects major errors inline. Soft: Encouragement first. Strict: Corrects all grammar and pronunciation."
    )

    # Speech Speed
    speech_speed = st.select_slider(
        "Speech Speed",
        options=["0.8x", "1.0x", "1.2x"],
        value="1.0x"
    )

    autoplay_voice = st.checkbox(
        "🔊 Auto-reproducir voz del tutor",
        value=False,
        help="Reproduce el audio automáticamente cuando Gabby responde."
    )

    st.divider()
    st.subheader("🔥 Streak")
    st.metric(label="Active Streak", value="1 Day", delta="Keep it up!")

    # System Status Expander (Accessible for diagnostics)
    with st.expander("🛠️ System Health Check"):
        st.write(f"**GenAI:** {config.model_name}")
        st.write(f"**User Scope:** `{config.default_user_id}`")
        db = get_firestore_client()
        st.write(f"**Firestore:** {'🟢 Connected' if db else '🔴 Disconnected'}")
        st.write(f"**Pexels API:** {'🟢 Configured' if PEXELS_API_KEY else '🟡 Missing Key'}")

# -----------------------------------------------------------------------------
# Main Viewport & Navigation
# -----------------------------------------------------------------------------
current_persona = personas_data.get(st.session_state.selected_persona, {})
avatar_img = current_persona.get("avatar_path", "assets/gabby.jpg")
banner_img = current_persona.get("banner_path", "assets/gabby-banner.jpg")

if "show_flashcards" not in st.session_state:
    st.session_state.show_flashcards = False

# =============================================================================
# VIEW 1: 🎴 Flashcard Deck (When toggled via book icon)
# =============================================================================
if st.session_state.show_flashcards:
    col_back, col_title = st.columns([1, 5], vertical_alignment="center")
    with col_back:
        if st.button("← Volver", key="btn_back_practice"):
            st.session_state.show_flashcards = False
            st.rerun()
    with col_title:
        st.subheader("🎴 Mazo de Flashcards (Sistema Leitner SRS)")
    st.caption("Repasa tus palabras guardadas automáticamente durante las conversaciones.")

    preset_decks = yaml_config.get("preset_decks", {})
    col_fc1, col_fc2 = st.columns([2, 1])
    with col_fc1:
        st.subheader("📚 Mazos Temáticos Disponibles")
        for deck_name, cards in preset_decks.items():
            with st.expander(f"📦 {deck_name} ({len(cards)} palabras)"):
                for sp, data in cards.items():
                    st.write(f"🇪🇸 **{sp}** ➔ 🇬🇧 _{data.get('english', '')}_ (Box {data.get('box', 1)})")
    with col_fc2:
        st.subheader("📊 Progreso Leitner")
        st.metric(label="Palabras Guardadas", value="0", delta="En sincronización")
        st.info("💡 En la siguiente iteración de Checkpoint 2, podrás repasar tarjetas interactivas con imágenes de Pexels y audio de voz.")

# =============================================================================
# VIEW 2: 💬 Practice Session (Default Voice-First Experience)
# =============================================================================
else:
    # 1. Hero Banner (Right at the top) / Auto-Collapse Status Bar
    user_turn_count = sum(1 for m in st.session_state.messages if m.get("role") == "user")

    if user_turn_count < 2:
        # Full-width 16:9 banner right at the very top
        if Path(banner_img).exists():
            st.image(banner_img, width='stretch')
        elif Path(avatar_img).exists():
            st.image(avatar_img, width='stretch')
    else:
        # Slim single-row status bar
        col_avatar_thumb, col_status_text = st.columns([1, 11], vertical_alignment="center")
        with col_avatar_thumb:
            if Path(avatar_img).exists():
                st.image(avatar_img, width=42)
            elif Path(banner_img).exists():
                st.image(banner_img, width=42)
        with col_status_text:
            st.markdown(
                f"""<div style="display: flex; align-items: center; gap: 8px;">
                    <strong style="font-size: 1.05rem; color: #1F2937;">{st.session_state.selected_persona}</strong>
                    <span style="font-size: 0.75rem; background: #EDE9FE; color: #7026ED; padding: 2px 8px; border-radius: 12px; font-weight: 600;">A2 · Conversación</span>
                    <span style="font-size: 0.8rem; color: #10B981; font-weight: 500;">● En línea</span>
                </div>""",
                unsafe_allow_html=True
            )

    # 3. First Message Greeting (if history empty)
    if not st.session_state.messages:
        initial_greeting = (
            f"¡Hola! Soy {st.session_state.selected_persona}. "
            "¿Cómo estás hoy? ¿De qué te gustaría hablar o practicar?"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": initial_greeting,
            "translation": f"Hello! I am {st.session_state.selected_persona}. How are you today? What would you like to talk about or practice?",
            "audio": None,
            "show_audio_player": False
        })

    # 4. Dedicated Chat Container
    chat_container = st.container()

    with chat_container:
        for idx, msg in enumerate(st.session_state.messages):
            role = msg["role"]
            with st.chat_message(role):
                st.markdown(msg["content"])

                if role == "assistant":
                    # Action buttons under tutor message: Speaker (🔊) next to Google Translate (文A)
                    col_replay, col_trans, _spacer = st.columns([0.08, 0.08, 0.84], vertical_alignment="center")

                    with col_replay:
                        if st.button("🔊", key=f"audio_btn_{idx}", help="Reproducir voz del tutor"):
                            if not msg.get("audio"):
                                with st.spinner("🎙️..."):
                                    msg["audio"] = synthesize_speech(
                                        msg["content"],
                                        persona_name=st.session_state.selected_persona,
                                        speed_str=speech_speed
                                    )
                            st.session_state[f"play_audio_{idx}"] = True
                            st.rerun()

                    is_translated = st.session_state.get(f"show_trans_{idx}", False)
                    with col_trans:
                        if st.button("文A", key=f"trans_btn_{idx}", help="Google Translate - Traducción al inglés"):
                            st.session_state[f"show_trans_{idx}"] = not is_translated
                            if not is_translated and not msg.get("translation"):
                                with st.spinner("🈳..."):
                                    msg["translation"] = translate_to_english(msg["content"])
                            st.rerun()

                    # Seamless invisible audio player for replay
                    if msg.get("audio") and st.session_state.get(f"play_audio_{idx}", False):
                        b64_audio = base64.b64encode(msg["audio"]).decode()
                        st.markdown(
                            f'<audio autoplay style="display:none;"><source src="data:audio/wav;base64,{b64_audio}" type="audio/wav"></audio>',
                            unsafe_allow_html=True
                        )
                        st.session_state[f"play_audio_{idx}"] = False

                    # Render English translation card if toggled on
                    if is_translated and msg.get("translation"):
                        st.markdown(
                            f"""<div style="background-color: #EDE9FE; border-left: 3px solid #7026ED; padding: 6px 12px; border-radius: 8px; margin-top: 6px; font-size: 0.92rem; color: #4C1D95;">
                            🇬🇧 <em>{msg['translation']}</em>
                            </div>""",
                            unsafe_allow_html=True
                        )

    # 5. Bottom Action Bar: Praktika Voice-First Pattern (No horizontal lines)
    audio_val = None
    text_val = None

    if hasattr(st, "bottom"):
        bottom_area = st.bottom
    else:
        bottom_area = st.container()

    with bottom_area:
        if not st.session_state.show_text_input:
            # Voice Mode: ONLY (+) button on far left and centered large push to talk button
            col_plus, col_mic, _spacer = st.columns([1, 1, 1], vertical_alignment="center")
            with col_plus:
                if st.button("＋", key="toggle_text_mode", help="Cambiar a escribir texto"):
                    st.session_state.show_text_input = True
                    st.rerun()
            with col_mic:
                audio_val = st.audio_input("Hablar", label_visibility="collapsed", key="push_to_talk")
        else:
            # Text Mode: chat input on left, microphone button on right
            col_chat, col_btn = st.columns([6, 1], vertical_alignment="center")
            with col_chat:
                text_val = st.chat_input("Escribe un mensaje en español...", key="chat_input_field")
            with col_btn:
                if st.button("🎙️", key="toggle_voice_mode", help="Volver a modo de voz"):
                    st.session_state.show_text_input = False
                    st.rerun()

    user_input = None
    input_is_audio = False

    # Check for quick prompt trigger
    if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
        user_input = st.session_state.quick_prompt
        st.session_state.quick_prompt = None
    elif text_val:
        user_input = text_val
    elif audio_val:
        user_input = audio_val
        input_is_audio = True

    # 6. Process User Turn with Gemini (Structured JSON with Transcription & Reply)
    if user_input:
        gemini_client = get_gemini_client()
        if not gemini_client:
            st.error("GEMINI_API_KEY no encontrada. Revisa los secrets.")
        else:
            # Build System Instruction with Structured JSON format specification
            system_instruction = f"""
{current_persona.get('system_instruction', '')}

FEEDBACK RIGOR: {feedback_style}
- Speak primarily in Latin American Spanish tailored for an advanced beginner (A2).
- Keep replies engaging, encouraging, and under 3-4 sentences.
- End your turn with a natural conversational question to continue the flow.
- If the user struggles with vocabulary or uses mixed English/Spanish ('Spanglish'), gently provide the right term and append a hidden tag: [SAVE: spanish_word | english_translation] inside your reply to save it to their flashcard deck.

CRITICAL STRUCTURED OUTPUT REQUIREMENT:
You must respond with a valid JSON object containing exactly two string fields:
{{
  "transcription": "Accurate verbatim transcription of what the user said (in Spanish or English). If the user provided text input, repeat the user text exactly.",
  "reply": "Your Spanish response to the user following persona and feedback rules, including any [SAVE: word | translation] tag."
}}
"""
            # Display User Message inside chat container
            with chat_container:
                if input_is_audio:
                    with st.chat_message("user"):
                        user_msg_placeholder = st.empty()
                        user_msg_placeholder.markdown("🎙️ _Transcribiendo audio..._")
                    latest_part = types.Part.from_bytes(
                        data=audio_val.getvalue(),
                        mime_type="audio/wav"
                    )
                else:
                    with st.chat_message("user"):
                        st.markdown(user_input)
                    latest_part = types.Part.from_text(text=user_input)

                # Generate Tutor Response with Animated 3-Dot Status Indicator
                with st.chat_message("assistant"):
                    typing_placeholder = st.empty()
                    typing_placeholder.markdown(
                        f'<div class="typing-bubble">'
                        f'<span class="typing-dot"></span>'
                        f'<span class="typing-dot"></span>'
                        f'<span class="typing-dot"></span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    raw_response_text = None
                    last_err = None

                    # Build multi-turn conversational history
                    contents = []
                    for hist_msg in st.session_state.messages[-6:]:
                        role_tag = "user" if hist_msg.get("role") == "user" else "model"
                        if hist_msg.get("content"):
                            contents.append(types.Content(
                                role=role_tag,
                                parts=[types.Part.from_text(text=hist_msg["content"])]
                            ))
                    # Append current user turn
                    contents.append(types.Content(
                        role="user",
                        parts=[latest_part]
                    ))

                    for model_cand in config.fallback_models:
                        try:
                            resp = gemini_client.models.generate_content(
                                model=model_cand,
                                contents=contents,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    response_mime_type="application/json",
                                    max_output_tokens=500,
                                    temperature=0.7
                                )
                            )
                            if resp.text:
                                raw_response_text = resp.text
                                break
                        except Exception as e:
                            last_err = e
                            logger.warning(f"Model {model_cand} generation error: {e}. Trying fallback...")

                    typing_placeholder.empty()

                    if raw_response_text:
                        turn_data = extract_turn_json(raw_response_text)

                        # Resolve user transcription and persist as text message
                        if input_is_audio:
                            user_transcription = turn_data.get("transcription", "").strip() or "🎙️ [Audio grabado]"
                            user_msg_placeholder.markdown(user_transcription)
                            st.session_state.messages.append({"role": "user", "content": user_transcription})
                        else:
                            st.session_state.messages.append({"role": "user", "content": user_input})

                        # Resolve assistant response
                        assistant_raw_reply = turn_data.get("reply", "").strip() or raw_response_text
                        clean_text = parse_and_save_vocabulary(assistant_raw_reply)
                        st.markdown(clean_text)

                        new_msg = {
                            "role": "assistant",
                            "content": clean_text,
                            "translation": None,
                            "audio": None,
                            "show_audio_player": False
                        }
                        if autoplay_voice:
                            with st.spinner("🎙️..."):
                                audio_bytes = synthesize_speech(
                                    clean_text,
                                    persona_name=st.session_state.selected_persona,
                                    speed_str=speech_speed
                                )
                                if audio_bytes:
                                    new_msg["audio"] = audio_bytes
                                    new_msg["show_audio_player"] = True
                                    new_idx = len(st.session_state.messages)
                                    st.session_state[f"play_audio_{new_idx}"] = True
                        st.session_state.messages.append(new_msg)
                        st.rerun()
                    else:
                        if input_is_audio:
                            user_msg_placeholder.markdown("⚠️ _No se pudo procesar el audio._")
                        st.error(f"Error communicating with Gemini: {last_err}")