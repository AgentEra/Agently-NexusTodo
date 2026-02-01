# 项目总览与启动

本文提供顶层总览与最小化启动指南。详细说明请参考下方各组件文档。

English version: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

## 架构总览
- **backend**（Go）：任务 API、数据持久化、设备注册。
- **auto_agent**（Python）：ReAct 编排、结构化输出、SSE 流式。
- **client**（Web/Electron）：对话 UI、流式气泡、任务卡片。

## 启动（最小化指南）
1) **后端**（默认端口 `8080`）
   - 进入 `backend/` 目录执行：
     ```bash
     go run main.go
     ```

2) **智能服务**（默认端口 `15590`）
   - 在仓库根目录执行：
     ```bash
     python -m uvicorn auto_agent.app:app --host 0.0.0.0 --port 15590
     ```
   - 通过 `TASK_API_BASE_URL` 访问后端（默认 `http://localhost:8080/api`）。

3) **客户端**
   - 进入 `client/` 目录执行：
     ```bash
     npm install
     npm run dev
     ```

## 组件文档
- 后端：[backend/docs/api-documentation.md](backend/docs/api-documentation.md), [backend/docs/backend-design.md](backend/docs/backend-design.md)
- 智能服务：[auto_agent/docs/dev_design.md](auto_agent/docs/dev_design.md), [auto_agent/docs/api-documentation.md](auto_agent/docs/api-documentation.md)
- 对话与 LLM 规范：[auto_agent/docs/spec-dd-llm-chat-ops.md](auto_agent/docs/spec-dd-llm-chat-ops.md)
- 客户端：[client/docs/client-documentation.md](client/docs/client-documentation.md)

## 测试
- Auto Agent：[auto_agent/docs/test-report.md](auto_agent/docs/test-report.md)
- 后端：[backend/docs/test-report.md](backend/docs/test-report.md)
