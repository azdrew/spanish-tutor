Please update `tutor.py` to fix a `StreamlitSecretNotFoundError` occurring on Google Cloud Run:

1. Update the `get_secret(key, default=None)` helper:
   - Check `os.getenv(key)` first to read Cloud Run environment variables.
   - Wrap the `st.secrets` lookup in a `try/except Exception` block so it does not crash when `.streamlit/secrets.toml` does not exist.
   - Return `default` if not found.

2. Update the Firestore client initialization (`get_firestore_client`):
   - First check if `firebase-key.json` exists on disk (local development).
   - Second, attempt to read `st.secrets["firebase"]` safely inside a `try/except` block (Streamlit Cloud).
   - Finally, fall back to `firestore.Client(project="spanish-tutor-e7616")` to support Google Cloud Run's native IAM credentials.

3. Verify that `GEMINI_API_KEY` and `PEXELS_API_KEY` are assigned using `get_secret()`.