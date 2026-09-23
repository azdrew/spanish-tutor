# SPANISH TUTOR: SPRINT BACKLOG & ROADMAP

---

## 🎯 [ ] CHECKPOINT 1: First Publish on Streamlit Cloud
**Goal:** Prove the end-to-end pipeline works (Mac -> GitHub -> Streamlit Cloud) with a clean connection to Firestore and Gemini before adding complex UI.

* [x] Remove legacy CLI prototype code from `tutor.py`[cite: 11].
* [x] Add all required imports from `requirements.txt` (`streamlit`, `google-genai`, `google-cloud-firestore`, `pyyaml`, `loguru`)[cite: 11].
* [x] Configure resilient secrets resolution (`st.secrets` with `.env` / `firebase-key.json` fallback)[cite: 11].
* [ ] Deploy to Streamlit Community Cloud and verify the initial UI loads successfully on a mobile browser[cite: 11].

---

## 🎯 [ ] CHECKPOINT 2: The MVP (Minimum Viable Product)
**Goal:** Deliver the core value proposition—talking to Gabby and saving words to a spaced repetition deck—using the Praktika-inspired layout.

* [x] Create `config.yaml` to store `personas` (Gabby/Mateo) and `preset_decks` starter datasets[cite: 10, 11].
* [ ] Build Tab 1 ("💬 Practice") with the compact 16:9 tutor banner (`st.columns`), avatar chat feed, and `st.audio_input` push-to-talk widget[cite: 9, 10, 11].
* [ ] Integrate Gemini 3.7 Flash API to process raw audio bytes/text and return conversational Spanish responses[cite: 9, 11].
* [ ] Implement automated vocabulary capture: parse `[SAVE: spanish_word]` tags via regex and upsert to Firestore `words/` subcollection[cite: 9, 11].
* [ ] Add inline spoken tutor TTS audio playback (🔊 Play Audio) and translation toggle (🈳 Translate) to chat bubbles[cite: 9, 10].
* [ ] Build Tab 2 ("🎴 Flashcards") with basic Leitner Box logic, filtering words due today (`next_review <= today`), and response controls ([Got It], [Wrong], [Pass])[cite: 9, 11].

---

## 🎯 [ ] CHECKPOINT 3: V1 Finished and Published
**Goal:** Polish the app into a fully-featured, cross-device experience ready for daily use and external testers.

* [ ] Build offloaded `st.sidebar` controls for Persona Selection (Gabby/Mateo), Speech Speed, Feedback Rigor (Soft/Balanced/Strict), and Streak metrics[cite: 10, 11].
* [ ] Implement Firestore persistence for `user_settings/config` (persona, feedback rigor, speech speed, streak days)[cite: 9, 10].
* [ ] Implement `import_preset_deck()` function to load starter decks from `config.yaml` into Firestore without duplicates[cite: 10, 11].
* [ ] Integrate Pexels API fetching for dynamic thumbnail image backfilling on missing flashcard images[cite: 9, 11].
* [ ] Implement Spoken "Say the Word" audio challenges in Tab 2 using `st.audio_input` and Gemini evaluation[cite: 9, 11].
* [ ] Save and load historical chat threads in Firestore subcollection `chat_sessions/`[cite: 9, 11].
* [ ] Implement floating "💡 What to say?" hint chip with 5-second silence trigger[cite: 9, 10].
* [ ] Final QA on Samsung Galaxy mobile browser to ensure full touch responsiveness and layout scaling[cite: 11, 22].