from agently import Agently


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def multi_agent_router():
    support_agent = Agently.create_agent()
    support_agent.set_agent_prompt("system", "You are a support agent.")
    support_agent.set_agent_prompt("instruct", ["Be concise", "Provide actionable steps"])

    marketing_agent = Agently.create_agent()
    marketing_agent.set_agent_prompt("system", "You are a marketing copywriter.")
    marketing_agent.set_agent_prompt("instruct", ["Use positive tone", "Highlight benefits"])

    def route(question: str):
        keywords = ["refund", "error", "fail", "issue", "problem", "bug"]
        if any(word in question.lower() for word in keywords):
            return "support", support_agent
        return "marketing", marketing_agent

    questions = [
        "My payment failed. What should I do?",
        "Write one short slogan highlighting speed and stability.",
    ]

    for question in questions:
        tag, agent = route(question)
        if tag == "support":
            response = (
                agent.input(question)
                .output({"reply": (str, "one-sentence reply"), "steps": [(str, "steps")]})
                .get_response()
            )
        else:
            response = (
                agent.input(question)
                .output({"slogan": (str, "one-line slogan"), "points": [(str, "benefits")]})
                .get_response()
            )
        print(tag, response.get_data())


if __name__ == "__main__":
    multi_agent_router()
