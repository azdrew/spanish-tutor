
# SPANISH TUTOR APP: RECONCILED ARCHITECTURE & UI BLUEPRINT (`PROJECT-DESIGN.md`)

## 1. Project Overview & Target Audience

* **Goal:** A responsive, adaptive single-file Streamlit web application (`tutor.py`) providing real-time, interactive Spanish conversation practice and Spaced Repetition System (SRS) flashcards.


* **Target Level & Dialect:** Advanced beginner (Duolingo A2 equivalent) focused on Latin American Spanish for movies and real-world travel/conversations.


* **Deployment & Viewports:** Hosted locally on macOS (VS Code) or Streamlit Community Cloud; viewed adaptively across desktop and Samsung Galaxy mobile web browsers over local Wi-Fi.



---

## 2. Praktika-Inspired Design System & UI Architecture

### UI Theme & Mobile Adaptation Rules

* **Color Palette & Styling:** Clean light-mode cards, violet/purple primary action accents (`#7C3AED` or `#6D28D9`), full-width touch targets (`use_container_width=True`), and friendly avatar thumbnails.


* **Sidebar Offloading:** Non-conversation controls (Persona Selector, Speech Speed, Feedback Rigor, Streaks) reside in `st.sidebar`, collapsing into a mobile hamburger menu to maintain a focused main viewport.



---

### UI Breakdown: Header, Sidebar, & Navigation

#### Header & Dynamic Status Bar (Praktika Style)

* **Dynamic Header Auto-Collapse:**
  * **Onboarding State (<2 user turns):** Full 16:9 hero banner (`assets/gabby-banner.jpg`) right at the top with warm tutor intro.
  * **Active Conversation State (>=2 user turns):** Hero image smoothly unmounts and is replaced with a slim, single-row status bar (42px avatar + *Gabby · A2 Práctica Diaria*) to reclaim maximum vertical feed height on mobile.

#### Sidebar: Persona & Lesson Settings

* **Persona Grid / Switcher:** Dropdown/selector between **Gabriella "Gabby"** (Default, warm female voice: `es-MX-DaliaNeural`) and **Mateo** (Secondary, patient male voice: `es-MX-JorgeNeural`). Displays avatar image and quick style badge.
* **Lesson Settings Controls:**
  * **Speech Speed:** Radio buttons (`0.8x`, `1.0x`, `1.2x`), mapped directly to Edge TTS rate modifiers (`-15%`, `+0%`, `+15%`).
  * **Tutor Feedback Style (Rigor):** Radio buttons mapping directly to system instructions:
    * **Soft:** Minimal corrections, focuses on flow and encouragement.
    * **Balanced (Default):** Corrects major errors and vocabulary blockers inline.
    * **Strict:** Corrects all grammar, preposition usage (*por* vs. *para*), and pronunciation errors (*r* vs. *rr*).
* **User Dashboard & Progress Metrics:** Displays current streak counter (e.g., 🔥 *9 Days*), active study plan level (*Spanish A2*), and current assigned tutor.

---

## 3. Main Interface Architecture (`tutor.py`)

```text
 ========================================================================
[ st.set_page_config(layout="centered") ]        [ ⚙️ Sidebar / Settings ]
========================================================================

+----------------------------------------------------------------------+
|                         DYNAMIC TOP BANNER                           |
|                                                                      |
|  STATE A: (user_turns < 2) -> Initial Onboarding                     |
|  +----------------------------------------------------------------+  |
|  | [ 🖼️ 16:9 Tutor Banner Image: assets/gabby-banner.jpg ]        |  |
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

### Tab 1: 💬 Practice Session (Conversation & Audio) — Praktika-Inspired Voice-First

* **Avatar & Auto-Collapsing Header:** Top 16:9 banner preview of selected tutor (Gabby/Mateo) for onboarding (<2 user turns), automatically collapsing into a slim, space-efficient status bar (avatar thumbnail + level badge) on turn 2+ to maximize chat viewport.
* **Chat Feed & Asymmetric Bubbles:** Chat history rendered via custom CSS-enhanced `st.chat_message`:
  * **Gabby (Assistant):** Left-aligned soft gray card (`#F3F4F6`).
  * **Student (User):** Right-aligned modern violet card (`#7C3AED`) with white text and an inline speaker icon inside the bubble to replay user recordings without large HTML5 audio players.
* **Centered Typing Indicator:** Animated 3-dot pulse (`•••`) centered horizontally and vertically within Gabby's chat bubble during response formulation.
* **Inline Response Action Row:** Underneath tutor replies:
  * 🔊 **Play Audio:** Plays spoken audio via high-fidelity neural voice.
  * 文A **Translate:** Toggles English translation card.
