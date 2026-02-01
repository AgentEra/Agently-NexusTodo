---
name: agently-fastapi-service
description: FastAPI service wrappers for Agently Agent + TriggerFlow (POST, SSE, WebSocket).
---

# Agently FastAPI Service Skill

Use this skill to expose Agently/TriggerFlow as HTTP and streaming APIs.

## Key Patterns
- POST endpoint for one-shot responses.
- SSE endpoint for streaming deltas.
- WebSocket endpoint for duplex streaming.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Stream event types should be explicit (`delta`, `action`, `execution`, `done`, `error`).
- Only send cards or final summaries in `done` to avoid duplicates in the UI.
- Enforce identity + auth headers (`Authorization`, `X-User-ID`, `X-Device-ID`) on every request.
- Prefer GET query params for SSE when payload is small; rely on `sessionId` for context.

## References
- `examples/fastapi_triggerflow_service.py`

## Examples
See `examples/run.sh` for runnable commands.
