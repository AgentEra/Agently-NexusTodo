# NexusTodo Backend Tests

本目录包含 NexusTodo 后端 API 的测试用例。

## 测试文件说明

### 1. `device_test.go`
设备管理 API 测试用例，包括：
- 设备注册测试
- 设备状态检查测试
- 认证和授权测试

**测试用例列表：**
- `TestDeviceRegister_Success` - 成功注册设备
- `TestDeviceRegister_InvalidDeviceID` - 无效设备ID
- `TestDeviceRegister_EmptyDeviceID` - 空设备ID
- `TestDeviceRegister_MissingDeviceID` - 缺少设备ID
- `TestDeviceRegister_DuplicateDevice` - 重复注册设备
- `TestDeviceStatus_Success` - 成功获取设备状态
- `TestDeviceStatus_Unauthorized` - 未授权访问
- `TestDeviceStatus_MissingAuthorization` - 缺少认证信息
- `TestDeviceStatus_MissingDeviceID` - 缺少设备ID
- `TestDeviceStatus_MissingUserID` - 缺少用户ID
- `TestDeviceStatus_InvalidContentType` - 无效内容类型

### 2. `task_test.go`
任务管理 API 测试用例，包括：
- 任务 CRUD 操作测试
- 任务过滤测试
- 认证和授权测试

**测试用例列表：**
- `TestGetTasks_Success` - 成功获取任务列表
- `TestGetTasks_WithStatusFilter` - 按状态过滤任务
- `TestGetTasks_Unauthorized` - 未授权访问
- `TestCreateTask_Success` - 成功创建任务
- `TestCreateTask_EmptyTitle` - 空标题
- `TestCreateTask_Unauthorized` - 未授权创建
- `TestGetTask_Success` - 成功获取任务详情
- `TestGetTask_NotFound` - 任务不存在
- `TestGetTask_Forbidden` - 无权访问任务
- `TestUpdateTask_Success` - 成功更新任务
- `TestUpdateTask_InvalidStatus` - 无效任务状态
- `TestUpdateTask_NotFound` - 任务不存在
- `TestDeleteTask_Success` - 成功删除任务
- `TestDeleteTask_NotFound` - 任务不存在
- `TestDeleteTask_Forbidden` - 无权删除任务
- `TestTaskWorkflow_Crud` - 完整 CRUD 工作流测试

### 3. `exception_test.go`
异常处理测试用例，包括：
- 输入验证测试
- 认证和授权异常测试
- 资源不存在测试
- 边界条件测试

**测试用例列表：**
- `TestExceptionHandling_InvalidJSON` - 无效 JSON
- `TestExceptionHandling_InvalidContentType` - 无效内容类型
- `TestExceptionHandling_MissingRequiredFields` - 缺少必填字段
- `TestExceptionHandling_EmptyRequestBody` - 空请求体
- `TestExceptionHandling_InvalidUUIDFormat` - 无效 UUID 格式
- `TestExceptionHandling_AuthenticationFailure` - 认证失败
- `TestExceptionHandling_AuthorizationFailure` - 授权失败
- `TestExceptionHandling_ResourceNotFound` - 资源不存在
- `TestExceptionHandling_InvalidTaskStatus` - 无效任务状态
- `TestExceptionHandling_MissingHeaders` - 缺少请求头
- `TestExceptionHandling_InvalidQueryParameters` - 无效查询参数
- `TestExceptionHandling_InvalidHTTPMethod` - 无效 HTTP 方法
- `TestExceptionHandling_MalformedURL` - 格式错误的 URL
- `TestExceptionHandling_EmptyTaskTitle` - 空任务标题
- `TestExceptionHandling_VeryLongInput` - 超长输入
- `TestExceptionHandling_SpecialCharactersInInput` - 特殊字符输入

## 运行测试

### 运行所有测试
```bash
cd backend
go test ./tests/...
```

### 运行特定测试文件
```bash
cd backend
go test ./tests/device_test.go
```

### 运行特定测试用例
```bash
cd backend
go test ./tests/... -run TestDeviceRegister_Success
```

### 查看详细输出
```bash
cd backend
go test ./tests/... -v
```

### 查看测试覆盖率
```bash
cd backend
go test ./tests/... -cover
```

### 生成覆盖率报告
```bash
cd backend
go test ./tests/... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## 测试数据说明

测试使用模拟数据，包括：
- 设备 ID: `550e8400-e29b-41d4-a716-446655440000`
- 用户 ID: `123e4567-e89b-12d3-a456-426614000`
- 默认 Token: `default-token`

## 注意事项

1. 测试使用 Gin 框架的测试模式，不会输出实际的 HTTP 日志
2. 所有测试都是独立的，不依赖外部数据库
3. 测试使用内存中的模拟数据，不会影响实际数据
4. 测试完成后会自动清理模拟数据

## 扩展测试

如需添加新的测试用例，请遵循以下规范：

1. 测试函数命名以 `Test` 开头
2. 使用 `testing.T` 参数
3. 使用 `t.Run()` 进行子测试分组
4. 使用 `t.Errorf()` 或 `t.Fatalf()` 报告错误
5. 确保测试用例独立，不依赖其他测试的执行顺序

## 测试覆盖率目标

- 设备管理 API: 100%
- 任务管理 API: 100%
- 异常处理: 100%
- 整体覆盖率: 95% 以上
