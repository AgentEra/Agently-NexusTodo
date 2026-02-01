---
name: agently-agent-systems
description: Build complex agent and intelligent system services with Agently (Model control + TriggerFlow).
---

# Agently Agent Systems Skill

Use this skill when building production-like agent systems and service modules with Agently: model control, streaming, orchestration, and API delivery.

## What this skill covers
- Model control for stable outputs (Output Format, ensure_keys, ordering).
- TriggerFlow orchestration for multi-step and event-driven logic.
- Streaming UX and ReAct-style loops.
- Service modules (FastAPI: POST, SSE, WebSocket).

## Design checklist
1) Define contracts: output schema and critical keys.
2) Choose streaming mode: one-shot, SSE, or WebSocket.
3) Orchestrate steps with TriggerFlow (when/to/collect).
4) Preserve only key memory; avoid full history.
5) Validate with runnable examples.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Use deterministic LLM settings (e.g., `temperature=0`) for structured outputs.
- Avoid stopping after `list` when a write operation is still required.
- Normalize keyword matching (strip "任务/事项/事情") before filtering.
- Record integration scenarios and run against real APIs to prevent UI-only validation.

## References
- `examples/fastapi_triggerflow_service.py`
- `examples/react_tool_loop.py`
- `examples/plan_execute_basic.py`
- `examples/triggerflow_emit_when_collect.py`
- `examples/triggerflow_runtime_data_collect.py`
- `examples/structured_output_with_ensure_keys.py`
- `examples/order_and_dependencies_output.py`
- `examples/multi_agent_router.py`
- `examples/rag_with_info_prompt.py`

## Example modules you can build
- Agent gateway: route requests to specialist agents by intent.
- Tool-powered analyst: ReAct loop with search + calculator.
- Orchestrated plan-execute: TriggerFlow pipeline with runtime_data.
- API service: FastAPI endpoints for POST + SSE + WebSocket.

## Examples
See `examples/run.sh` for runnable commands.
