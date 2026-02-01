from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def key_waiter_early_field():
    agent = Agently.create_agent()

    agent.input("Explain recursion in one sentence.")
    agent.output(
        {
            "thinking": (str, "brief thought"),
            "answer": (str, "one-sentence answer"),
        }
    )

    early = agent.get_key_result("thinking")
    print("thinking:", early)

    agent.input("Explain recursion in one sentence.")
    agent.output(
        {
            "thinking": (str, "brief thought"),
            "answer": (str, "one-sentence answer"),
        }
    )

    for key, value in agent.wait_keys(["thinking", "answer"]):
        print(key, value)


if __name__ == "__main__":
    key_waiter_early_field()
