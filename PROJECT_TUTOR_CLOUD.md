# Project Context: Spanish Tutor App Migration

## Executive Summary
This document isolates the migration context for a conversational, Python-based Spanish Tutor Web Application. The application is moving from Streamlit Community Cloud into a production-ready, serverless setup on Google Cloud (GCP).

## Device & Environment Settings
- **Hardware:** MacBook Pro (Intel-based, 13-inch, 2020)
- **Local Workspace:** VS Code with the Google AntiGravity Pro extension
- **Current Runtime Environment:** Streamlit Community Cloud (connected to a private GitHub repo)
- **Target Infrastructure:** Google Cloud Run (Containerized Docker micro-service)
- **Target Database:** Google Cloud Firestore (leveraging Application Default Credentials - ADC)

## Application Architecture & Workflow
1. **User Frontend:** Streamlit web interface presenting a conversational avatar.
2. **AI Dialect Optimization:** Deep interaction loop leveraging the Google GenAI SDK (Gemini Pro) restricted strictly to the Latin American Spanish dialect.
3. **Voice Engineering Pipeline:** Text-to-speech output powered by an ElevenLabs API integration utilizing a custom voice clone.
4. **Data Management Sync:** Local data files (JSON word banks) are migrating to high-performance schemas in Cloud Firestore.

## Build Configurations Managed via IDE
### requirements.txt Target Dependencies
```text
streamlit
google-genai
google-cloud-firestore
firebase-admin
loguru
pydantic
pydantic-settings
pyyaml
python-dotenv
requests
google-cloud-secret-manager
```

### Dockerfile Blueprint (Optimized for Cold Starts)
```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
```

### Continuous Deployment Pipeline (cloudbuild.yaml)
Managed via a Git-triggered Cloud Build framework pushing directly to Artifact Registry and scaling to zero instances when idle (`--min-instances 0`) to enforce strict budget limits covered by monthly Google AI Pro renewal credits.
