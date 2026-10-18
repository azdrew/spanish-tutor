# SPANISH TUTOR APP: MASTER ARCHITECTURE & CONTEXT

## 1. Project Overview & Environment

* **Primary Language:** Python 3.x
* **UI Framework:** Streamlit (Single-file web application in `tutor.py`)[cite: 2]
* **Configuration:** `config.yaml` (Loads personas, UI settings, and preset starter decks)[cite: 2]
* **Database / Cloud State:** Firebase Cloud Firestore (`google-cloud-firestore`)[cite: 2]
* **Deployment & Execution:** Hosted on macOS (VS Code) -> GitHub Repository -> Streamlit Community Cloud / Mobile Browser via local Wi-Fi[cite: 2]

### 2. API Configuration & Secrets Management

* **SDK Package & LLM Models:** `google-genai` connecting to `gemini-flash-lite-latest` (primary), with resilient fallbacks to `gemini-3.5-flash-lite` and `gemini-3.8-flash`. Structured JSON output guarantees accurate audio transcription and clean conversational responses without 503/429 hang loops.
* **Speech Engine (TTS):** Microsoft Edge Neural TTS (`edge-tts`) as primary speech engine (`es-MX-DaliaNeural` for Gabby, `es-MX-JorgeNeural` for Mateo). Provides unlimited requests (zero daily quota caps), natural human-sounding Latin American Spanish prosody, and speed pacing support (`-15%` for 0.8x, `+0%` for 1.0x, `+15%` for 1.2x). Auto-falls back to Google Translate TTS (`translate_tts`, 0.3s latency) if network drops occur.
* **Secret Keys:** `GEMINI_API_KEY`, `PEXELS_API_KEY`, and `firebase-key.json` loaded via `.env` and `st.secrets`. Strictly excluded via `.gitignore`.

## 3. Database Schema (Firebase Firestore)

* **Base Reference:** `users/default_user/`
* **Subcollection 1:** `words/` (Document ID = Spanish Word)
    * Fields: `english`, `box` (1-5), `last_reviewed`, `next_review`, `image_url`
* **Subcollection 2:** `chat_sessions/` (Document ID = Timestamp ID)
    * Fields: `timestamp`, `title`, `messages` array
* **Subcollection 3:** `user_settings/` (Document ID = `config`)
    * Fields: `tutor_persona`, `feedback_style`, `speech_speed`, `streak_days`

## 4. Tutor Personas & Operational Rules

* **Personas:** Gabriella "Gabby" (Default, warm, female voice: `es-MX-DaliaNeural`) / Mateo (Secondary, patient male voice: `es-MX-JorgeNeural`).
* **Language Pacing:** Speak primarily in Latin American Spanish; switch briefly to English for major grammar or structural corrections.
* **Feedback Rigor Settings:** Controlled via sidebar (Soft / Balanced / Strict).
* **Automated Word Tracking:** Gemini appends hidden `[SAVE: spanish_word | english_translation]` tags when the user struggles. Regex strips tags for UI display, and an asynchronous daemon thread (`threading.Thread`) upserts words to Firestore `words/` in the background without blocking the UI or audio playback.
* **Silence Helper:** "💡 What to say?" hint chip opens suggestions when tapped or after 5 seconds of silence.

## 5. Visual UI Structure & Layout (`tutor.py`)

### Sidebar (`st.sidebar`)

* Tutor Persona Selector (`assets/gabby.png`, `assets/mateo.png`)
* Speech Speed slider (`0.8x`, `1.0x`, `1.2x`) and Feedback Rigor controls
* User streak counter (🔥 X Days) and level display
* Past chat history session selector
* Pre-made Starter Deck Importer (`config.yaml`)

### Tab 1 ("💬 Practice") — Praktika Voice-First Experience

* **Header Auto-Collapse:**
    * Initial state (<2 user turns): Displays full-width 16:9 hero banner and tutor title card.
    * Active state (>=2 user turns): Unmounts large hero image and replaces it with a slim, single-row status bar (avatar thumbnail + level badge) to maximize vertical chat space.