* **Bottom Floating Action Bar:**
  * **Push-to-Talk Button:** Fixed circular 76px microphone button centered at the bottom of the viewport (`position: fixed; bottom: 20px; left: 50%`), stripped of bounding boxes and labels for pure one-tap voice interaction.
  * **Left `+` Button:** Fixed at bottom left (`bottom: 28px`), toggling a dismissible text input field (`st.chat_input`) for typing mode.
  * **Viewport Clearance:** `9.5rem` bottom padding on the main block container to eliminate overlapping on mobile browsers and virtual keyboards.
* **Asynchronous Vocabulary Logging:** Model emits `[SAVE: spanish_word | english_translation]` tags; background daemon thread (`threading.Thread`) saves cards to Firestore asynchronously without freezing the chat UI.

### Tab 2: 🎴 Flashcard Deck (Leitner SRS & Spoken Challenges) — Checkpoint 2

* **Leitner Box SRS Filtering:** Displays only words due for review today based on Box 1–5 scheduling intervals.
* **Card View & Action Row:** Expander cards displaying Spanish/English terms, mastery levels, and dynamic **Pexels thumbnail images**.
* **Response Controls:** Responsive action row featuring **[✅ Got It Right]**, **[❌ Got It Wrong]**, and **[🤷 Pass / Don't Know]**.
* **Duolingo-Style Spoken Challenges:** Intermittent audio challenges prompting the user to speak Spanish translations aloud, evaluated by Gemini.
* **Pre-Made Starter Decks:** Importer widget to merge preset topics (*Numbers*, *Days & Months*, *Body Parts*) into Firestore.

---

## 4. Technical Stack & Dependencies

| Component | Technology / Library | Purpose |
| --- | --- | --- |
| **Language & UI Framework** | Python 3.x, Streamlit (`tutor.py`) | Single-file responsive Praktika-inspired web app. |
| **LLM Engine & SDK** | `google-genai` (`gemini-flash-lite-latest`, fallbacks: `gemini-3.5-flash-lite`, `gemini-3.8-flash`) | Fast, structured JSON multimodal audio transcription and conversational responses. |
| **Voice Engine (TTS)** | Microsoft Edge Neural TTS (`edge-tts` — `es-MX-DaliaNeural` / `es-MX-JorgeNeural`) | 100% free, unlimited high-fidelity Latin American Spanish neural speech with speed pacing. |
| **Fallback Speech Engine** | Google Translate TTS (`translate_tts`) | Zero-latency (0.3s) failsafe voice generation with infinite quota. |
| **Database & Cloud State** | Firebase Cloud Firestore (`google-cloud-firestore`) | Asynchronous background persistence for `words/`, `chat_sessions/`, and `user_settings/`. |
| **Configuration & Logging** | `pydantic-settings`, `pyyaml`, `loguru` | Type-safe configuration management and structured logging. |
| **Media API** | Pexels REST API | Dynamic image fetching for flashcard visual cues (Checkpoint 2). |
| **Secrets Management** | `.env`, `firebase-key.json`, and `st.secrets` | API keys excluded from version control via `.gitignore`. |

---

## 5. Database Schema (Firebase Firestore)

* **Base Reference:** `users/default_user/`

* **Subcollection 1:** `words/` *(Document ID = Spanish Word)*
* **Fields:** `english` (string), `box` (int 1–5), `last_reviewed` (date string), `next_review` (date string), `image_url` (string/null).




* **Subcollection 2:** `chat_sessions/` *(Document ID = Timestamp ID)*
* **Fields:** `timestamp` (string), `title` (string), `messages` (array of objects).




* **Subcollection 3:** `user_settings/` *(Document ID = config)*
* **Fields:** `tutor_persona` (string), `feedback_style` (string), `speech_speed` (string), `streak_days` (int).





---

## 6. Directory Structure

```text
spanish-tutor/
├── .env                  # Secrets: GEMINI_API_KEY, PEXELS_API_KEY
├── .gitignore            # Ignores .env, firebase-key.json, .streamlit/secrets.toml, etc.
├── .streamlit/           # Local Streamlit config and secrets.toml
├── config.yaml           # Non-sensitive app settings, persona prompts & preset starter decks
├── firebase-key.json     # Firebase Service Account Credentials (ignored by Git)
├── PROJECT_CONTEXT.md    # Master architecture and technical context
├── PROJECT_DESIGN.md     # Reconciled Praktika-inspired UI blueprint & specifications
├── requirements.txt      # Python dependencies
├── tutor.py              # Single-file Streamlit application entry point
├── assets/               # Avatar images (gabby.png, mateo.png)
└── docs/                 # Developer Documentation Hub
    ├── firebase_schema.md # Firestore subcollection specifications
    └── sprint_backlog.md # Checkpoint task tracking & roadmap
```