# 技术方案设计文档：NexusTodo 对话式任务操作

## 1. 目标与范围
- 目标：在 NexusTodo 中新增“对话式任务操作”，用户通过自然语言完成任务的创建/查询/更新/删除，并获得可读结果；同时提供流式对话能力用于更好的交互体验。
- 范围：前端新增侧边栏入口与对话界面；Auto Agent 服务负责解析意图并调用现有任务 API，提供 POST 与流式（SSE）能力；后端任务 API 复用。

## 2. 总体方案概览
### 2.1 架构概览
- 前端：新增侧边栏入口 + 对话 UI；负责会话展示、输入与调用 `/agent/chat`；接收结果后刷新任务列表。
- Auto Agent（/auto_agent）：FastAPI 服务 + Agently + Ollama（qwen2.5:7b），使用 ReAct 规划多步动作并调用任务 API。
- 后端：现有任务管理 API（CRUD）保持不变。

### 2.2 关键设计原则（遵循 /auto_agent/docs/skills）
- 结构化输出：使用 Agently output control 的 `ensure_keys` 固化 ReAct 规划字段，确保稳定解析。
- 服务暴露：使用 Agently FastAPI service 作为 POST/SSE/WS 的对话服务封装。
- 流式与 ReAct：流式输出思考/观察过程与工具执行结果，便于前端增量展示。
- Orchestration：复杂流程可用 TriggerFlow 编排（意图解析 -> 校验 -> API 调用 -> 汇总响应）。

## 3. 功能设计
### 3.1 前端（client）
- 入口：左侧边栏新增“对话/AI 对话/智能助手”入口，点击进入对话页面。
- 对话界面：
  - 消息区展示 user/assistant 消息。
  - 输入区发送自然语言指令。
  - 当 assistant 返回结果时，展示摘要和必要详情。
- 会话管理：
  - 前端持有 sessionId（首次为空，由服务端生成返回）。
  - 每次请求携带本轮用户消息与必要历史（或仅本轮消息 + sessionId）。
- 流式输出与终止：
  - 对话默认使用 SSE 流式输出思考/观察过程，结论阶段输出任务卡片。
  - 发送按钮在执行中可切换为“终止任务”，并进行二次确认。
- 刷新任务列表：
  - 操作成功后触发现有任务列表的全量同步/刷新逻辑。
- Electron/IPC 调用约束（基于 client 实现）：
  - `app.js` 中统一使用 `requestApi`；当存在 `window.nexusTodoBridge.request` 时通过 IPC 进行网络请求（避免 CORS）。
  - 对话请求应沿用该调用路径（即走 `requestApi -> ipcRenderer -> ipcMain`）。
- 本地存储与身份复用（基于 client 约定）：
  - 现有键：`nt_base_url`、`nt_device_id`、`nt_user_id`、`nt_tasks_cache`、`nt_last_sync`。
  - 对话功能应复用 `nt_device_id` / `nt_user_id`，并在写操作后调用 `syncTasks` 更新 `nt_tasks_cache` 与 `nt_last_sync`。
- UI 嵌入方式（基于现有结构）：
  - 当前界面为“侧边栏 + 主内容”，主内容包含列表头、筛选工具条、任务列表与编辑入口。
  - 方案建议：新增“视图模式”状态，切换为“对话模式”后隐藏任务列表与筛选工具条，替换为对话面板；返回“任务模式”时恢复原视图。
  - 对话面板可复用 `main` 区域，不改动整体布局栅格。
- Agent 服务地址：
  - 现有 `nt_base_url` 默认值为 `http://localhost:8080/api`（包含 `/api`）。
  - 若 Agent 服务不在同一 host/路径，需新增 `nt_agent_base_url`（或在设置中增加 Agent Base URL）。
  - 若同一 host，建议派生：`agentBaseUrl = nt_base_url.replace(/\\/api$/, \"\") + \"/agent\"`。

### 3.2 Auto Agent（/auto_agent）
- 核心模块：
  - API 层：`POST /agent/chat` 解析与执行，必要时补充 `GET /agent/chat/stream` 或 `WS /agent/chat/ws`。
  - LLM 解析层：调用 Ollama `qwen2.5:7b`，输出结构化 JSON。
  - Orchestrator：使用 ReAct（思考->行动->观察）驱动多步任务并调用任务 API。
  - Task API Adapter：封装对后端 `/api/tasks` 的调用（携带鉴权头）。
- 运行配置：
  - `TASK_API_TIMEOUT`：任务 API 调用超时（秒），默认 `60`。
  - `REACT_MAX_STEPS`：ReAct 最大执行步数，默认 `10`。
  - LLM 解析请求固定 `temperature=0`，降低随机性以稳定结构化输出。
- 解析与执行策略：
  - 当目标不明确且缺少筛选条件时，返回追问；若提供关键词/筛选条件（如“包含X”），允许直接执行批量写操作。
  - 当意图为 `list/detail` 时，缺参可默认拉取列表后筛选或请求补充。
  - 当意图为 `update/delete` 且目标不唯一时，`update` 需返回候选列表；`delete` 对关键词筛选默认批量删除。
- ReAct 执行约束：
  - 允许最多 `REACT_MAX_STEPS` 步（默认 10）。
  - 查询/筛选完成后自动收敛为结论。
  - 写操作（create/update/delete/get）成功后自动收敛为结论。
- 查询规则：
  - “未完成/未结束/未办完”需映射为 `status_list=["待办","进行中","已延期"]`。
  - 关键词匹配会忽略常见后缀（如“任务/事项/事情”）。
  - 改名请求：`action_input.title` 为新标题，`action_input.query.keyword` 为旧标题（不含“任务”等后缀）。
  - `taskId` 必须为 UUID，否则忽略并回退到关键词筛选。
  - 支持基于最近列表的序号选择：`selection_indices=[1,2]`。

