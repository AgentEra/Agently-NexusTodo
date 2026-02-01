import os
from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def prompt_config_from_yaml():
    agent = Agently.create_agent()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "prompt_template.yaml")

    result = agent.load_yaml_prompt(
        yaml_path,
        mappings={"question": "What is the core value of structured output?"},
    ).start()

    print(result)


if __name__ == "__main__":
    prompt_config_from_yaml()
