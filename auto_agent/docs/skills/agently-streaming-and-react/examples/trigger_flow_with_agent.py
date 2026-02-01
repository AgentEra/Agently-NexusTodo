import asyncio
from agently import Agently, TriggerFlow, TriggerFlowEventData


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def trigger_flow_with_agent():
    agent = Agently.create_agent()
    flow = TriggerFlow()

    async def stream_reply(data: TriggerFlowEventData):
        data.put_into_stream("[assistant] ")
        try:
            request = agent.input(data.value)
            async for chunk in request.get_async_generator(type="delta"):
                data.put_into_stream(chunk)
            data.put_into_stream("\n")
            data.stop_stream()
            return "done"
        except Exception as exc:
            data.put_into_stream(f"\n[error] {exc}\n")
            data.stop_stream()
            return "error"

    flow.to(stream_reply).end()

    question = "Explain recursion in 3 sentences and give a simple analogy."
    for event in flow.get_runtime_stream(question, timeout=None):
        print(event, end="", flush=True)


if __name__ == "__main__":
    trigger_flow_with_agent()
