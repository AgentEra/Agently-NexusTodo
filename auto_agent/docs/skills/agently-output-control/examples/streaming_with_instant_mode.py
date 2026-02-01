from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def streaming_with_instant_mode():
    agent = Agently.create_agent()

    generator = (
        agent.input("Provide a short title, a two-sentence summary, and 3 bullets.")
        .output(
            {
                "title": (str, "one-line title"),
                "summary": (str, "two-sentence summary"),
                "bullets": [(str, "bullet list, <= 12 words each")],
            }
        )
        .get_generator(type="instant")
    )

    active_field = None
    active_bullet_index = None

    for msg in generator:
        if msg.path in ("title", "summary"):
            if msg.path != active_field:
                if active_bullet_index is not None:
                    print()
                    active_bullet_index = None
                print(f"{msg.path}: ", end="", flush=True)
                active_field = msg.path
            if msg.delta:
                print(msg.delta, end="", flush=True)
            if msg.is_complete:
                print()
                active_field = None

        elif msg.wildcard_path == "bullets[*]":
            index = msg.path.split("[", 1)[1].split("]", 1)[0]
            if index != active_bullet_index:
                if active_bullet_index is not None:
                    print()
                print("- ", end="", flush=True)
                active_bullet_index = index
            if msg.delta:
                print(msg.delta, end="", flush=True)
            if msg.is_complete:
                print()
                active_bullet_index = None


if __name__ == "__main__":
    streaming_with_instant_mode()
