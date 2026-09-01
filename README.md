# 🇪🇸 Spanish Tutor App

An interactive, AI-powered Spanish language tutor and spaced-repetition flashcard web application built with Python and Streamlit[cite: 1, 3, 4, 7]. The app is designed to help advanced beginners (focusing on Latin American Spanish) practice natural conversation for real-world scenarios, television, and film[cite: 1, 8, 9].

---

## 📸 Overview & Architecture

The project features a single-file, responsive Streamlit dashboard (`tutor.py`) that unifies real-time conversational roleplay with an interactive vocabulary flashcard deck[cite: 1, 3, 4, 12].

```text
            +---------------------------------+
            | Streamlit Web UI (`tutor.py`)   |
            +---------------------------------+
             /                               \
Tab 1: Conversation                     Tab 2: Flashcards
-------------------                     ------------------
st.audio_input (Voice)        * Leitner Box SRS (1–5)  Gemini 2.5 Flash API             * Pexels Thumbnail Fetching  Regex Tag Parsing ([SAVE:])     * "Say the Word" Audio QuizAuto-saving to Firestore        * Pre-made Starter Decks
\                               /
+-----------------------------+
|  Firebase Cloud Firestore   |
+-----------------------------+
```

## 🚀 Key Features

* **Interactive Audio Tutor ("Gabby" & "Mateo"):** Speak directly to the app using push-to-talk native audio recording (`st.audio_input`)[cite: 3, 4]. Default tutor persona Gabriella ("Gabby") responds in conversational Spanish while providing gentle English corrections for major grammatical or structural errors[cite: 3, 9].
* **Automated Vocabulary Logging:** During conversations, when key vocabulary or conjugations are missed or used in "Spanglish," Gemini appends background `[SAVE: word]` tags[cite: 1, 3, 4]. The app strips these tags from display and automatically adds the word to your active review deck in Cloud Firestore[cite: 1, 3, 4, 11].
* **Leitner Box Spaced Repetition (SRS):** Flashcards track progress through Boxes 1–5[cite: 3]. Items move up or down in interval scheduling based on user review performance[cite: 3, 8].
* **Dynamic Media Lookup:** Automatically fetches thumbnail images for vocabulary cards via the Pexels API and caches the image URL in Firestore to optimize subsequent views[cite: 8, 11].
* **Interactive Spoken Challenges:** Features Duolingo-style random interjections that prompt you to speak Spanish translations aloud, evaluated in real time by Gemini.
* **Pre-Made Starter Decks:** Easily merge starter topics (e.g., *Numbers 1–10*, *Days & Months*, *Body Parts*) into your main vocabulary database without overwriting existing progress[cite: 9, 11].

## 🛠️ Tech Stack & Dependencies

* **Language & UI:** Python 3.x[cite: 5], [Streamlit](https://streamlit.io/)[cite: 1, 3, 4]
* **LLM SDK:** `google-genai` (utilizing `gemini-3.6-flash`)[cite: 1, 3, 4]
* **Database:** Firebase Cloud Firestore (`google-cloud-firestore`)[cite: 1, 11]
* **Configuration & Logging:** `pydantic-settings`, `pyyaml`, `loguru`
* **External APIs:** Pexels API (for thumbnail fetching)[cite: 11]