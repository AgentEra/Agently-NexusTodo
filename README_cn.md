# NexusTodo（VibeCoding 版）

![NexusTodo 预览](NexusTodoImage.png)

一个通过 VibeCoding 完成的端到端智能任务系统：Go 后端、基于 Agently 的智能服务，以及支持流式输出的 Web 客户端。

English README: [README.md](README.md)

## 背景说明
本项目全程以 VibeCoding 方式完成。Golang 后端由 TRAE 实现，其它部分（智能服务、客户端、文档）由 VSCode + Codex 完成。部分搭建过程在 51CTO 由 Maplemx 主讲的线上直播课程中演示。整体开发与优化约 6 小时，其中直播教学覆盖约 4 小时。

## 项目组成
- **backend**（Go）：任务 API、数据持久化、设备注册。
- **auto_agent**（Python）：ReAct 流程、结构化输出、SSE 流式、任务工具调用。
- **client**（Web）：对话 UI、流式气泡、任务卡片。

## Agently 框架说明
本项目智能模块基于 Agently AI 应用开发框架完成。
- GitHub：[https://github.com/AgentEra/Agently](https://github.com/AgentEra/Agently)
- 官网：[https://Agently.tech](https://Agently.tech)（英文），[https://Agently.cn](https://Agently.cn)（中文）

Agently 在本项目中提供了关键能力：
- 结构化输出约束（`output()` + `ensure_keys`）。
- 无厂商锁定的工具规划。
- 流式输出与 ReAct 风格循环。

## 文档索引
- 项目启动与总览：[PROJECT_OVERVIEW_cn.md](PROJECT_OVERVIEW_cn.md)
- 后端 API 与设计：[backend/docs/api-documentation.md](backend/docs/api-documentation.md), [backend/docs/backend-design.md](backend/docs/backend-design.md)
- 智能服务设计与 API：[auto_agent/docs/dev_design.md](auto_agent/docs/dev_design.md), [auto_agent/docs/api-documentation.md](auto_agent/docs/api-documentation.md)
- 对话与 LLM 运行规范：[auto_agent/docs/spec-dd-llm-chat-ops.md](auto_agent/docs/spec-dd-llm-chat-ops.md)
- 客户端使用：[client/docs/client-documentation.md](client/docs/client-documentation.md)
- 测试报告：[auto_agent/docs/test-report.md](auto_agent/docs/test-report.md), [backend/docs/test-report.md](backend/docs/test-report.md)

## VibeCoding 过程与质量闭环
关于指导、自检、场景测试与优化迭代的完整记录：
- 英文：[docs/vibecoding-process.md](docs/vibecoding-process.md)
- 中文：[docs/vibecoding-process_cn.md](docs/vibecoding-process_cn.md)

## Agently + VibeCoding 经验总结
我们总结了基于 Agently 的 VibeCoding 实践与自举优化流程：
- 用确定性、合同式结构输出减少歧义。
- 以真实接口集成场景作为主要验证门槛。
- 将失败修复沉淀为提示词/解析/文档规则。

## Agently 社区与贡献
- 文档：[https://Agently.tech/docs](https://Agently.tech/docs)
- GitHub：[https://github.com/AgentEra/Agently](https://github.com/AgentEra/Agently)
- 示例（Agently 仓库）：
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/)
  - [https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/](https://github.com/AgentEra/Agently/tree/main/examples/step_by_step/13-auto_loop_fastapi/)
- 讨论区：[https://github.com/AgentEra/Agently/discussions](https://github.com/AgentEra/Agently/discussions)
- 贡献与反馈：[https://github.com/AgentEra/Agently/issues](https://github.com/AgentEra/Agently/issues)

### 加入 Agently 微信讨论群
可通过以下方式找到官方微信群入口：
- 访问 Agently 官网（[https://Agently.tech](https://Agently.tech)），在首页找到 WeChat Group / Join Us 入口。
- 访问 Agently GitHub 主页（[https://github.com/AgentEra/Agently](https://github.com/AgentEra/Agently)），查看 "WeChat Group (Join Us)" 区域。

当前 GitHub README 中的申请表链接：
- [https://doc.weixin.qq.com/forms/AIoA8gcHAFMAScAhgZQABIlW6tV3l7QQf](https://doc.weixin.qq.com/forms/AIoA8gcHAFMAScAhgZQABIlW6tV3l7QQf)
