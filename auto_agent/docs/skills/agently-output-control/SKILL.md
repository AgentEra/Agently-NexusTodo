---
name: agently-output-control
description: Structured output patterns with ensure_keys, ordering, and instant streaming.
---

# Agently Output Control Skill

Use this skill when you need stable structured output, key guarantees, ordered dependencies, or instant streaming.

## Key Patterns
- Define Output Format first, then use `ensure_keys` for critical fields.
- Order fields so dependencies appear earlier.
- Use `get_generator(type="instant")` for structured streaming.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Keep outputs strictly JSON for machine parsing; no extra prose.
- Use `temperature=0` to reduce random schema drift.
- Validate critical fields (e.g., `taskId` must be UUID) before execution.
- If parsing fails, fall back to a safe clarify response rather than guessing.

## References
- `examples/structured_output_with_ensure_keys.py`
- `examples/order_and_dependencies_output.py`
- `examples/streaming_with_instant_mode.py`
- `examples/response_event_streams.py`
- `examples/key_waiter_early_field.py`

## Examples
See `examples/run.sh` for runnable commands.
