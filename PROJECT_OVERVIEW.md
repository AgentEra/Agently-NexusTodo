# Project Overview & Startup

This document provides a top-level overview and a minimal startup guide. For full details, follow the component docs referenced below.

Chinese version: [PROJECT_OVERVIEW_cn.md](PROJECT_OVERVIEW_cn.md)

## Architecture Overview
- **backend** (Go): task API, persistence, device registration.
- **auto_agent** (Python): ReAct-based orchestration, structured outputs, SSE streaming.
- **client** (Web/Electron): chat UI with streaming bubbles and task cards.

## Startup (Minimal Guide)
1) **Backend** (default port `8080`)
   - From `backend/`, run:
     ```bash
     go run main.go
     ```

2) **Auto Agent** (default port `15590`)
   - From repo root, run:
     ```bash
     python -m uvicorn auto_agent.app:app --host 0.0.0.0 --port 15590
     ```
   - It uses `TASK_API_BASE_URL` to reach the backend (`http://localhost:8080/api` by default).

3) **Client**
   - From `client/`, run:
     ```bash
     npm install
     npm run dev
     ```

## Component Documentation
- Backend: [backend/docs/api-documentation.md](backend/docs/api-documentation.md), [backend/docs/backend-design.md](backend/docs/backend-design.md)
- Auto Agent: [auto_agent/docs/dev_design.md](auto_agent/docs/dev_design.md), [auto_agent/docs/api-documentation.md](auto_agent/docs/api-documentation.md)
- Chat/LLM ops: [auto_agent/docs/spec-dd-llm-chat-ops.md](auto_agent/docs/spec-dd-llm-chat-ops.md)
- Client: [client/docs/client-documentation.md](client/docs/client-documentation.md)

## Testing
- Auto Agent tests: [auto_agent/docs/test-report.md](auto_agent/docs/test-report.md)
- Backend tests: [backend/docs/test-report.md](backend/docs/test-report.md)
