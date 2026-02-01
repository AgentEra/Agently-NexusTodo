import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agently import Agently, TriggerFlow, TriggerFlowEventData


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)

agent = Agently.create_agent()
app = FastAPI()


class ChatRequest(BaseModel):
    input: str


flow_once = TriggerFlow()
flow_stream = TriggerFlow()


@flow_once.chunk
async def once_reply(data: TriggerFlowEventData):
    result = await (
        agent.input(data.value)
        .output({"reply": (str, "one-sentence reply")})
        .async_start()
    )
    return result


@flow_stream.chunk
async def stream_reply(data: TriggerFlowEventData):
    response = agent.input(data.value).get_response()
    async for delta in response.get_async_generator(type="delta"):
        data.put_into_stream({"event": "delta", "data": delta})
    final_data = await response.async_get_data()
    data.put_into_stream({"event": "final", "data": final_data})
    data.stop_stream()
    return final_data


flow_once.to(once_reply).end()
flow_stream.to(stream_reply).end()


@app.post("/chat")
async def chat_once(req: ChatRequest):
    return await flow_once.async_start(req.input)


@app.post("/chat/stream")
async def chat_sse(req: ChatRequest):
    async def event_generator():
        async for item in flow_stream.get_async_runtime_stream(req.input, timeout=None):
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/chat/ws")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            user_input = payload.get("input", "")
            async for item in flow_stream.get_async_runtime_stream(user_input, timeout=None):
                try:
                    await ws.send_json(item)
                except WebSocketDisconnect:
                    return
                except Exception:
                    return
                if item.get("event") == "final":
                    break
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=15590)
