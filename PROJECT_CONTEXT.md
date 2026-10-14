# SPANISH TUTOR APP: MASTER ARCHITECTURE & CONTEXT

## 1. Project Overview & Environment

* **Primary Language:** Python 3.x
* **UI Framework:** Streamlit (Single-file web application in `tutor.py`)[cite: 2]
* **Configuration:** `config.yaml` (Loads personas, UI settings, and preset starter decks)[cite: 2]
* **Database / Cloud State:** Firebase Cloud Firestore (`google-cloud-firestore`)[cite: 2]
* **Deployment & Execution:** Hosted on macOS (VS Code) -> GitHub Repository -> Streamlit Community Cloud / Mobile Browser via local Wi-Fi[cite: 2]

## 2. API Configuration & Secrets Management

* **SDK Package:** `google-genai` (Connecting to `gemini-2.5-flash`)
* **Secret Keys:** `GEMINI_API_KEY`, `PEXELS_API_KEY`, and `firebase-key.json` loaded via `.env` and `st.secrets`[cite: 2]. Strictly excluded via `.gitignore`[cite: 2].

## 3. Database Schema (Firebase Firestore)

* **Base Reference:** `users/default_user/`[cite: 2]
* **Subcollection 1:** `words/` (Document ID = Spanish Word)
    * Fields: `english`, `box` (1-5), `last_reviewed`, `next_review`, `image_url`[cite: 2]
* **Subcollection 2:** `chat_sessions/` (Document ID = Timestamp ID)
    * Fields: `timestamp`, `title`, `messages` array[cite: 2]
* **Subcollection 3:** `user_settings/` (Document ID = `config`)[cite: 2]
    * Fields: `tutor_persona`, `feedback_style`, `speech_speed`, `streak_days`[cite: 2]

## 4. Tutor Personas & Operational Rules

* **Personas:** Gabriella "Gabby" (Default, warm, female voice) / Mateo (Secondary, male voice)[cite: 2].
* **Language Pacing:** Speak primarily in Latin American Spanish; switch briefly to English for major grammar or structural corrections[cite: 2].
* **Feedback Rigor Settings:** Controlled via sidebar (Soft / Balanced / Strict)[cite: 2].
* **Automated Word Tracking:** Gemini appends hidden `[SAVE: spanish_word]` tags when the user struggles[cite: 2]. Regex strips tags for UI display and upserts words to Firestore `words/` subcollection[cite: 2].
* **Silence Helper:** "💡 What to say?" hint chip opens suggestions when tapped or after 5 seconds of silence[cite: 2].

## 5. Visual UI Structure & Layout (`tutor.py`)

### Sidebar (`st.sidebar`)

* Tutor Persona Selector (`assets/gabby.png`, `assets/mateo.png`)[cite: 2]
* Speech Speed slider and Feedback Rigor controls[cite: 2]
* User streak counter (🔥 X Days) and level display[cite: 2]
* Past chat history session selector[cite: 2]
* Pre-made Starter Deck Importer (`config.yaml`)[cite: 2]

### Tab 1 ("💬 Practice")

* **Header Auto-Collapse:**
    * Initial state (<2 user turns): Displays 16:9 hero banner and tutor title card[cite: 2].
    * Active state (>=2 user turns): Unmounts large hero image and replaces it with a slim, single-row status bar (avatar thumbnail + level) to maximize vertical space.
* **Text-Message Conversational Feed:**
    * Chat history renders as alternating left/right speech bubbles (`st.chat_message`) using 1:1 avatars for Gabby/Mateo and the user[cite: 2].
    * Audio display widgets are replaced with the user's transcribed spoken text for readable, message-style chat logs.
    * Assistant bubbles feature inline 🔊 TTS Audio replay and 🈳 Translation toggles[cite: 2].
* **Bottom Action Bar (Praktika Voice-First Pattern):**
    * Default Mode: Push-to-talk microphone (`st.audio_input`)[cite: 2] spans the primary bottom bar with a small `✏️` pencil icon button. Prevents virtual keyboards from opening on mobile.
    * Text Mode: Tapping `✏️` reveals `st.chat_input` and a `🎙️` button to toggle back to voice-only input.

### Tab 2 ("🎴 Flashcards")

* Leitner Box SRS filtering (renders words due for review today: `next_review <= today`)[cite: 2].
* Action Controls: `[✅ Got It Right]`, `[❌ Got It Wrong]`, `[🤷 Pass / Don't Know]`[cite: 2].
* Dynamic Image Fetching: Pexels API backfills missing `image_url` fields in Firestore[cite: 2].
* Spoken "Say the Word" Challenges: Audio interjections evaluated by Gemini[cite: 2].