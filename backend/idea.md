## Features

- AI-generated reply creation injected into Gmail view using memory + preference in backend
- One-click smart replies and contextual actions (remind, label, tag)
- Memory-aware suggestions based on prior interactions and email content
- Customizable dashboard with categorized widgets (Todos, Finance, Follow-ups, View Later)
- Automatic batch reply generation and email tagging using LLMs
- Secure Google login with access to Gmail via API
- Chrome Extension overlay with Gmail integration

## Components

### 1. Chrome Extension
### 2. Web Dashboard (Next.js)
### 3. FastAPI Backend
### 4. Database Layer (PostgreSQL)

## What Each Component Does

### Chrome Extension
- Injects UI elements into the Gmail DOM (summary chips, reply buttons)
- Scrapes relevant content from visible emails (sender, subject, body)
- Sends scraped content to backend for real-time processing
- Displays responses (summaries, reply suggestions, memory cues)
- Communicates with backend via secure API endpoints

### Web Dashboard
- Handles Google OAuth login
- Shows categorized views of user’s inbox (urgent, follow-ups, finances)
- Offers control panel to customize memory preferences, tagging rules, reply tone
- Optionally displays batch AI replies generated overnight

### FastAPI Backend
- Orchestrates Gmail API access using tokens stored after login
- Runs AI agents (summarization, intent detection, reminder/finance extractors)
- Exposes RESTful endpoints for extension and dashboard consumption
- Handles logic for tagging, reply generation, and memory updates
- Manages queues or cron jobs for batch processing

### Database Layer
- **PostgreSQL**: stores structured data — email metadata, tags, reminders, reply drafts
- **MongoDB**: stores unstructured memory objects, raw AI outputs, user preferences
- **(Optional)** Vector store: used for semantic memory embedding and retrieval

---

## How Each Component Should Be Structured

### Chrome Extension
- `manifest.json` with content script injection into Gmail
- `content_scripts/` for DOM parsing and UI injection
- `background.js` or `service_worker.js` for auth/session handling
- `popup/` for lightweight dashboard or settings menu
- Uses `fetch()` to communicate with backend

### Web Dashboard (React + Vite + TS)
- Auth page for Google login using OAuth flow
- Dashboard layout with React components (Bento tiles, filters, etc.)
- API layer (`/api/`) to call backend FastAPI endpoints
- Uses server components or ISR/SSR for async dashboard content

### FastAPI Backend
- `app/main.py`: entrypoint with app setup and middleware
- `api/`: route modules (`email.py`, `reply.py`, `auth.py`)
- `services/`: AI agents and Gmail API clients
- `core/`: config and token logic (`config.py`, `auth.py`)
- `models/`: Pydantic schemas for all API inputs/outputs
- `db/`: database connection utils and query helpers
- `.env`: contains Gmail client secret, database URLs, etc.

---

Let me know if you want this in a Markdown README template next.
