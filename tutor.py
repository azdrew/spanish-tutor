"""Spanish Tutor AI - Streamlit Web Application (Praktika-Inspired MVP).

Architecture & Specifications: PROJECT_CONTEXT.md & PROJECT_DESIGN.md
"""

import os
import re
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# UI & State
import streamlit as st

# Environment & Settings
from dotenv import load_dotenv
import yaml
from pydantic import BaseModel, Field

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
    model_name: str = "gemini-flash-latest"
    fallback_models: list[str] = [
        "gemini-flash-latest",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
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

# -----------------------------------------------------------------------------
# Streamlit UI Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Spanish Tutor AI",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern Praktika-style styling
st.markdown("""
<style>
    .tutor-banner {
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 100%);
        color: white;
        padding: 1.25rem 1.5rem;
    }
    .topic-chip {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.2);
        color: #F3E8FF;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = yaml_config.get("app_settings", {}).get("default_persona", "Gabby")

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
# Main Viewport & Tabs
# -----------------------------------------------------------------------------
current_persona = personas_data.get(st.session_state.selected_persona, {})
avatar_img = current_persona.get("avatar_path", "assets/gabby.jpg")
banner_img = current_persona.get("banner_path", "assets/gabby-banner.jpg")

# Navigation Tabs
tab_practice, tab_flashcards = st.tabs(["💬 Practice Session", "🎴 Flashcard Deck"])

# =============================================================================
# TAB 1: 💬 Practice Session
# =============================================================================
with tab_practice:
    # 1. Compact 16:9 Tutor Banner (Praktika Style)
    col_banner_img, col_banner_text = st.columns([1, 2])
    
    with col_banner_img:
        if Path(banner_img).exists():
            st.image(banner_img, use_container_width=True)
        elif Path(avatar_img).exists():
            st.image(avatar_img, use_container_width=True)

    with col_banner_text:
        st.markdown('<span class="topic-chip">A2 · Conversación Diaria & Viajes</span>', unsafe_allow_html=True)
        st.markdown(f"### {st.session_state.selected_persona} — Tu Tutora de Español")
        st.caption(f"_{current_persona.get('desc', 'Práctica conversacional personalizada.')}_")
        st.info("💡 **Tip:** Habla en español o escribe abajo. Si tienes dudas, puedes preguntar en inglés.")

    st.divider()

    # 2. First Message Greeting (if history empty)
    if not st.session_state.messages:
        initial_greeting = (
            f"¡Hola! Soy {st.session_state.selected_persona}. "
            "¿Cómo estás hoy? ¿De qué te gustaría hablar o practicar?"
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": initial_greeting
        })

    # 3. Chat History Feed
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = avatar_img if role == "assistant" else None
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

    # 4. Floating Suggestion / What to say chip
    with st.expander("💡 ¿No sabes qué decir? Sugerencias rápidas"):
        col_s1, col_s2, col_s3 = st.columns(3)
        if col_s1.button("🍽️ Quiero pedir comida"):
            st.session_state.quick_prompt = "Quiero practicar cómo pedir comida en un restaurante mexicano."
        if col_s2.button("✈️ Planear un viaje"):
            st.session_state.quick_prompt = "Estoy planeando un viaje a España o Colombia."
        if col_s3.button("🎬 Hablar de películas"):
            st.session_state.quick_prompt = "¿Cuáles son algunas buenas películas en español para aprender?"

    # 5. Push-to-Talk Audio & Text Input
    audio_val = st.audio_input("🎙️ Push-to-Talk (Habla con tu micrófono)")
    text_val = st.chat_input("Escribe un mensaje en español o haz una pregunta...")

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

    # 6. Process User Turn with Gemini
    if user_input:
        gemini_client = get_gemini_client()
        if not gemini_client:
            st.error("GEMINI_API_KEY no encontrada. Revisa los secrets.")
        else:
            # Build System Instruction
            system_instruction = f"""
{current_persona.get('system_instruction', '')}

FEEDBACK RIGOR: {feedback_style}
- Speak primarily in Latin American Spanish tailored for an advanced beginner (A2).
- Keep replies engaging, encouraging, and under 3-4 sentences.
- End your turn with a natural conversational question to continue the flow.
- If the user struggles with vocabulary or uses mixed English/Spanish ('Spanglish'), gently provide the right term and append a hidden tag: [SAVE: spanish_word | english_translation] to save it to their flashcard deck.
"""
            # Display User Message
            if input_is_audio:
                with st.chat_message("user"):
                    st.audio(audio_val)
                user_content_part = types.Part.from_bytes(
                    data=audio_val.getvalue(),
                    mime_type="audio/wav"
                )
            else:
                with st.chat_message("user"):
                    st.markdown(user_input)
                user_content_part = user_input
                st.session_state.messages.append({"role": "user", "content": user_input})

            # Generate Tutor Response with Real-Time Streaming
            with st.chat_message("assistant", avatar=avatar_img):
                raw_response = None
                last_err = None
                
                def create_stream(cand_model):
                    return gemini_client.models.generate_content_stream(
                        model=cand_model,
                        contents=user_content_part,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            max_output_tokens=300,
                            temperature=0.7
                        )
                    )

                for model_cand in config.fallback_models:
                    try:
                        def chunk_gen(model_name):
                            for chunk in create_stream(model_name):
                                if chunk.text:
                                    yield chunk.text

                        # Stream tokens to UI in real time
                        raw_response = st.write_stream(chunk_gen(model_cand))
                        break
                    except Exception as e:
                        last_err = e
                        logger.warning(f"Model {model_cand} stream error: {e}. Trying fallback...")
                
                if raw_response:
                    clean_text = parse_and_save_vocabulary(raw_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": clean_text
                    })
                else:
                    st.error(f"Error communicating with Gemini: {last_err}")

# =============================================================================
# TAB 2: 🎴 Flashcard Deck (MVP Preview)
# =============================================================================
with tab_flashcards:
    st.header("🎴 Mazo de Flashcards (Sistema Leitner SRS)")
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