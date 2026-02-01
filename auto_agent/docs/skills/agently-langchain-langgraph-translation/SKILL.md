---
name: agently-langchain-langgraph-translation
description: Translate LangChain/LangGraph patterns into Agently code (model control + TriggerFlow).
---

# LangChain/LangGraph -> Agently Translation Skill

Use this skill to translate LangChain/LangGraph code into Agently patterns for production services.

## Core mapping (high level)
- PromptTemplate -> `agent.set_agent_prompt` / `agent.set_request_prompt` with mappings
- LLMChain -> `agent.input(...).output(...).start()`
- OutputParser -> Output Format + `get_data()` / `ensure_keys`
- Tools -> `@agent.tool_func` + `agent.use_tool(...)`
- Memory -> keep key memory (runtime_data or custom memory); avoid full history
- LangGraph node -> TriggerFlow chunk
- LangGraph edges/conditions -> TriggerFlow `when()/to()/if_condition()/match()`
- Streaming -> `get_generator` / `get_async_generator` or runtime_stream

## Translation steps
1) Identify data contracts (inputs/outputs) and enforce with Output Format.
2) Convert graph nodes into TriggerFlow chunks.
3) Replace edges with when/to/condition/collect.
4) Convert tools to `@agent.tool_func` and call via `use_tool` or ReAct loop.
5) Use runtime_data for per-run state; keep only key memory.

## References
- `references/overview.md`
- `examples/langchain_to_agently_map.py`
- `examples/langgraph_to_agently_triggerflow.py`

## Examples
See `examples/run.sh` for runnable commands.
