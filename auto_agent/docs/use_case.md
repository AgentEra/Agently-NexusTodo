# Use Case 文档：NexusTodo Auto Agent

## 1. 参与者
- 用户：通过自然语言发起任务操作
- 客户端（NexusTodo UI）：展示对话、维护 sessionId、调用 Auto Agent
- Auto Agent 服务：解析意图、调用任务 API、返回对话结果
- 任务后端 API：提供任务 CRUD 与鉴权

## 2. 用例列表（摘要）
| 用例编号 | 用例名称 | 目标 | 关键接口 |
| --- | --- | --- | --- |
| UC-01 | 创建任务（对话） | 通过自然语言创建任务 | POST /agent/chat |
| UC-02 | 查询任务列表（对话） | 获取任务列表并展示 | POST /agent/chat |
| UC-03 | 查询任务详情（对话） | 获取指定任务详情 | POST /agent/chat |
| UC-04 | 更新任务（对话） | 修改任务属性 | POST /agent/chat |
| UC-05 | 删除任务（对话） | 删除指定任务 | POST /agent/chat |
| UC-06 | 信息补全与澄清 | 参数不足时引导用户补充 | POST /agent/chat |
| UC-07 | 流式对话（SSE） | 实时增量展示 assistant 回复 | GET /agent/chat/stream |
| UC-08 | 错误与鉴权处理 | 统一错误返回与鉴权失败提示 | POST /agent/chat / GET /agent/chat/stream |

## 3. 用例详情

### UC-01 创建任务（对话）
- **目标**：用户用自然语言创建任务（标题必填，可含描述、标签、状态）。
- **参与者**：用户、客户端、Auto Agent、任务后端 API。
- **前置条件**：客户端持有 `userId`、`deviceId`；请求头包含鉴权信息。
- **触发**：用户输入“帮我创建一个任务：周一提交周报，标签 work”。
- **主成功流程**：
  1. 客户端将用户消息发送至 `POST /agent/chat`。
  2. Auto Agent 解析意图为 `create` 并组织参数。
  3. Auto Agent 调用 `POST /api/tasks` 创建任务。
  4. Auto Agent 返回 `assistantMessage`、`action` 与 `execution`。
  5. 客户端展示结果并触发任务列表刷新。
- **后置条件**：任务创建成功；任务列表同步刷新。
- **备选/异常流程**：
  - 标题缺失 → 进入 UC-06。
  - 后端返回鉴权失败/参数不合法 → 进入 UC-08。

### UC-02 查询任务列表（对话）
- **目标**：按状态/标签/关键字查询任务列表。
- **前置条件**：鉴权信息有效。
- **触发**：用户输入“帮我列出已完成的 work 标签任务”。
- **主成功流程**：
  1. 客户端发送 `POST /agent/chat`。
  2. Auto Agent 解析 `list`，必要时整理 `query`。
  3. Auto Agent 调用 `GET /api/tasks?status=已完成&tags=work`。
  4. 返回列表摘要与结果对象。
  5. 客户端展示任务列表或摘要。
- **备选/异常流程**：
  - 关键字查询后端不支持 → Auto Agent 先拉取列表再本地过滤。
  - 无匹配结果 → 返回“未找到”提示。

### UC-03 查询任务详情（对话）
- **目标**：获取指定任务详情。
- **触发**：用户输入“查看任务 123 的详情”。
- **主成功流程**：
  1. Auto Agent 解析 `detail` 与 `taskId`。
  2. 调用 `GET /api/tasks/:taskId`。
  3. 返回详情信息。
- **备选/异常流程**：
  - 任务不存在 → UC-08（TASK_NOT_FOUND）。
  - 任务 ID 缺失 → UC-06。

### UC-04 更新任务（对话）
- **目标**：更新任务标题、描述、状态或标签。
- **触发**：用户输入“把任务 123 标记为已完成”。
- **主成功流程**：
  1. Auto Agent 解析 `update` 与字段。
  2. 调用 `PUT /api/tasks/:taskId`。
  3. 返回更新结果。
  4. 客户端刷新任务列表。
- **备选/异常流程**：
  - 目标不唯一 → 返回候选并澄清（UC-06）。
  - 状态非法 → UC-08（INVALID_STATUS）。

### UC-05 删除任务（对话）
- **目标**：删除指定任务。
- **触发**：用户输入“删除任务 123”。
- **主成功流程**：
  1. Auto Agent 解析 `delete` 与 `taskId`。
  2. 调用 `DELETE /api/tasks/:taskId`。
  3. 返回删除结果。
  4. 客户端刷新任务列表。
- **备选/异常流程**：
  - 目标不唯一 → 返回候选并澄清（UC-06）。

### UC-06 信息补全与澄清
- **目标**：当意图不明确或参数不足时，引导用户补充信息。
- **触发**：用户输入“帮我创建任务”但未提供标题。
- **主成功流程**：
  1. Auto Agent 通过 ReAct 规划判断信息不足。
  2. 返回追问文本（`assistantMessage`）并将 `execution.status` 置为 `skipped`。
  3. 客户端展示追问并等待用户补充。
- **后置条件**：后续消息补全信息后回到 UC-01~UC-05。

### UC-07 流式对话（SSE）
- **目标**：实时展示 assistant 回复与结构化事件。
- **触发**：客户端以 GET 方式调用 `/agent/chat/stream`。
- **主成功流程**：
  1. 客户端带 query 参数请求 SSE。
  2. Auto Agent 按 `delta` 事件流式返回文本片段。
  3. 需要时发送 `action` / `execution` 事件。
  4. 发送 `done` 事件结束。
- **备选/异常流程**：
  - 发生错误 → 发送 `error` 事件并关闭连接。

### UC-08 错误与鉴权处理
- **目标**：统一返回鉴权失败、参数错误、上游异常等错误信息。
- **触发**：缺失鉴权头、参数不合法或后端失败。
- **主成功流程**：
  1. Auto Agent 返回 HTTP 400/401/403/502/500。
  2. SSE 场景返回 `error` 事件。
  3. 客户端展示可读错误信息。
- **后置条件**：不执行写操作或回滚已触发的动作。

## 4. 业务规则与约束
- 任务状态枚举固定为：`待办` / `进行中` / `已完成` / `已延期` / `已取消`。
- 信息不足时禁止写操作，并将 `execution.status` 置为 `skipped`。
- 任务 API 响应需兼容 `{data: ...}` 与直接 payload。
- 任务列表按创建时间升序且顺序稳定。

## 5. 关键数据结构
- 对话请求：`sessionId`（可选）、`userId`、`deviceId`、`messages`。
- 对话响应：`assistantMessage`、`action`、`execution`。
- SSE 事件类型：`delta`、`action`、`execution`、`done`、`error`。
