from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def single_request_multi_read():
    agent = Agently.create_agent()

    response = (
        agent.input("Explain structured output in one sentence and list 2 benefits.")
        .output(
            {
                "intro": (str, "one-sentence definition"),
                "advantages": [(str, "benefits")],
            }
        )
        .get_response()
    )

    print("text:", response.get_text())
    print("data:", response.get_data())
    print("meta:", response.get_meta())


if __name__ == "__main__":
    single_request_multi_read()
