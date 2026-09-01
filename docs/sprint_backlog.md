# SPANISH TUTOR: SPRINT BACKLOG & ROADMAP

This backlog translates the master architecture from `PROJECT_CONTEXT.md` into actionable sprint deliverables.

---

## 🏃 Sprint 0: Foundation & Pipeline Validation
- [x] **Task 0.1: Initial `tutor.py` Setup & Pipeline Validation ("Hello World")**
  - Remove legacy CLI prototype code from `tutor.py`.
  - Add all required imports from `requirements.txt` (`streamlit`, `google-genai`, `google-cloud-firestore`, `firebase-admin`, `loguru`, `pydantic`, `pydantic-settings`, `pyyaml`, `requests`, `python-dotenv`).
  - Configure resilient secrets resolution (`st.secrets` with `.env` / `firebase-key.json` fallback).
  - Add initial Streamlit "Hello World" UI with interactive service health check indicators (Streamlit, Gemini API, Firestore, Pexels) to validate the end-to-end deployment pipeline.

---

## 🏃 Sprint 1: Cloud Architecture & State Management
- [ ] **Task 1.1: Firebase Firestore Connection Layer**
  - Implement dynamic credential resolver (`st.secrets` for Streamlit Cloud + local `firebase-key.json` fallback).
  - Initialize Firestore client and create helper methods for user document reference (`users/default_user/`).
- [ ] **Task 1.2: Multi-Environment Secrets Configuration**
  - Verify `.streamlit/secrets.toml` and `.env` loading for `GEMINI_API_KEY`, `PEXELS_API_KEY`, and service account.
- [ ] **Task 1.3: Document Schema Specs**
  - Detail schema models in `docs/firebase_schema.md`.

---

## 🏃 Sprint 2: Spaced Repetition (SRS) Flashcard Engine
- [ ] **Task 2.1: Leitner Box 1–5 Data Model & Scheduling**
  - Query words due for review today (`next_review <= today`).
  - Implement promotion (Box $N \to \min(N+1, 5)$) on success, and demotion (reset to Box 1) on incorrect.
- [ ] **Task 2.2: Pexels API Thumbnail Visual Integrations**
  - Fetch relevant visual context for vocabulary words missing `image_url` and persist back to Firestore.
- [ ] **Task 2.3: Pre-Made Topic Decks Importer**
  - Starter topic merging (Numbers, Months, Common Verbs, Body Parts) into Firestore `words/` subcollection.
- [ ] **Task 2.4: Spoken "Say the Word" Audio Challenges**
  - Interleaved spoken prompts requiring the user to translate aloud, evaluated via Gemini API.

---

## 🏃 Sprint 3: Conversational AI Tutor & Voice Interaction
- [ ] **Task 3.1: Persona & Prompt Engineering**
  - Implement Gabriella "Gabby" (warm, primary) and Mateo (secondary) personas.
  - Enforce Latin American dialect, $r$ vs. $rr$ pronunciation corrections, and *por* vs. *para* preposition checks.
- [ ] **Task 3.2: Push-to-Talk Voice Interface**
  - Integrate `st.audio_input` with raw byte streaming to `gemini-3.7-flash`.
- [ ] **Task 3.3: Spoken Tutor Audio (TTS)**
  - Generate and autoplay spoken audio responses for tutor dialogue.
- [ ] **Task 3.4: Automated Vocabulary Capture**
  - Parse `[SAVE: spanish_word]` tags from model output with regex, strip tags for UI display, and upsert cards to Firestore.
- [ ] **Task 3.5: 5-Second Silence Helper**
  - Display 3 quick response suggestions if user hesitation is detected.

---

## 🏃 Sprint 4: Chat History & Cross-Device Polish
- [ ] **Task 4.1: Chat Session Persistence**
  - Save and load historical chat threads in Firestore subcollection `users/default_user/chat_sessions/`.
  - Provide a collapsible sidebar history viewer.
- [ ] **Task 4.2: Mobile Responsive Layout**
  - Optimize UI for Samsung Galaxy browser & local Wi-Fi pairing.

