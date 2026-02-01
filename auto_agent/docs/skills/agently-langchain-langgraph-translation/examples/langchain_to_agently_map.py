from agently import Agently


LANGCHAIN_TOOL_SNIPPET = """
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    \"\"\"Search customer records for a matching query.\"\"\"
    return f\"Found {limit} matches for {query}\"
"""


LANGCHAIN_BIND_SNIPPET = """
tools = [search_database]
bound_model = model.bind_tools(tools)
result = bound_model.invoke(user_input)
"""


def langchain_to_agently_map():
    mapping = {
        "PromptTemplate": "agent.set_agent_prompt / agent.set_request_prompt + mappings",
        "LLMChain": "agent.input(...).output(...).start()",
        "OutputParser": "Output Format + response.get_data() / ensure_keys",
        "Tool": "@agent.tool_func + agent.use_tool(...)",
        "Memory": "runtime_data or custom key memory (avoid full history)",
    }

    print("LangChain -> Agently mapping")
    for k, v in mapping.items():
        print(f"- {k}: {v}")

    print("\nLangChain tool example (reference, adapted from docs):")
    print(LANGCHAIN_TOOL_SNIPPET.strip())
    print("\nLangChain tool binding example (reference, adapted from docs):")
    print(LANGCHAIN_BIND_SNIPPET.strip())

    # Agently equivalent (runnable)
    agent = Agently.create_agent()
    agent.set_agent_prompt("system", "You are a concise assistant.")
    agent.set_request_prompt("input", "Summarize the value of structured output.")
    agent.set_request_prompt("output", {"summary": (str, "one sentence")})
    print("\nAgently prompt prepared.")


if __name__ == "__main__":
    langchain_to_agently_map()