* **Text-Message Conversational Feed:**
    * Chat history renders as asymmetric speech bubbles (`st.chat_message`):
        * **Assistant (Gabby):** Soft gray card (`#F3F4F6`) with dark slate typography.
        * **User (Student):** Sleek violet pill (`#7C3AED`) with white typography, right-aligned.
    * Audio display widgets are replaced with the user's transcribed spoken text for readable, message-style chat logs, featuring an inline speaker icon inside the student bubble for optional audio replay.
    * Assistant bubbles feature inline 🔊 TTS Audio replay and 文A Google Translate toggles in a clean horizontal row.
    * **Centered Typing Indicator:** A 3-dot pulse animation (`•••`) horizontally and vertically centered directly within Gabby's chat bubble during response generation.
* **Praktika Bottom Action Bar:**
    * **Push-to-Talk Microphone Button:** Pinned to viewport bottom center (`bottom: 20px; left: 50%; transform: translateX(-50%)`). Stripped of all bounding boxes, borders, and labels to leave a focused, 76px circular mic button.
    * **Left Floating `+` Button:** Fixed at bottom left (`bottom: 28px`), allowing users to toggle a text input bar (`st.chat_input`) with automatic dismissal on submit.
    * **Viewport Clearance:** Bottom padding (`9.5rem`) on `stMainBlockContainer` preventing mobile keyboard clipping and ensuring chat always scrolls cleanly above floating controls.

### Tab 2 ("🎴 Flashcards") — Checkpoint 2 Roadmap

* Leitner Box SRS filtering (renders words due for review today: `next_review <= today`).
* Action Controls: `[✅ Got It Right]`, `[❌ Got It Wrong]`, `[🤷 Pass / Don't Know]`.
* Dynamic Image Fetching: Pexels API backfills missing `image_url` fields in Firestore.
* Spoken "Say the Word" Challenges: Audio interjections evaluated by Gemini.

```text
 ========================================================================
[ st.set_page_config(layout="centered") ]                               
========================================================================

+----------------------------------------------------------------------+
|                         DYNAMIC TOP BANNER                           |
|                                                                      |
|  STATE A: (user_turns < 2) -> Initial Onboarding                     |
|  +----------------------------------------------------------------+  |
|  | [ 🖼️ 16:9 Tutor Banner Image: assets/gabby_banner.jpeg ]         |  |
|  | **Gabby — Tu Tutora de Español**                               |  |
|  | Warm & encouraging Latin American Spanish practice.            |  |
|  +----------------------------------------------------------------+  |
|                                                                      |
|  STATE B: (user_turns >= 2) -> Auto-Collapsed Slim Status Bar        |
|  +----------------------------------------------------------------+  |
|  | [ 👤 42px Avatar ]  **Gabby** · *A2 Práctica Diaria*           |  |
|  +----------------------------------------------------------------+  |
+----------------------------------------------------------------------+
|--------------------------- st.divider() -----------------------------|
+----------------------------------------------------------------------+
|                CONVERSATIONAL CHAT FEED (st.chat_message)            |
|                                                                      |
|   +-------------------------------------------------------------+    |
|   | 👤 User Speech Bubble (Right-aligned violet #7C3AED)        |    |
|   | "Hola Gabby, ¿cómo estás hoy? Quiero practicar español."     |    |
|   | [ 🔊 Replay My Voice ]                                      |    |
|   +-------------------------------------------------------------+    |
|                                                                      |
|   +-------------------------------------------------------------+    |
|   | 👩‍🏫 Gabby Speech Bubble (Left-aligned soft gray #F3F4F6)      |    |
|   | "¡Hola! Estoy muy bien. ¿Qué hiciste esta mañana?"          |    |
|   | [ 🔊 Escuchar ]   [ 文A Traducir ]                           |    |
|   +-------------------------------------------------------------+    |
|                                                                      |
|   (While generating response: centered typing pulse [ • • • ])       |
|                                                                      |
+----------------------------------------------------------------------+
|                                                                      |
|               PRAKTIKA VOICE-FIRST FLOATING CONTROLS                 |
|                                                                      |
|  +-------------------+       +--------------------+                  |
|  | [ + ] Toggle Text |       |  ( 🎙️ ) Push-To-Talk|                  |
|  +-------------------+       +--------------------+                  |
|  (Fixed Bottom-Left)         (Fixed Bottom-Center)                   |
|                                                                      |
+----------------------------------------------------------------------+
```