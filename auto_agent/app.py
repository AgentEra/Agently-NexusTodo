from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from .agent_core import AgentCore, ReActPlanner, SessionStore
from .config import settings
from .models import ChatMessage, ChatRequest, ChatResponse
from .task_api import TaskApi


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(timeout=settings.request_timeout)
    task_api = TaskApi(settings.task_api_base_url, client)
    session_store = SessionStore(settings.max_session_messages)
    planner = ReActPlanner()
    app.state.agent_core = AgentCore(task_api, session_store, planner)
    try:
        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)


def _resolve_identity(
    req_user_id: Optional[str],
    req_device_id: Optional[str],
    header_user_id: Optional[str],
    header_device_id: Optional[str],
) -> tuple[str, str]:
    user_id = req_user_id or header_user_id
    device_id = req_device_id or header_device_id

    if not user_id or not device_id:
        raise HTTPException(status_code=400, detail="userId 和 deviceId 不能为空")

    if req_user_id and header_user_id and req_user_id != header_user_id:
        raise HTTPException(status_code=400, detail="userId 与请求头不一致")
    if req_device_id and header_device_id and req_device_id != header_device_id:
        raise HTTPException(status_code=400, detail="deviceId 与请求头不一致")

    return user_id, device_id


def _auth_headers(
    authorization: Optional[str], user_id: str, device_id: str
) -> dict[str, str]:
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization 头")
    return {
        "Authorization": authorization,
        "X-User-ID": user_id,
        "X-Device-ID": device_id,
    }


@app.post("/agent/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID"),
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-ID"),
):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    user_id, device_id = _resolve_identity(req.userId, req.deviceId, x_user_id, x_device_id)
    headers = _auth_headers(authorization, user_id, device_id)

    agent_core: AgentCore = app.state.agent_core
    result = await agent_core.handle_chat(req.sessionId, req.messages, headers)
    return result


@app.get("/agent/chat/stream")
async def chat_stream(
    message: str = Query(..., min_length=1),
    sessionId: Optional[str] = Query(default=None),
    userId: Optional[str] = Query(default=None),
    deviceId: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID"),
    x_device_id: Optional[str] = Header(default=None, alias="X-Device-ID"),
):
    user_id, device_id = _resolve_identity(userId, deviceId, x_user_id, x_device_id)
    headers = _auth_headers(authorization, user_id, device_id)
    agent_core: AgentCore = app.state.agent_core

    async def event_generator():
        try:
            async for event_type, payload in agent_core.handle_chat_stream(
                sessionId,
                [ChatMessage(role="user", content=message)],
                headers,
            ):
                if event_type == "delta":
                    yield _sse_event("delta", payload)
                elif event_type == "action":
                    yield _sse_event("action", payload)
                elif event_type == "execution":
                    yield _sse_event("execution", payload)
                elif event_type == "done":
                    yield _sse_event("done", payload)
                elif event_type == "error":
                    yield _sse_event("error", payload)
        except Exception as exc:
            yield _sse_event("error", {"code": "INTERNAL_ERROR", "message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _chunk_text(text: str, size: int) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _sse_event(event_type: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=15590)
