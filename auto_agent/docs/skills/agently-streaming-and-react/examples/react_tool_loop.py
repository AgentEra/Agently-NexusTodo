import ast
import json
import time
from agently import Agently, TriggerFlow, TriggerFlowEventData
from agently.builtins.tools import Search


Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
        "model_type": "chat",
    },
)


def safe_eval(expr: str) -> str:
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Num,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Load,
        ast.Constant,
        ast.FloorDiv,
    )
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return "invalid expression"

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            return "invalid expression"
    try:
        return str(eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}))
    except Exception:
        return "invalid expression"


search = Search(
    proxy="http://127.0.0.1:7890",
    region="us-en",
    options={"safesearch": "on"},
)


def merge_memory(existing: list[str], new_items: list[str], max_items: int = 6) -> list[str]:
    seen = set()
    merged = []
    for item in existing + new_items:
        item = str(item).strip()
        if not item or item in seen:
            continue
        merged.append(item)
        seen.add(item)
    if len(merged) > max_items:
        merged = merged[-max_items:]
    return merged


def react_tool_loop():
    agent = Agently.create_agent()
    agent.set_agent_prompt(
        "system",
        "You are a tool-using assistant. Use ReAct format: thought->action->observation. "
        "Use key memory and avoid repeating explanations.",
    )

    flow = TriggerFlow()

    @flow.chunk
    async def get_input(data: TriggerFlowEventData):
        if data.get_runtime_data("memory") is None:
            data.set_runtime_data("memory", [])
        try:
            user_input = input("Question (type 'exit' to stop): ").strip()
        except EOFError:
            user_input = "exit"
        if user_input.lower() in {"exit", "quit"}:
            data.stop_stream()
            return "exit"
        await data.async_emit("UserInput", user_input)
        return "next"

    @flow.chunk
    async def react_answer(data: TriggerFlowEventData):
        question = str(data.value)
        scratchpad = ""
        max_steps = 4
        memory = data.get_runtime_data("memory") or []
        memory_text = "\n".join(f"- {item}" for item in memory) if memory else "(none)"

        for step in range(1, max_steps + 1):
            prompt = (
                "Return JSON only:\n"
                "{\n"
                '  "thought": "short reasoning",\n'
                '  "action": "search_web|calculator|final",\n'
                '  "action_input": "tool input",\n'
                '  "final": "final answer when action=final (no format examples)"\n'
                "}\n\n"
                f"Question: {question}\n\n"
                "Use key memory and avoid repeating explanations:\n"
                f"{memory_text}\n\n"
                "Prior thoughts and observations:\n"
                f"{scratchpad}"
            )

            data_point = (
                agent.input(prompt)
                .output(
                    {
                        "thought": (str, "short reasoning"),
                        "action": (str, "search_web|calculator|final"),
                        "action_input": (str, "tool input"),
                        "final": (str, "final answer"),
                    }
                )
                .start()
            )

            action = str(data_point.get("action", "final")).strip()
            action_input = str(data_point.get("action_input", "")).strip()
            thought = str(data_point.get("thought", "")).strip()

            if thought:
                data.put_into_stream(f"[thought] {thought}\n")

            if action == "final":
                final_text = str(data_point.get("final", "")).strip()
                data.put_into_stream(f"[final] {final_text}\n")
                memory_update = (
                    agent.input(
                        "Extract up to 3 key memories to keep long-term. "
                        "Do not repeat the full text and do not include reasoning.\n"
                        f"User question: {question}\nFinal answer: {final_text}"
                    )
                    .output({"memory": [(str, "key memory")]})
                    .start()
                )
                new_items = memory_update.get("memory", [])
                data.set_runtime_data(
                    "memory",
                    merge_memory(memory, new_items),
                )
                await data.async_emit("Loop", None)
                return "done"

            if action not in {"search_web", "calculator", "final"}:
                data.put_into_stream("[final] action not allowed\n")
                await data.async_emit("Loop", None)
                return "error"

            if action == "search_web":
                result = await search.search(action_input)
                observation = json.dumps(result, ensure_ascii=False)
            else:
                observation = safe_eval(action_input)
            data.put_into_stream(f"[action] {action}({action_input})\n")
            data.put_into_stream(f"[observation] {observation}\n")
            time.sleep(0.5)

            scratchpad += (
                f"Thought: {thought}\n"
                f"Action: {action}\n"
                f"Action Input: {action_input}\n"
                f"Observation: {observation}\n\n"
            )

        data.put_into_stream("[final] reached max steps\n")
        await data.async_emit("Loop", None)
        return "max_steps"

    flow.to(get_input)
    flow.when("UserInput").to(react_answer)
    flow.when("Loop").to(get_input)

    for event in flow.get_runtime_stream("start", timeout=None):
        print(event, end="", flush=True)


if __name__ == "__main__":
    react_tool_loop()
