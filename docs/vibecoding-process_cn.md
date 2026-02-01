# VibeCoding 过程与质量闭环

中文版本。English version: [docs/vibecoding-process.md](docs/vibecoding-process.md)。

## 1) 工作流概览
VibeCoding 强调“目标明确 + 合同式约束 + 可执行验证 + 失败驱动优化”的快速闭环。本项目迭代路径为：
1) 明确契约与验收标准。
2) 打通后端/智能服务/前端的最小闭环。
3) 增加结构化输出与流式体验。
4) 用真实接口扩展场景测试。
5) 修复失败模式并同步文档，持续循环。

## 2) 规则先行
将关键规则前置到提示词和文档中：固定动作枚举、严格 JSON 输出、确定性配置、明确状态映射。这些约束减少歧义，使错误更易定位。

## 3) 自检闭环
自检以可复现实测为核心。我们优先使用真实接口的集成场景来验证正确性，避免只看 UI 输出。常见失败被记录，并沉淀为提示词规则、解析约束与执行保护。

## 4) 典型失败与修复
- **list 后过早结束** → 若仅用于定位目标，必须继续 update/delete。
- **改名不明确** → 强制 `title=新标题`，`query.keyword=旧标题`。
- **taskId 非 UUID** → 过滤无效 ID，回退关键词匹配。
- **流式卡片重复** → 仅在 `done` 输出卡片。
- **“这些任务”指代** → 记录最近列表并支持 `selection_indices`。

## 5) Agently + VibeCoding 收益
Agently 让 VibeCoding 更可控：
- 结构化输出保障稳定性；
- 工具规划清晰可追踪；
- 流式与编排更贴近生产体验；
- 需要分支逻辑时可用 TriggerFlow。

## 6) 效果评估与自举优化
效果评估以“真实任务执行正确”为准，而非仅 UI 结果。每次失败都会沉淀为提示词/解析/契约的修复，并补充回归用例，形成自举优化闭环。

## 7) 后续复用建议
- 先定契约与状态枚举；
- 采用确定性 LLM 设置；
- 早期引入真实接口用例；
- 行为变化必须同步文档。

## 8) 进一步阅读（Agently）
如需在新项目中复用该流程，可从 Agently 文档与示例开始：
- 文档：[https://Agently.tech/docs](https://Agently.tech/docs)
- 示例（Agently 仓库）：
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/)
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/)
- 社区：[https://github.com/AgentEra/Agently/discussions](https://github.com/AgentEra/Agently/discussions)
