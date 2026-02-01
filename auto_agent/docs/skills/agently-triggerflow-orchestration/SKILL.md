---
name: agently-triggerflow-orchestration
description: Event-driven TriggerFlow orchestration patterns and branching.
---

# Agently TriggerFlow Orchestration Skill

Use this skill for event-driven orchestration, branching, and runtime_data/collect flows.

## Key Patterns
- Define named chunks, then connect with `to()` / `when()` / `collect()`.
- Use `runtime_data` for per-execution state.
- Use `batch()` or `for_each()` for fan-out work.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Prefer a simple ReAct loop if only sequential tool calls are needed.
- Use TriggerFlow when you truly need branching or event-driven orchestration.

## References
- `examples/standard_trigger_flow_usage.py`
- `examples/triggerflow_emit_when_collect.py`
- `examples/triggerflow_runtime_data_collect.py`
- `examples/plan_execute_basic.py`
- `examples/iterative_refinement_loop.py`

## Examples
See `examples/run.sh` for runnable commands.