### 3.3 后端 API 依赖与映射（基于 backend/docs/api-documentation.md）
**基础信息**
- Base URL：`http://localhost:8080/api`
- 认证头（除设备注册接口外均需要）：
  - `Authorization: Bearer default-token`
  - `X-User-ID: {用户ID}`
  - `X-Device-ID: {设备ID}`

**设备注册（用于获取/确认 userId + deviceId）**
- `POST /api/device/register`（无需认证）
- 请求：`{ "deviceId": "uuid" }`
- 响应：`{ "deviceId": "...", "userId": "...", "message": "注册成功" }`

**任务 API 映射**
- `create` -> `POST /api/tasks`
  - 必填：title；可选：description、tags、status（默认后端返回为“待办”）。
- `list` -> `GET /api/tasks`
  - 支持 query：`status`、`tags`（多个标签用逗号分隔）。
  - 关键字查询：API 文档未提供；如需支持，可在 Agent 端先拉取列表后做本地过滤（title/description 包含）。
- `detail` -> `GET /api/tasks/:taskId`
- `update` -> `PUT /api/tasks/:taskId`
  - 可更新：title、description、status、tags。
- `delete` -> `DELETE /api/tasks/:taskId`

**响应形态与排序约束**
- API 文档的任务接口示例返回为数组/对象（非统一 `data` 包装），但通用规范中存在统一响应格式说明。
- Task API Adapter 需要兼容两类返回：`{data: ...}` 与直接 payload。
- 任务列表按创建时间升序排序且保持稳定顺序（更新或新增不改变已有任务顺序）。

### 3.4 任务状态映射
- 统一枚举：`待办` / `进行中` / `已完成` / `已延期` / `已取消`。
- 提示词中固定映射规则（中文同义词/英文状态需要映射到上述枚举）。

## 4. 数据结构与接口协议
### 4.1 ReAct 规划输出（内部对齐）
```json
{
  "thought": "string",
  "action": "list_tasks|get_task|create_task|update_task|delete_task|final",
  "action_input": {
    "taskId": "uuid?",
    "taskIds": ["uuid"],
    "title": "string?",
    "description": "string?",
    "status": "待办|进行中|已完成|已延期|已取消?",
    "tags": ["string"],
    "bulk": true,
    "selection_index": 1,
    "selection_indices": [1,2],
    "query": {
      "status": "string?",
      "status_list": ["string"],
      "tags": ["string"],
      "keyword": "string?"
    }
  },
  "final": "string"
}
```
- 通过 `ensure_keys` 强制存在：`thought`、`action`、`action_input`、`final`。
- 当 `action=final` 时输出 `final` 文本。

### 4.2 对话请求/响应
- `POST /agent/chat`
  - 请求：
```json
{
  "sessionId": "uuid?",
  "userId": "uuid",
  "deviceId": "uuid",
  "messages": [{"role": "user", "content": "..."}]
}
```
  - 响应：
```json
{
  "sessionId": "uuid",
  "assistantMessage": "string",
  "action": {
    "intent": "create|list|detail|update|delete|clarify",
    "params": {}
  },
  "execution": {
    "status": "success|failed|skipped",
    "result": {}
  }
}
```

### 4.3 会话结构（建议）
```json
{
  "sessionId": "uuid",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```
- 服务端可选择保留关键上下文（最近 N 轮/关键信息摘要）。

## 5. 交互流程
1. 前端发送自然语言到 `/agent/chat` 或 `/agent/chat/stream`。
2. Auto Agent 使用 ReAct（思考->行动->观察）驱动多步任务。
3. 若信息不足：返回追问消息，不执行写操作。
4. 通过工具调用任务 API，直到收敛结论。
5. 组装 `assistantMessage` 与 `execution.result` 返回前端。
6. 前端刷新任务列表（复用已有全量同步）。

## 6. 异常与边界处理
- 意图不清晰/缺少关键参数：返回澄清问题。
- 查询/更新/删除目标不唯一：列出候选并追问。
- 后端错误（认证失败/无权访问/任务不存在/无效状态）：返回可读错误，并透传错误码（如 `UNAUTHORIZED`、`FORBIDDEN`、`TASK_NOT_FOUND`、`INVALID_STATUS`）。
- ReAct 规划输出解析失败：回退到澄清提问并提示用户重述。

## 7. 安全与鉴权
- Auto Agent 透传现有鉴权头调用后端任务 API：`Authorization` + `X-User-ID` + `X-Device-ID`。
- 设备首次接入时由客户端调用 `/api/device/register` 获取/确认 `userId` 与 `deviceId`。
- 不在 LLM 中存储敏感信息；仅传递必要业务字段。

## 8. 流式对话（明确实现目标）
- 提供流式接口：`GET /agent/chat/stream`（SSE）。
- SSE 按 ReAct 流程输出：`delta` 为思考/观察文本，`action`/`execution` 为工具调用与执行结果。

## 9. 验收与测试要点
- 创建/查询/更新/删除全流程可用。
- 对话可补充缺失信息并完成任务。
- 任务状态严格映射到既有枚举值。
- 操作成功后触发任务列表刷新。
- ReAct 规划输出稳定且解析成功率高。
- 流式对话接口可用，前端可实时接收并展示增量输出。

## 10. 风险与假设
- 风险：模型误判导致错误操作，需依赖澄清与 ReAct 规划降低风险。
- 风险：自然语言状态映射不一致，需提示词固化映射规则。
- 假设：前端可以新增对话入口与 UI；后端 API 可直接复用。
