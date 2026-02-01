# VibeCoding Process & Quality Loop

English version. Chinese version: [docs/vibecoding-process_cn.md](docs/vibecoding-process_cn.md).

## 1) Workflow Overview
VibeCoding emphasizes rapid, human-in-the-loop iteration: set clear goals, codify contracts, validate with executable scenarios, then refine by failure analysis. The project followed a multi-step loop:
1) Define contracts and success criteria.
2) Implement a minimal vertical slice (backend + agent + client).
3) Add structured outputs and streaming.
4) Expand scenario tests with real APIs.
5) Fix failure modes, update docs, and repeat.

## 2) Guidance-First Development
We front-loaded “rules of the road” into prompts and docs: fixed action enums, strict JSON outputs, deterministic settings, and explicit status mappings. This reduced ambiguity and made errors actionable.

## 3) Self-Check Loop
The self-check loop is centered on reproducible tests. We used real API integration scenarios to validate correctness beyond UI output. Common failures were logged, then translated into prompt rules, parsing constraints, and execution guards.

## 4) Typical Failure Modes and Fixes
Key problems and the fixes applied:
- **Stop too early after list** → continue to update/delete if list was only for locating targets.
- **Rename ambiguity** → enforce `title=NEW` and `query.keyword=OLD`.
- **Non-UUID taskId** → validate and fallback to keyword matching.
- **Duplicate cards during streaming** → cards only on `done`.
- **“These tasks” references** → store recent list and allow `selection_indices`.

## 5) Agently + VibeCoding Benefits
Agently enables a disciplined VibeCoding flow:
- Contract-first outputs (`output()` + `ensure_keys`) keep behavior stable.
- Tool planning is explicit and traceable.
- Streaming and orchestration align with production UX.
- TriggerFlow is available when branching logic is required.

## 6) Evaluation & Self-Bootstrapping
We measure success by “real tasks executed correctly” rather than UI-only outcomes. Integration scenarios are treated as guardrails; when a scenario fails, we update prompts, parsers, or contracts, then add regression tests. This is the self-bootstrapping loop that keeps the system improving.

## 7) Reuse for Future Projects
To reuse this workflow in new projects:
- Start with contracts and status enums.
- Use deterministic LLM settings.
- Build integration scenarios early.
- Keep docs synced with behavior changes.

## 8) Further Reading (Agently)
If you want to replicate this workflow on new projects, start from Agently’s docs and examples:
- Docs: [https://Agently.tech/docs](https://Agently.tech/docs)
- Examples (Agently repo):
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/)
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/)
- Community: [https://github.com/AgentEra/Agently/discussions](https://github.com/AgentEra/Agently/discussions)
