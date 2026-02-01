# NexusTodo API 文档

## 目录

- [概述](#概述)
- [认证机制](#认证机制)
- [通用规范](#通用规范)
- [设备管理 API](#设备管理-api)
- [任务管理 API](#任务管理-api)
- [错误码说明](#错误码说明)
- [数据模型](#数据模型)

---

## 概述

NexusTodo 后端提供 RESTful API 接口，支持设备注册、任务管理、数据同步等核心功能。API 基于 HTTP 协议，使用 JSON 格式进行数据交换。

**基础信息**
- **Base URL**: `http://localhost:8080/api`
- **协议**: HTTP (生产环境应使用 HTTPS)
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 认证机制

### 默认 Token 认证

所有 API 请求（除设备注册接口外）都需要在请求头中携带认证信息：

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**参数说明**
- `Authorization`: 固定值 `Bearer default-token`
- `X-User-ID`: 用户 ID（UUID 格式）
- `X-Device-ID`: 设备 ID（UUID 格式）

**注意**: 设备注册接口 (`/api/device/register`) 不需要认证。

---

## 通用规范

### HTTP 方法

| 方法 | 描述 |
| :--- | :--- |
| `GET` | 获取资源 |
| `POST` | 创建资源 |
| `PUT` | 更新资源（完整更新） |
| `DELETE` | 删除资源 |

### HTTP 状态码

| 状态码 | 描述 |
| :--- | :--- |
| `200 OK` | 请求成功 |
| `201 Created` | 资源创建成功 |
| `400 Bad Request` | 请求参数错误 |
| `401 Unauthorized` | 未授权/认证失败 |
| `403 Forbidden` | 无权限访问 |
| `404 Not Found` | 资源不存在 |
| `500 Internal Server Error` | 服务器内部错误 |

### 通用响应格式

**成功响应**
```json
{
  "data": {},
  "message": "操作成功"
}
```

**错误响应**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

---

## 设备管理 API

### 1. 设备注册

注册新设备或更新已注册设备的活跃状态。

**接口信息**
- **路径**: `/api/device/register`
- **方法**: `POST`
- **认证**: 不需要
- **Content-Type**: `application/json`

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `deviceId` | string | 是 | 设备唯一标识符（UUID 格式） |

**请求示例**
```bash
curl -X POST http://localhost:8080/api/device/register \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**响应示例**

成功响应 (200 OK):
```json
{
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "message": "注册成功"
}
```

错误响应 (400 Bad Request):
```json
{
  "error": {
    "code": "INVALID_DEVICE_ID",
    "message": "设备ID格式错误"
  }
}
```

**业务逻辑**
1. 验证 `deviceId` 格式（UUID）
2. 检查设备是否已注册
3. 若未注册，创建新设备记录并绑定默认用户
4. 若已注册，更新设备最后活跃时间
5. 返回设备ID和用户ID

---

### 2. 设备状态检查

检查设备的注册状态和关联信息。

**接口信息**
- **路径**: `/api/device/status`
- **方法**: `GET`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-Device-ID: {设备ID}
X-User-ID: {用户ID}
```

**请求示例**
```bash
curl -X GET http://localhost:8080/api/device/status \
  -H "Authorization: Bearer default-token" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000"
```

**响应示例**

成功响应 (200 OK):
```json
{
  "deviceId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "lastSeenAt": "2023-06-01T13:00:00Z"
}
```

错误响应 (401 Unauthorized):
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "认证失败"
  }
}
```

错误响应 (404 Not Found):
```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "设备不存在"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 检查设备是否存在
3. 更新设备最后活跃时间
4. 返回设备状态信息

---

## 任务管理 API

### 1. 获取任务列表

获取用户的任务列表，支持按状态和标签过滤。

**接口信息**
- **路径**: `/api/tasks`
- **方法**: `GET`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**查询参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `status` | string | 否 | 任务状态过滤（待办/进行中/已完成/已延期/已取消） |
| `tags` | string | 否 | 标签过滤（多个标签用逗号分隔） |

**请求示例**

获取所有任务:
```bash
curl -X GET http://localhost:8080/api/tasks \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

按状态过滤:
```bash
curl -X GET "http://localhost:8080/api/tasks?status=待办" \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

按标签过滤:
```bash
curl -X GET "http://localhost:8080/api/tasks?tags=work,urgent" \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**

成功响应 (200 OK):
```json
[
  {
    "taskId": "111e2222-e89b-12d3-a456-426614174000",
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "title": "完成项目报告",
    "description": "撰写本周项目进展报告",
    "status": "待办",
    "tags": ["work", "urgent"],
    "createdAt": "2023-06-01T10:00:00Z",
    "updatedAt": "2023-06-01T10:00:00Z"
  },
  {
    "taskId": "222e3333-e89b-12d3-a456-426614174000",
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "title": "准备会议材料",
    "description": "准备明天的团队会议材料",
    "status": "待办",
    "tags": ["work", "urgent"],
    "createdAt": "2023-06-01T09:00:00Z",
    "updatedAt": "2023-06-01T09:00:00Z"
  }
]
```

错误响应 (401 Unauthorized):
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "认证失败"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 从请求头获取用户ID
3. 根据查询参数过滤任务
4. 按创建时间升序排序（最早创建的任务排在前面）
5. 返回符合条件的任务列表

**重要说明**
- 任务列表默认按创建时间升序排序，确保任务顺序稳定
- 即使更新任务状态或创建新任务，已有任务的位置也不会改变
- 这种排序方式避免了任务在列表中"消失"的错觉

---

### 2. 获取任务详情

获取单个任务的详细信息。

**接口信息**
- **路径**: `/api/tasks/:taskId`
- **方法**: `GET`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `taskId` | string | 是 | 任务 ID（UUID 格式） |

**请求示例**
```bash
curl -X GET http://localhost:8080/api/tasks/111e2222-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**

成功响应 (200 OK):
```json
{
  "taskId": "111e2222-e89b-12d3-a456-426614174000",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "title": "完成项目报告",
  "description": "撰写本周项目进展报告",
  "status": "待办",
  "tags": ["work", "urgent"],
  "createdAt": "2023-06-01T10:00:00Z",
  "updatedAt": "2023-06-01T10:00:00Z"
}
```

错误响应 (403 Forbidden):
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "无权访问该任务"
  }
}
```

错误响应 (404 Not Found):
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 检查任务是否存在
3. 检查任务是否属于当前用户
4. 返回任务详细信息

---

### 3. 创建任务

创建新的任务。

**接口信息**
- **路径**: `/api/tasks`
- **方法**: `POST`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `title` | string | 是 | 任务标题 |
| `description` | string | 否 | 任务描述 |
| `tags` | string[] | 否 | 自定义标签数组 |

**请求示例**
```bash
curl -X POST http://localhost:8080/api/tasks \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成代码审查",
    "description": "审查团队成员提交的代码",
    "tags": ["work", "code-review"]
  }'
```

**响应示例**

成功响应 (201 Created):
```json
{
  "taskId": "333e4444-e89b-12d3-a456-426614174000",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "title": "完成代码审查",
  "description": "审查团队成员提交的代码",
  "status": "待办",
  "tags": ["work", "code-review"],
  "createdAt": "2023-06-01T11:00:00Z",
  "updatedAt": "2023-06-01T11:00:00Z"
}
```

错误响应 (400 Bad Request):
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "标题不能为空"
  }
}
```

错误响应 (401 Unauthorized):
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "认证失败"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 验证请求数据
3. 从请求头获取用户ID
4. 创建新任务记录，默认状态为"待办"
5. 返回新任务信息

---

### 4. 更新任务

更新任务的信息。

**接口信息**
- **路径**: `/api/tasks/:taskId`
- **方法**: `PUT`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `taskId` | string | 是 | 任务 ID（UUID 格式） |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `title` | string | 否 | 任务标题 |
| `description` | string | 否 | 任务描述 |
| `status` | string | 否 | 任务状态（待办/进行中/已完成/已延期/已取消） |
| `tags` | string[] | 否 | 自定义标签数组 |

**请求示例**
```bash
curl -X PUT http://localhost:8080/api/tasks/333e4444-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "进行中",
    "description": "审查团队成员提交的代码，重点关注性能问题"
  }'
```

**响应示例**

成功响应 (200 OK):
```json
{
  "taskId": "333e4444-e89b-12d3-a456-426614174000",
  "userId": "123e4567-e89b-12d3-a456-426614174000",
  "title": "完成代码审查",
  "description": "审查团队成员提交的代码，重点关注性能问题",
  "status": "进行中",
  "tags": ["work", "code-review"],
  "createdAt": "2023-06-01T11:00:00Z",
  "updatedAt": "2023-06-01T12:00:00Z"
}
```

错误响应 (400 Bad Request):
```json
{
  "error": {
    "code": "INVALID_STATUS",
    "message": "无效的任务状态"
  }
}
```

错误响应 (403 Forbidden):
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "无权访问该任务"
  }
}
```

错误响应 (404 Not Found):
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 验证请求数据
3. 检查任务是否存在
4. 检查任务是否属于当前用户
5. 更新任务信息
6. 返回更新后的任务信息

---

### 5. 删除任务

删除指定的任务。

**接口信息**
- **路径**: `/api/tasks/:taskId`
- **方法**: `DELETE`
- **认证**: 需要
- **Content-Type**: `application/json`

**请求头**
```
Authorization: Bearer default-token
X-User-ID: {用户ID}
X-Device-ID: {设备ID}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `taskId` | string | 是 | 任务 ID（UUID 格式） |

