# FIREBASE CLOUD FIRESTORE SCHEMA SPECIFICATION

This document outlines the database schema and structure used by the Spanish Tutor application.

---

## 1. Base User Path
All user data is partitioned under individual user root documents:
```text
users/{user_id}/   (Default: users/default_user/)
```

---

## 2. Subcollection: `words`
Stores vocabulary cards, SRS progress (Leitner boxes), and media references.

* **Path:** `users/{user_id}/words/{spanish_word}`
* **Document ID:** The Spanish word (lowercased, trimmed, e.g., `desarrollar`)

### Field Specifications

| Field | Type | Description |
| :--- | :--- | :--- |
| `spanish` | `string` | The Spanish word or phrase (e.g. `"la manzana"`). |
| `english` | `string` | English translation meaning (e.g. `"apple"`). |
| `box` | `integer` | Leitner SRS box level (1 to 5). Starts at 1. |
| `last_reviewed` | `timestamp` | UTC timestamp of last practice session. |
| `next_review` | `timestamp` | UTC timestamp when the card is next due. |
| `image_url` | `string` | Pexels image thumbnail URL (or empty string). |
| `tags` | `array<string>` | Optional category tags (e.g. `["starter_deck", "food"]`). |

---

## 3. Subcollection: `chat_sessions`
Stores completed and active conversation transcripts for review and context continuity.

* **Path:** `users/{user_id}/chat_sessions/{session_id}`
* **Document ID:** Timestamp ID (e.g., `session_20260901_150000`)

### Field Specifications

| Field | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `string` | Unique session identifier. |
| `timestamp` | `timestamp` | UTC creation timestamp. |
| `title` | `string` | Generated summary title (e.g. `"Ordering at a restaurant"`). |
| `persona` | `string` | Persona used (`"Gabby"` or `"Mateo"`). |
| `messages` | `array<map>` | Ordered list of turns: `[{ "role": "user" \| "assistant", "content": string, "timestamp": string }]`. |

