---
name: agently-streaming-and-react
description: Streaming outputs, runtime streams, and ReAct-style tool loops.
---

# Agently Streaming and ReAct Skill

Use this skill for streaming outputs, runtime stream UX, and ReAct-style tool loops.

## Key Patterns
- Use `get_generator(type="instant")` for structured streaming.
- Use TriggerFlow runtime_stream for live UI output.
- ReAct loop: thought -> action -> observation -> final.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Do not stop the loop after a `list_tasks` if it is only used to locate targets for update/delete; continue to the write action.
- Stop after successful write or query completion to avoid infinite loops.
- Emit task cards only on final/done; stream only thought/observation during execution.
- Keep action enum strict and JSON-only output to prevent parse drift.
- Set LLM `temperature=0` to stabilize structured output.

## References
- `examples/streaming_with_instant_mode.py`
- `examples/response_event_streams.py`
- `examples/trigger_flow_with_agent.py`
- `examples/react_tool_loop.py`

## Examples
See `examples/run.sh` for runnable commands.
