from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def structured_output_with_ensure_keys():
    agent = Agently.create_agent()

    response = (
        agent.input("Give one product improvement suggestion and 2 concrete actions.")
        .output(
            {
                "recommendation": (str, "one-sentence recommendation"),
                "actions": [(str, "concrete actions")],
            }
        )
        .get_response()
    )

    data = response.get_data(
        ensure_keys=["recommendation", "actions[*]"],
        key_style="dot",
        max_retries=2,
        raise_ensure_failure=False,
    )

    print(data)


if __name__ == "__main__":
    structured_output_with_ensure_keys()
