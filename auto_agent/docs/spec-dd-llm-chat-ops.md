# Spec-DD：NexusTodo 对话式任务操作

## 背景/目标
- 在 NexusTodo 中新增“对话式任务操作”能力：用户通过自然语言输入完成任务增删改查，并获得对应的操作结果呈现。
- 入口位于左侧边栏，点击后进入多轮对话界面。
- 实现位置：`/auto_agent` 目录。

## 用户与场景
- 目标用户：NexusTodo 现有用户。
- 使用场景：用户在左侧边栏选择“对话”入口，通过多轮对话完成任务管理。
- 典型场景：用户无需操作 UI 表单/卡片，直接用对话创建、更新、删除或查询任务。

## 功能清单
1. 对话入口
   - 左侧边栏新增入口（命名待定，例如“AI 对话/智能助手”）。
   - 点击后进入对话界面。
2. 多轮对话
   - 支持持续对话上下文，用于补充缺失信息（如缺少任务标题或目标任务不明确）。
3. 自然语言解析
   - 使用本地 Ollama 模型 `qwen2.5:7b` 解析用户意图与参数。
   - 将解析结果映射为任务 CRUD 操作。
4. 任务操作
   - 创建任务：标题必填，可选描述、标签。
   - 查询任务：支持全量列表、按状态/标签/关键词过滤；可查询单条任务详情。
   - 更新任务：更新标题、描述、状态、标签。
   - 删除任务：删除单条任务。
5. 结果呈现
   - 对话区展示操作结果摘要（如创建成功、更新成功、查询列表）。
   - 操作完成后触发任务列表刷新（复用现有全量同步逻辑）。

## 用户流程
1. 用户点击左侧边栏“对话”入口进入聊天界面。
2. 用户输入自然语言指令（如“帮我创建一个任务：周一提交周报，标签 work”）。
3. 系统调用 LLM 进行 ReAct 规划（思考->行动->观察）。
4. 若参数不完整或存在歧义，系统在对话中追问补充信息。
5. 解析完整后执行对应 API 操作。
6. 对话区返回操作结果，并刷新任务列表。

## 数据结构
### 1) ReAct 规划输出（建议）
用于稳定解析与执行，输出需满足固定 JSON 结构（参考 `agently-output-control` 的 ensure_keys 方案）。
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

### 2) 对话会话结构（建议）
```json
{
  "sessionId": "uuid",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## 接口草案
### A. Auto Agent 服务（Python 3.10+，位于 `/auto_agent`）
> 使用 `agently-agent-systems` / `agently-fastapi-service` / `agently-streaming-and-react` 的示例与模式。

1) 解析与执行（单次请求）
- `POST /agent/chat`
- 请求体：
```json
{
  "sessionId": "uuid?",
  "userId": "uuid",
  "deviceId": "uuid",
  "messages": [{"role": "user", "content": "..."}]
}
```
- 响应体：
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

2) （可选）流式对话
- `GET /agent/chat/stream`（SSE）或 `WS /agent/chat/ws`
- 用于逐步返回模型输出与执行状态。

### B. 任务管理 API（复用现有后端）
- `GET /api/tasks`（列表/过滤）
- `GET /api/tasks/:taskId`（详情）
- `POST /api/tasks`（创建）
- `PUT /api/tasks/:taskId`（更新）
- `DELETE /api/tasks/:taskId`（删除）

## 边界与异常
- 目标不明确且缺少筛选条件时，返回追问；若提供关键词/筛选条件，可直接执行批量写操作（删除含关键词默认批量）。
- 更新目标不唯一时提示用户选择或补充信息。
- 后端返回错误（认证失败、任务不存在、无效状态等）时，需在对话中提示原因。
- ReAct 规划输出无法解析时，回退到澄清提问。
- “未完成/未结束/未办完”需映射为多状态筛选（`status_list`）。
- 改名请求：`action_input.title` 为新标题，`action_input.query.keyword` 为旧标题（不含“任务”等后缀），`taskId` 必须为 UUID。
- 关键词匹配忽略常见后缀（任务/事项/事情）。
- 当用户说“这些/上述/刚才列出的任务”，使用 `selection_indices` 选择序号列表。

## 非功能需求
- 未指定额外非功能要求（性能、稳定性、成本、审计等无额外约束）。

## 验收标准
1. 用户可通过对话完成任务的创建、查询、更新、删除。
2. 对话支持多轮补充信息（如缺少标题、目标任务不明确）。
3. 操作成功后，对话区展示结果并触发任务列表刷新。
4. 任务状态支持既有枚举值（待办/进行中/已完成/已延期/已取消）。
5. 使用本地 Ollama 模型 `qwen2.5:7b` 完成解析。
6. 开发遵循 `/auto_agent/docs/skills` 里的技能指引。

## 风险与假设
- 风险：模型误判意图可能导致错误操作（需通过澄清与 ReAct 规划降低风险）。
- 风险：自然语言与状态枚举映射不一致，需要在提示词中固化映射规则。
- 假设：客户端可新增侧边栏入口并集成对话 UI。
- 假设：现有后端 API（任务管理与认证头）可直接复用。
- 假设：未指定交付时间（无里程碑约束）。