**请求示例**
```bash
curl -X DELETE http://localhost:8080/api/tasks/333e4444-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer default-token" \
  -H "X-User-ID: 123e4567-e89b-12d3-a456-426614174000" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**响应示例**

成功响应 (200 OK):
```json
{
  "message": "删除成功"
}
```

错误响应 (403 Forbidden):
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "无权访问该任务"
  }
}
```

错误响应 (404 Not Found):
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在"
  }
}
```

**业务逻辑**
1. 验证认证信息
2. 检查任务是否存在
3. 检查任务是否属于当前用户
4. 删除任务记录
5. 返回删除成功消息

---

## 错误码说明

### 通用错误码

| 错误码 | HTTP 状态码 | 说明 |
| :--- | :--- | :--- |
| `UNAUTHORIZED` | 401 | 认证失败 |
| `FORBIDDEN` | 403 | 无权限访问 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 设备管理错误码

| 错误码 | HTTP 状态码 | 说明 |
| :--- | :--- | :--- |
| `INVALID_DEVICE_ID` | 400 | 设备ID格式错误 |
| `DEVICE_NOT_FOUND` | 404 | 设备不存在 |

### 任务管理错误码

| 错误码 | HTTP 状态码 | 说明 |
| :--- | :--- | :--- |
| `INVALID_REQUEST` | 400 | 请求参数错误 |
| `INVALID_STATUS` | 400 | 无效的任务状态 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |

---

## 数据模型

### User (用户)

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 用户 ID |
| `createdAt` | Timestamp | 创建时间 |
| `updatedAt` | Timestamp | 更新时间 |

### Device (设备)

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 设备 ID |
| `userId` | UUID | 关联的用户 ID |
| `lastSeenAt` | Timestamp | 最后活跃时间 |
| `createdAt` | Timestamp | 创建时间 |
| `updatedAt` | Timestamp | 更新时间 |

### Task (任务)

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | UUID | 任务 ID |
| `userId` | UUID | 关联的用户 ID |
| `title` | string | 任务标题 |
| `description` | string | 任务描述 |
| `status` | string | 任务状态（待办/进行中/已完成/已延期/已取消） |
| `tags` | string[] | 自定义标签数组 |
| `createdAt` | Timestamp | 创建时间 |
| `updatedAt` | Timestamp | 更新时间 |

---

## 附录

### 任务状态说明

| 状态值 | 说明 |
| :--- | :--- |
| `待办` | 任务待处理 |
| `进行中` | 任务正在处理 |
| `已完成` | 任务已完成 |
| `已延期` | 任务已延期 |
| `已取消` | 任务已取消 |

### 时间格式

所有时间字段使用 ISO 8601 格式：
```
2023-06-01T10:00:00Z
```

### UUID 格式

所有 ID 字段使用 UUID v4 格式：
```
550e8400-e29b-41d4-a716-446655440000
```
