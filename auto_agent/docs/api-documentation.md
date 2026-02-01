# Auto Agent API 文档（对话式任务操作）

本文档基于 `auto_agent/docs/dev_design.md`，作为后续开发与对接的标准规范。

## 概述
- 服务目标：提供对话式任务操作能力（意图解析 + 任务 API 调用）。
- 传输协议：HTTP / SSE
- 数据格式：JSON（UTF-8）
- Base URL：`http://localhost:8080`（示例，实际以部署为准）

## 认证与鉴权
Auto Agent 透传后端鉴权头调用任务 API，请求中需携带：
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

## 运行配置
- `TASK_API_TIMEOUT`：任务 API 调用超时（秒），默认 `60`。
- `REACT_MAX_STEPS`：ReAct 最大执行步数，默认 `10`。
- LLM 请求固定 `temperature=0`，以稳定结构化输出。

## 通用数据结构

### 1) 对话消息
```json
{
  "role": "user|assistant",
  "content": "string"
}
```

### 2) ReAct 规划输出（内部对齐）
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

## 接口列表

### 1. 单次对话解析与执行
**POST** `/agent/chat`

**请求头**
```
Content-Type: application/json
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**请求体**
```json
{
  "sessionId": "uuid?",
  "userId": "uuid",
  "deviceId": "uuid",
  "messages": [
    {"role": "user", "content": "..."}
  ]
}
```

**响应体**
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

**说明**
- 当信息不足时，可能返回 `execution.status=skipped` 并在 `assistantMessage` 中给出追问。
- `execution.result` 为调用后端任务 API 的结果或错误摘要。
- `assistantMessage` 可能包含 ReAct 思考/观察过程与最终结论（多行文本）。
- 若需要表达多状态筛选（如“未完成”），可使用 `action_input.query.status_list`。
- 若用户引用“这些/上述/刚才列出的任务”，可使用 `selection_indices` 指定序号列表。

**请求示例**
```bash
curl -X POST http://localhost:8080/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我创建一个任务：周一提交周报，标签 work"}
    ]
  }'
```

**响应示例**
```json
{
  "sessionId": "7a1b0f7c-3a6b-4cbb-9d84-8b6e9f0c8f5a",
  "assistantMessage": "已创建任务：周一提交周报（标签：work）。",
  "action": {
    "intent": "create",
    "params": {
      "title": "周一提交周报",
      "tags": ["work"]
    }
  },
  "execution": {
    "status": "success",
    "result": {
      "taskId": "333e4444-e89b-12d3-a456-426614174000",
      "status": "待办"
    }
  }
}
```

---

### 2. 流式对话（SSE）
**GET** `/agent/chat/stream`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
Accept: text/event-stream
```

**查询参数**
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `sessionId` | string | 否 | 会话 ID（首次可为空） |
| `userId` | string | 是 | 用户 ID |
| `deviceId` | string | 是 | 设备 ID |
| `message` | string | 是 | 本轮用户输入 |

> 说明：为保持 GET 语义，SSE 使用 query 传参；如需传递多轮历史，建议由服务端基于 `sessionId` 做上下文管理。

**返回格式**
- `Content-Type: text/event-stream`
- 事件格式：
```
event: {eventType}
data: {json}

```

**事件类型**
- `delta`: assistant 增量文本片段（含思考/观察）
- `action`: ReAct 步骤动作（包含 `step`/`action`/`intent`/`input`）
- `execution`: 任务 API 执行结果
- `done`: 本次对话完成
- `error`: 错误信息（发生错误时终止流）

**事件示例**
```
event: delta
data: {"sessionId":"...","content":"已创建任务："}

event: delta
data: {"sessionId":"...","content":"周一提交周报（标签：work）。"}

event: action
data: {"step":1,"action":"create_task","intent":"create","input":{"title":"周一提交周报","tags":["work"]}}

event: execution
data: {"status":"success","result":{"taskId":"...","status":"待办"}}

event: done
data: {"sessionId":"...","assistantMessage":"已创建任务：周一提交周报（标签：work）。"}
```

---

## 错误处理

### HTTP 状态码
- `400 Bad Request`: 参数缺失或格式不合法
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 无权限
- `502 Bad Gateway`: 上游任务 API 或 LLM 服务异常
- `500 Internal Server Error`: 服务内部错误

### SSE 错误事件
```
event: error
data: {"code":"ERROR_CODE","message":"错误描述"}
```

## 任务状态枚举
`待办` / `进行中` / `已完成` / `已延期` / `已取消`

## 兼容性说明
- Auto Agent 调用后端任务 API 时需要兼容两类响应：`{data: ...}` 与直接 payload。
- 任务列表排序遵循后端规则：按创建时间升序且稳定不乱序。
