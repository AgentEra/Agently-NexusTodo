# Launch Story: Building NexusTodo with VibeCoding + Agently

> This is the English companion of the WeChat-ready Chinese post: [docs/wechat-article_cn.md](docs/wechat-article_cn.md).

## A tiny demo, a big point

NexusTodo is a small end-to-end sample: a Go task service, a Python agent service built with [Agently](https://github.com/AgentEra/Agently), and a streaming web client.

We built and iterated the full system in ~6 hours. About ~4 hours of the setup and building process was demonstrated live in a 51CTO course hosted by Maplemx. The Golang backend was implemented by TRAE, while the remaining parts (agent service, client, and documentation) were built with VSCode + Codex.

But the “ToDo app” is not the main takeaway. The real takeaway is how to make agentic development *repeatable*:

## The key insight from the live session

**SpecDD matters.** For multi-module systems, the API documentation is not “nice to have” — it is the coordination contract that keeps parallel work aligned.

In practice, we treated:
- **SpecDD** as the top-level “intent + constraints”.
- **API docs** as the inter-module contract (the thing you can actually test against).
- **Integration scenarios** as the gate that decides whether the system is real or just a UI illusion.

## VibeCoding as “multi-team coordination”

During VibeCoding, the human role often shifts from “typing code” to **coordinating a technical team**:
- One session for frontend, one for backend, one for the agent module.
- Each session has its own local tests and workflows.
- As the project reaches end-to-end integration, those “teams” must converge.

One pattern that worked well: **gradual permission opening**. Early on, the agent session is constrained to a specific folder. During integration, you widen the allowed surface so that cross-module bugs can be fixed in one place, without losing earlier discipline.

## Why Agently helped (a lot)

When you embed an LLM-powered module into a real product, the hardest part is not “chat” — it is *reliability under ambiguity*.

Agently helped us turn “prompt magic” into engineering primitives:
- **Schema-first outputs** (`output()` + `ensure_keys`) so responses are stable without relying on brittle parsing.
- **TriggerFlow** for signal-driven orchestration (simple, readable control flow for multi-step tasks).
- **Streaming-first API ergonomics** so UI/UX can show intermediate reasoning tokens and final results cleanly.

We also captured common pitfalls discovered during development as reusable skills:
- [auto_agent/docs/skills/agently-agent-systems/SKILL.md](auto_agent/docs/skills/agently-agent-systems/SKILL.md)
- [auto_agent/docs/skills/agently-agents-and-prompts/SKILL.md](auto_agent/docs/skills/agently-agents-and-prompts/SKILL.md)

## The “hard-write VibeCoding” traps (and how to avoid them)

If you ask a model to “just build everything end-to-end”, it often hits predictable failure modes:
- **“Accept All” scaling problems**: the code grows beyond your comprehension, and small fixes become roulette.  
  Reference: Karpathy’s “vibe coding / accept all” post and related discussions (e.g. Ars Technica’s overview).
- **Quality regression**: more logic bugs, more security issues, longer review tails.  
  Reference: CodeRabbit’s PR analysis and coverage (e.g. The Register).
- **Security overconfidence**: people believe the code is secure even when it isn’t.  
  Reference: Stanford / Dan Boneh’s team on insecure code + overconfidence.
- **Supply chain risks**: hallucinated dependencies can be weaponized (“slopsquatting”).  
  Reference: the “package hallucination” line of research (UTSA coverage; arXiv paper).

Our mitigation strategy was boring — and that’s the point:
- Contract-first docs (SpecDD + API docs).
- Deterministic structured outputs for the agent.
- Real-API scenario tests as the main acceptance criteria.
- Streaming UX that clearly separates “in-progress” vs “final answer”.

## Try it, remix it, ship your own

- Project repo: [https://github.com/AgentEra/Agently-NexusTodo](https://github.com/AgentEra/Agently-NexusTodo)
- Quick start: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- VibeCoding write-up: [docs/vibecoding-process.md](docs/vibecoding-process.md)

## Join the Agently community (WeChat)

You can find the official WeChat group entry in:
- [https://Agently.tech](https://Agently.tech)
- [https://github.com/AgentEra/Agently](https://github.com/AgentEra/Agently)

Application form (as linked from the official docs / README at the time of writing):
- [https://doc.weixin.qq.com/forms/AIoA8gcHAFMAScAhgZQABIlW6tV3l7QQf](https://doc.weixin.qq.com/forms/AIoA8gcHAFMAScAhgZQABIlW6tV3l7QQf)

## Further Reading (Public Sources)

- Karpathy (X): <https://x.com/karpathy/status/1886192184808149383>
- Reddit thread (a typical “how do I vibe code” discussion): <https://www.reddit.com/r/ClaudeAI/comments/1igppfg/i_dont_know_how_to_vibe_code/>
- Ars Technica (vibe coding overview): <https://arstechnica.com/ai/2025/03/is-vibe-coding-with-ai-gnarly-or-reckless-maybe-some-of-both/>
- The Register (AI code issues coverage): <https://www.theregister.com/2025/12/17/ai_code_bugs/>
- CodeRabbit report entry (press release): <https://www.businesswire.com/news/home/20251217666881/en/CodeRabbits-State-of-AI-vs-Human-Code-Generation-Report-Finds-That-AI-Written-Code-Produces-1.7x-More-Issues-Than-Human-Code>
- Stanford EE (Boneh team): <https://ee.stanford.edu/dan-boneh-and-team-find-relying-ai-more-likely-make-your-code-buggier>
- arXiv (package hallucination / slopsquatting): <https://arxiv.org/abs/2406.10279>
