from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def response_event_streams():
    agent = Agently.create_agent()

    response = agent.input("Explain recursion in one sentence.").get_response()
    print("delta:", end=" ")
    for chunk in response.get_generator(type="delta"):
        print(chunk, end="", flush=True)
    print("\n")

    response = agent.input("Explain recursion in one sentence.").get_response()
    counts = {}
    for event, _ in response.get_generator(
        type="specific",
        specific=["reasoning_delta", "delta", "done"],
    ):
        counts[event] = counts.get(event, 0) + 1
    print("specific_event_counts:", counts)


if __name__ == "__main__":
    response_event_streams()
