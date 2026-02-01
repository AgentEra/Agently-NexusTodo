from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    deviceId: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)


class Action(BaseModel):
    intent: str
    params: dict[str, Any] = Field(default_factory=dict)


class Execution(BaseModel):
    status: Literal["success", "failed", "skipped"]
    result: Any = Field(default_factory=dict)


class ChatResponse(BaseModel):
    sessionId: str
    assistantMessage: str
    action: Action
    execution: Execution
