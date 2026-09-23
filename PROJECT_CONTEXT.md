# SPANISH TUTOR APP: MASTER ARCHITECTURE & CONTEXT

## 1. Project Overview & Environment
* **Primary Language:** Python 3.x
* **UI Framework:** Streamlit (Single-file web application in `tutor.py`)[cite: 9]
* **Configuration:** `config.yaml` (Loads personas, UI settings, and preset starter decks)[cite: 9, 10]
* **Database / Cloud State:** Firebase Cloud Firestore (`google-cloud-firestore`)[cite: 9, 10]
* **Deployment & Execution:** Hosted on macOS (VS Code) -> GitHub Repository -> Streamlit Cloud / Phone Browser via Wi-Fi[cite: 9, 10]

## 2. API Configuration & Secrets Management
* **SDK Package:** `google-genai` (Connecting to `gemini-3.7-flash`)[cite: 9, 11]
* **Secret Keys:** `GEMINI_API_KEY`, `PEXELS_API_KEY`, and `firebase-key.json` loaded via `.env` and `st.secrets`[cite: 9, 11]. Strictly excluded via `.gitignore`[cite: 9, 10].

## 3. Database Schema (Firebase Firestore)
* **Base Reference:** `users/default_user/`[cite: 9]
* **Subcollection 1:** `words/` (Document ID = Spanish Word)
    * Fields: `english`, `box` (1-5), `last_reviewed`, `next_review`, `image_url`[cite: 9]
* **Subcollection 2:** `chat_sessions/` (Document ID = Timestamp ID)
    * Fields: `timestamp`, `title`, `messages` array[cite: 9]
* **Subcollection 3:** `user_settings/` (Document ID = `config`)
    * Fields: `tutor_persona`, `feedback_style`, `speech_speed`, `streak_days`

## 4. Tutor Personas & Operational Rules
* **Personas:** Gabriella "Gabby" (Default, warm, female voice)[cite: 9, 10] / Mateo (Secondary, male voice)[cite: 9, 10].
* **Language Pacing:** Speak primarily in Latin American Spanish; switch briefly to English for major grammar or structural corrections[cite: 9].
* **Feedback Rigor Settings:** Controlled via sidebar (Soft / Balanced / Strict)[cite: 10].
* **Automated Word Tracking:** Gemini appends hidden `[SAVE: spanish_word]` tags when the user struggles[cite: 9]. Regex strips tags for UI display and upserts words to Firestore `words/` subcollection[cite: 9].
* **Silence Helper:** "💡 What to say?" hint chip opens suggestions when tapped or after 5 seconds of silence[cite: 9].

## 5. Visual UI Structure & Layout (`tutor.py`)
* **Sidebar (`st.sidebar`):**
    * Tutor Persona Selector (Gabby/Mateo)[cite: 9, 10]
    * Speech Speed slider and Feedback Rigor controls[cite: 10]
    * User streak counter (🔥 X Days) and level display
    * Past chat history session selector[cite: 9]
    * Pre-made Starter Deck Importer (`config.yaml`)[cite: 9, 10]
* **Tab 1 ("💬 Practice"):**
    * Compact 16:9 horizontal tutor banner at the top (`st.columns` layout)[cite: 9, 10]
    * Chat history feed using 1:1 square face avatars with inline 🔊 TTS Audio & 🈳 Translation toggles[cite: 9, 10]
    * Push-to-talk microphone input (`st.audio_input`) accepting raw audio bytes[cite: 9]
* **Tab 2 ("🎴 Flashcards"):**
    * Leitner Box SRS filtering (renders words due for review today: `next_review <= today`)[cite: 9, 11]
    * Action Controls: [✅ Got It Right], [❌ Got It Wrong], [🤷 Pass / Don't Know]
    * Dynamic Image Fetching: Pexels API backfills missing `image_url` fields in Firestore[cite: 9, 11]
    * Spoken "Say the Word" Challenges: Audio interjections evaluated by Gemini[cite: 9, 11]