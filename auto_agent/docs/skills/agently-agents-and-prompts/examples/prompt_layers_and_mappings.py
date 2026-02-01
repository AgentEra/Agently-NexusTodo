from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def prompt_layers_and_mappings():
    agent = Agently.create_agent()

    agent.set_agent_prompt("system", "You are an enterprise assistant.")
    agent.set_agent_prompt("instruct", ["Be concise", "Give the conclusion first, then rationale"])

    response = (
        agent.set_request_prompt(
            "input",
            "Give one actionable suggestion for {name} ({role}).",
            mappings={"name": "Alex", "role": "Product Manager"},
        )
        .output({"advice": (str, "one-sentence advice")})
        .get_response()
    )

    print(response.get_data())


if __name__ == "__main__":
    prompt_layers_and_mappings()
