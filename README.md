# Lyftr AI – LLM Chatbot with Key Failover and Response Caching

Production-grade full-stack AI chatbot built with **React**, **TypeScript**, **Vite**, **Python FastAPI**, **LiteLLM**, and **SQLite**. Features automated key-pool failover across multiple API keys, LiteLLM built-in response caching with real-time detection, request-scoped failure simulation, per-request token usage tracking, and multi-turn conversational memory.

---

## 1. Live URLs

- **Frontend Application**: `https://lyftr-ai-frontend.vercel.app` *(Pending live deployment authorization)*
- **Backend API Base**: `https://lyftr-ai-backend.railway.app` *(Pending live deployment authorization)*
- **Health Check Endpoint**: `https://lyftr-ai-backend.railway.app/health` *(Pending live deployment authorization)*

---

## 2. Run locally: with Docker and without

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for Docker runs)

### With Docker & Docker Compose (Recommended)

1. Clone and navigate to the project directory:
   ```bash
   cd "lyftr AI"
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   *Populate `LLM_API_KEYS` with your real keys (e.g. `LLM_API_KEYS=sk-key1,sk-key2`).*

3. Launch the full stack with Make or Docker Compose:
   ```bash
   make up
   # Or directly via docker compose:
   docker compose up --build -d
   ```

4. Access the services:
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

5. Stop the containers:
   ```bash
   make down
   # Or:
   docker compose down
   ```

---

### Without Docker (Direct Local Execution)

#### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend initializes the SQLite schema automatically and begins listening on port 8000.

#### 2. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

#### 3. Run Backend Automated Tests
```bash
cd backend
pytest -v tests/test_api.py
```

---

## 3. Design decisions: key fallback, caching, SQLite session storage

### Automatic Key Fallback & Key Pool Architecture
- **Safe Key Isolation**: Configured keys (`LLM_API_KEYS`) are parsed into an ordered pool indexed as `key_1`, `key_2`, `key_3`, etc. Raw API secrets are strictly isolated on the server and are **never** returned in API responses, logs, or sent to the frontend.
- **Provider Error Detection**: When a request to `key_n` encounters eligible provider errors (`429 Too Many Requests`, quota exhaustion, or `5xx Server Errors`), the service logs a warning, increments `fallback_attempts`, and automatically retries with `key_n+1`.
- **Fault-Tolerant Resilience**: Non-provider errors (e.g. malformed payload `400` or `422`) fail fast without consuming subsequent keys. If all configured keys in the pool are exhausted, the endpoint cleanly returns HTTP 503 (`{"detail": "all providers unavailable"}`) and aborts persisting the failed user prompt.

### LiteLLM Built-in Response Caching
- **Native Gateway Caching**: Employs LiteLLM's official `Cache` subsystem (`diskcache` / in-memory `local`). No custom mock dictionaries are used.
- **Strict Cache Key Identity**: Cache keys are derived deterministically from `model` + the **complete message list** (system prompt + cumulative session history + new user message).
- **Accurate Cache Hit Detection**: Cache hits are identified directly from LiteLLM's internal metadata (`_hidden_params['cache_hit']`), reporting `resolution_source: LLM_CACHE`, `key_id: null`, and `fallback_attempts: 0`, while preserving identical text and per-request token metrics.
- **Context Isolation**: A prompt sent in Session A will hit `LIVE_INFERENCE`. An identical prompt sent as the first message in Session B hits `LLM_CACHE`. However, multi-turn conversations have differing history arrays and therefore correctly isolate their cache keys.

### SQLite Session Storage
- **Zero External Dependencies**: Implemented strictly with SQLite using SQLAlchemy ORM.
- **Automatic Schema Initialization**: The `messages` table is automatically verified and created during the FastAPI lifespan startup event.
- **Atomic Turn Persistence**: To satisfy the invariant that failed requests (such as 422 or 503) are never stored in history, messages are committed only after successful model resolution.
- **Container Volume Persistence**: Docker Compose mounts a named volume (`sqlite_data`) to `/data` (`DATABASE_URL=sqlite:////data/app.db`), guaranteeing conversation history survives container restarts and upgrades.
- **System Prompt Separation**: System prompts are passed directly to the LLM context but are excluded from the `GET /sessions/{session_id}/messages` endpoint.

---

## 4. Verification: how to see failover, cache hits and per-message token usage

### How to See LIVE_INFERENCE vs. LLM_CACHE
1. Open the UI at `http://localhost:3000`.
2. Send: `Explain machine learning in one short paragraph.`
   - Notice the badge displays `LIVE_INFERENCE`, with latency (e.g., `812 ms`), input tokens, output tokens, and key `key_1`.
3. Click **New Chat** (which creates a new `session_id`).
4. Send the exact same prompt: `Explain machine learning in one short paragraph.`
   - Notice the badge instantly displays `LLM_CACHE`.
   - Latency drops significantly (e.g., `< 15 ms`).
   - `key_id` is `cached` (`null`), `fallbacks: 0`, and the reply text is identical.

### How to Demonstrate Key Failover with X-Simulate-Failure
The application includes a built-in Developer Mode test hook:
1. Click the **Dev Mode** button in the top navigation bar.
2. Select **Simulate key_1 Rate Limit (429)**.
3. Send a unique query: `What is quantum entanglement?`
   - Key 1 simulates a 429 error and triggers automatic fallback.
   - The response succeeds with HTTP 200, displaying `key_2` and `fallbacks: 1`.
4. Select **Simulate All Keys Failing (*=429)**.
   - Send any prompt: The UI displays `"AI providers are temporarily unavailable. Please try again."` (HTTP 503).
   - No broken turns are recorded to the SQLite session history.

### Verifying Per-Request Token Usage
- In the metadata strip of each assistant response:
  - `↑ <input_tokens> in`: Represents prompt tokens for that specific request (system prompt + history + current message).
  - `↓ <output_tokens> out`: Represents completion tokens for that specific assistant answer.
- Subsequent turns in the same session will show increased `input_tokens` as conversation history grows, while starting a new session resets `input_tokens`.

---

## 5. Setup Used: editor and AI tools

- **IDE**: Visual Studio Code / Cursor with Python, TypeScript, and Docker extensions.
- **AI Tooling**: Google DeepMind Antigravity AI Agent for architecture design, code generation, refactoring, test suite development, and containerization.
- **Python Environment**: Python 3.13 / 3.11 with virtual environment (`venv`).
- **Frontend Tooling**: Vite 5, React 18, TypeScript 5.

---

## 6. Bonus features (if any): what was added beyond the requirements and why

1. **Interactive Developer Mode UI**: An integrated modal and header status badge allowing testers and reviewers to inject `X-Simulate-Failure` headers on demand (`key_1=429`, `key_1=500`, `*=429`) directly from the browser without needing curl or Postman.
2. **Dynamic Session Settings Panel**: An intuitive modal allowing users to customize and test system prompts on the fly, proving that changing the system prompt changes the complete message list and alters cache identity.
3. **Live Health & Key Pool Monitor**: Real-time status pill in the header checking backend connectivity, number of active keys configured, and LiteLLM cache engine readiness.
4. **Rich Markdown & Syntax Highlighting**: Clean rendering of code snippets, bullet points, and formatted text in assistant replies using `react-markdown`.
5. **Quick Prompt Starter Cards**: One-click prompt starters on empty chats to immediately test live inference, response caching, and key failover.
