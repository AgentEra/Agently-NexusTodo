---
name: agently-agents-and-prompts
description: Agent setup, prompt layering, routing, and info injection patterns.
---

# Agently Agents and Prompts Skill

Use this skill for agent configuration, prompt layering, YAML-based prompts, and multi-agent routing.

## Key Patterns
- Keep stable rules in agent prompts; keep dynamic input in request prompts.
- Use YAML prompts for maintainable configurations.
- Route to specialized agents by intent.

## Pitfalls to Avoid (Lessons from NexusTodo)
- Fix action enums and status enums in the system prompt to prevent invalid actions.
- Map common Chinese phrases to structured fields (e.g., "未完成" => `status_list`).
- Rename requests should set `title=NEW` and `query.keyword=OLD` (without "任务" suffix).
- Deletion with keyword should be allowed as bulk without extra clarification.
- For “这些/上述/刚才列出的任务”, return `selection_indices` to select by list order.

## References
- `examples/prompt_layers_and_mappings.py`
- `examples/prompt_config_from_yaml.py`
- `examples/multi_agent_router.py`
- `examples/rag_with_info_prompt.py`
- `examples/single_request_multi_read.py`
- `examples/prompt_template.yaml`

## Examples
See `examples/run.sh` for runnable commands.
