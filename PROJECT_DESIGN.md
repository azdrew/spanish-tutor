
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

#### Header & Status Bar (Praktika Style)

* **Active Topic Banner:** Displays current level, module, and focus area (e.g., *A2 · Frases Esenciales para Viajar - Intereses: Viajes y Turismo*).


* **Action Header Card:** Shows current grammar topic (*Comparación gramatical*) with direct **[Grammar]**, **[Continue]**, and **[Restart]** controls.



#### Sidebar: Persona & Lesson Settings

* **Persona Grid / Switcher:** Dropdown/selector between **Gabriella "Gabby"** (Default, warm female voice) and **Mateo** (Secondary, patient male voice). Displays avatar image and quick style badge (*Standard*).


* **Lesson Settings Modal / Controls:**
* **Speech Speed:** Slider/Select (`0.8x`, `1.0x`, `1.2x`).


* **Text Size:** Selector (`Regular`, `Large`).


* **Response Length:** Selector (`Short`, `Normal`, `Detailed`).


* **Tutor Feedback Style (Rigor):** Radio buttons mapping directly to system instructions:


* **Soft:** Minimal corrections, focuses on flow and encouragement.


* **Balanced (Default):** Corrects major errors and vocabulary blockers inline.


* **Strict:** Corrects all grammar, preposition usage (*por* vs. *para*), and pronunciation errors (*r* vs. *rr*).






* **User Dashboard & Progress Metrics:** Displays current streak counter (e.g., 🔥 *9 Days*), active study plan level (*Spanish A2*), and current assigned tutor.



---

## 3. Main Interface Tabs (`tutor.py`)

```
========================================================================================================
🇪🇸 Spanish Tutor                                                               [ ⚙️ Sidebar / Settings ]
========================================================================================================
 [ Active Banner: A2 · Frases Esenciales para Viajar - Intereses: Viajes y Turismo ][cite: 1]
 ------------------------------------------------------------------------------------------------------
 |  💬 Practice Session  |  🎴 Flashcard Deck  |
 ------------------------------------------------------------------------------------------------------

```

### Tab 1: 💬 Practice Session (Conversation & Audio)

* **Avatar & Chat Feed:** Top avatar preview of selected tutor (Gabby/Mateo) with chat bubbles rendering past messages (`st.chat_message`).


* **Audio Player & Translation Toggles:** Assistant speech bubbles feature inline action buttons:
* 🔊 **Play Audio:** Auto-plays spoken response via TTS.


* 🈳 **Translate:** Toggles English translation view.




* **Prompt Helper / Hint Chip:** Floating **"💡 What to say?"** button that opens a suggestion box when tapped or after 5 seconds of silence.


* **Bottom Input Bar (Push-to-Talk):**
* `st.audio_input` microphone widget allowing users to tap to record, review/delete, and send.


* Option menu (`+` button) for extra tools (e.g., Quick Grammar Reference).




* **Automated Word Log:** Background regex parsing intercepts `[SAVE: spanish_word]` tags from model output, strips them from the UI, and automatically saves the word to Firestore.



### Tab 2: 🎴 Flashcard Deck (Leitner SRS & Spoken Challenges)

* **Leitner Box SRS Filtering:** Displays only words due for review today based on Box 1–5 scheduling intervals.


* **Card View & Action Row:** Expander cards displaying Spanish/English terms, mastery levels, and dynamic **Pexels thumbnail images**.


* **Response Controls:** Responsive action row featuring **[✅ Got It Right]**, **[❌ Got It Wrong]**, and **[🤷 Pass / Don't Know]**.


* **Duolingo-Style Spoken Challenges:** Intermittent audio challenges prompting the user to speak Spanish translations aloud, evaluated by Gemini.


* **Pre-Made Starter Decks:** Importer widget to merge preset topics (*Numbers*, *Days & Months*, *Body Parts*) into Firestore.



---

## 4. Technical Stack & Dependencies

| Component | Technology / Library | Purpose |
| --- | --- | --- |
| **Language & UI Framework** | Python 3.x, Streamlit (`tutor.py`) | Single-file responsive web dashboard.

 |
| **LLM Engine & SDK** | `google-genai` (`gemini-3.7-flash` / `gemini-flash-latest`) | Fast, low-latency conversational audio and evaluation.

 |
| **Database & Cloud State** | Firebase Cloud Firestore (`google-cloud-firestore`) | NoSQL storage for `words/`, `chat_sessions/`, and `user_settings/` subcollections.

 |
| **Configuration & Logging** | `pydantic-settings`, `pyyaml`, `loguru` | Type-safe configuration management and structured logging.

 |
| **Media API** | Pexels REST API | Dynamic image fetching for flashcard visual cues.

 |
| **Secrets Management** | `.env`, `firebase-key.json`, and `st.secrets` | API keys excluded from version control via `.gitignore`.

 |

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