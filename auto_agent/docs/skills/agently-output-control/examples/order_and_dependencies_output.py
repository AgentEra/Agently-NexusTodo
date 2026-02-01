from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def order_and_dependencies_output():
    agent = Agently.create_agent()

    result = (
        agent.input("How would you prepare a small product release checklist?")
        .output(
            {
                "checklist": [
                    {
                        "item": (str, "checklist item"),
                        "reason": (str, "why it matters"),
                    }
                ],
                "confirmed": (str, "only confirmed information"),
                "unknowns": (str, "items still to be confirmed"),
            }
        )
        .start(
            ensure_keys=["checklist[*].item", "checklist[*].reason"],
        )
    )

    print(result)


if __name__ == "__main__":
    order_and_dependencies_output()
