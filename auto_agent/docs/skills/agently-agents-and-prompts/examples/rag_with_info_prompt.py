from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def rag_with_info_prompt():
    agent = Agently.create_agent()

    kb = [
        {"title": "Agently Output Format", "content": "Stabilizes structured outputs."},
        {"title": "TriggerFlow", "content": "Event-driven workflow orchestration."},
        {"title": "Session/Memo", "content": "Memory and context compression for multi-turn chats."},
    ]

    question = "What are Agently's core capabilities?"
    knowledge = [item for item in kb if "Agently" in item["title"] or "TriggerFlow" in item["title"]]

    response = (
        agent.set_request_prompt("input", question)
        .set_request_prompt("info", {"knowledge": knowledge})
        .output(
            {
                "answer": (str, "one-sentence answer"),
                "sources": [(str, "source titles")],
            }
        )
        .get_response()
    )

    print(response.get_data())


if __name__ == "__main__":
    rag_with_info_prompt()
