package tests

import (
	"bytes"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

const (
	taskEndpoint = "/tasks"
)

type TaskCreateRequest struct {
	Title       string   `json:"title" binding:"required"`
	Description string   `json:"description"`
	Tags        []string `json:"tags"`
}

type TaskUpdateRequest struct {
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Status      string   `json:"status" binding:"omitempty,oneof=待办 进行中 已完成 已延期 已取消"`
	Tags        []string `json:"tags"`
}

type TaskResponse struct {
	TaskID      string   `json:"taskId"`
	UserID      string   `json:"userId"`
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Status      string   `json:"status"`
	Tags        []string `json:"tags"`
	CreatedAt   string   `json:"createdAt"`
	UpdatedAt   string   `json:"updatedAt"`
}

type TaskListResponse []TaskResponse

type SuccessResponse struct {
	Message string `json:"message"`
}

var (
	mockTasks = make(map[string]TaskResponse)
)

func generateUUID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func setupTaskTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()

	api := router.Group(baseURL)
	{
		task := api.Group(taskEndpoint)
		{
			task.GET("", mockGetTasksHandler)
			task.POST("", mockCreateTaskHandler)
			task.GET("/:taskId", mockGetTaskHandler)
			task.PUT("/:taskId", mockUpdateTaskHandler)
			task.DELETE("/:taskId", mockDeleteTaskHandler)
		}
	}

	return router
}

func mockGetTasksHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader != "Bearer default-token" {
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "UNAUTHORIZED",
				Message: "认证失败",
			},
		})
		return
	}

	userID := c.GetHeader("X-User-ID")
	status := c.Query("status")
	tags := c.Query("tags")

	var filteredTasks []TaskResponse
	for _, task := range mockTasks {
		if task.UserID != userID {
			continue
		}
		if status != "" && task.Status != status {
			continue
		}
		if tags != "" {
			tagMap := make(map[string]bool)
			for _, tag := range task.Tags {
				tagMap[tag] = true
			}
			found := false
			for _, filterTag := range parseTags(tags) {
				if tagMap[filterTag] {
					found = true
					break
				}
			}
			if !found {
				continue
			}
		}
		filteredTasks = append(filteredTasks, task)
	}

	c.JSON(http.StatusOK, filteredTasks)
}

func mockCreateTaskHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader != "Bearer default-token" {
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "UNAUTHORIZED",
				Message: "认证失败",
			},
		})
		return
	}

	var req TaskCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_REQUEST",
				Message: "请求参数错误",
			},
		})
		return
	}

	if req.Title == "" {
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_REQUEST",
				Message: "标题不能为空",
			},
		})
		return
	}

	taskID := generateUUID()
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		userID = "123e4567-e89b-12d3-a456-426614174000"
	}

	task := TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       req.Title,
		Description: req.Description,
		Status:      "待办",
		Tags:        req.Tags,
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	mockTasks[taskID] = task
	c.JSON(http.StatusCreated, task)
}

func mockGetTaskHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader != "Bearer default-token" {
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "UNAUTHORIZED",
				Message: "认证失败",
			},
		})
		return
	}

	taskID := c.Param("taskId")
	task, exists := mockTasks[taskID]
	if !exists {
		c.JSON(http.StatusNotFound, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "TASK_NOT_FOUND",
				Message: "任务不存在",
			},
		})
		return
	}

	userID := c.GetHeader("X-User-ID")
	if task.UserID != userID {
		c.JSON(http.StatusForbidden, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "FORBIDDEN",
				Message: "无权访问该任务",
			},
		})
		return
	}

	c.JSON(http.StatusOK, task)
}

func mockUpdateTaskHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader != "Bearer default-token" {
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "UNAUTHORIZED",
				Message: "认证失败",
			},
		})
		return
	}

	taskID := c.Param("taskId")
	task, exists := mockTasks[taskID]
	if !exists {
		c.JSON(http.StatusNotFound, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "TASK_NOT_FOUND",
				Message: "任务不存在",
			},
		})
		return
	}

	userID := c.GetHeader("X-User-ID")
	if task.UserID != userID {
		c.JSON(http.StatusForbidden, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "FORBIDDEN",
				Message: "无权访问该任务",
			},
		})
		return
	}

	var req TaskUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_STATUS",
				Message: "无效的任务状态",
			},
		})
		return
	}

	if req.Title != "" {
		task.Title = req.Title
	}
	if req.Description != "" {
		task.Description = req.Description
	}
	if req.Status != "" {
		task.Status = req.Status
	}
	if req.Tags != nil {
		task.Tags = req.Tags
	}
	task.UpdatedAt = "2023-06-01T12:00:00Z"

	mockTasks[taskID] = task
	c.JSON(http.StatusOK, task)
}

func mockDeleteTaskHandler(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader != "Bearer default-token" {
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "UNAUTHORIZED",
				Message: "认证失败",
			},
		})
		return
	}

	taskID := c.Param("taskId")
	task, exists := mockTasks[taskID]
	if !exists {
		c.JSON(http.StatusNotFound, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "TASK_NOT_FOUND",
				Message: "任务不存在",
			},
		})
		return
	}

	userID := c.GetHeader("X-User-ID")
	if task.UserID != userID {
		c.JSON(http.StatusForbidden, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "FORBIDDEN",
				Message: "无权访问该任务",
			},
		})
		return
	}

	delete(mockTasks, taskID)
	c.JSON(http.StatusOK, SuccessResponse{
		Message: "删除成功",
	})
}

func parseTags(tagsStr string) []string {
	var tags []string
	for _, tag := range []string{tagsStr} {
		tags = append(tags, tag)
	}
	return tags
}

func TestGetTasks_Success(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614174000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("GET", baseURL+taskEndpoint, nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var tasks []TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if len(tasks) == 0 {
		t.Error("Expected at least one task")
	}

	delete(mockTasks, taskID)
}

func TestGetTasks_WithStatusFilter(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614174000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "进行中",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("GET", baseURL+taskEndpoint+"?status=进行中", nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var tasks []TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	for _, task := range tasks {
		if task.Status != "进行中" {
			t.Errorf("Expected status '进行中', got '%s'", task.Status)
		}
	}

	delete(mockTasks, taskID)
}

func TestGetTasks_Unauthorized(t *testing.T) {
	router := setupTaskTestRouter()

	req, _ := http.NewRequest("GET", baseURL+taskEndpoint, nil)
	req.Header.Set("Authorization", "Bearer invalid-token")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("Expected status code %d, got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestCreateTask_Success(t *testing.T) {
	router := setupTaskTestRouter()

	reqBody := TaskCreateRequest{
		Title:       "新任务",
		Description: "任务描述",
		Tags:        []string{"work", "urgent"},
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status code %d, got %d", http.StatusCreated, w.Code)
	}

	var task TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &task)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if task.Title != reqBody.Title {
		t.Errorf("Expected title '%s', got '%s'", reqBody.Title, task.Title)
	}

	if task.Status != "待办" {
		t.Errorf("Expected default status '待办', got '%s'", task.Status)
	}
}

func TestCreateTask_EmptyTitle(t *testing.T) {
	router := setupTaskTestRouter()

	reqBody := TaskCreateRequest{
		Title: "",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestCreateTask_Unauthorized(t *testing.T) {
	router := setupTaskTestRouter()

	reqBody := TaskCreateRequest{
		Title: "新任务",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer invalid-token")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("Expected status code %d, got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestGetTask_Success(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("GET", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var task TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &task)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if task.TaskID != taskID {
		t.Errorf("Expected task ID %s, got %s", taskID, task.TaskID)
	}

	delete(mockTasks, taskID)
}

func TestGetTask_NotFound(t *testing.T) {
	router := setupTaskTestRouter()

	taskID := generateUUID()

	req, _ := http.NewRequest("GET", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status code %d, got %d", http.StatusNotFound, w.Code)
	}
}

func TestGetTask_Forbidden(t *testing.T) {
	router := setupTaskTestRouter()

	userID1 := "123e4567-e89b-12d3-a456-426614000"
	userID2 := "223e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID1,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("GET", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID2)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Errorf("Expected status code %d, got %d", http.StatusForbidden, w.Code)
	}

	delete(mockTasks, taskID)
}

func TestUpdateTask_Success(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "原标题",
		Description: "原描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	reqBody := TaskUpdateRequest{
		Status:      "进行中",
		Description: "新描述",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var task TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &task)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if task.Status != reqBody.Status {
		t.Errorf("Expected status '%s', got '%s'", reqBody.Status, task.Status)
	}

	if task.Description != reqBody.Description {
		t.Errorf("Expected description '%s', got '%s'", reqBody.Description, task.Description)
	}

	delete(mockTasks, taskID)
}

func TestUpdateTask_InvalidStatus(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "原标题",
		Description: "原描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	reqBody := TaskUpdateRequest{
		Status: "无效状态",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}

	delete(mockTasks, taskID)
}

func TestUpdateTask_NotFound(t *testing.T) {
	router := setupTaskTestRouter()

	taskID := generateUUID()

	reqBody := TaskUpdateRequest{
		Status: "进行中",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status code %d, got %d", http.StatusNotFound, w.Code)
	}
}

func TestDeleteTask_Success(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("DELETE", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response SuccessResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.Message != "删除成功" {
		t.Errorf("Expected message '删除成功', got '%s'", response.Message)
	}

	if _, exists := mockTasks[taskID]; exists {
		t.Error("Task should be deleted")
	}
}

func TestDeleteTask_NotFound(t *testing.T) {
	router := setupTaskTestRouter()

	taskID := generateUUID()

	req, _ := http.NewRequest("DELETE", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("Expected status code %d, got %d", http.StatusNotFound, w.Code)
	}
}

func TestDeleteTask_Forbidden(t *testing.T) {
	router := setupTaskTestRouter()

	userID1 := "123e4567-e89b-12d3-a456-426614000"
	userID2 := "223e4567-e89b-12d3-a456-426614000"
	taskID := generateUUID()

	mockTasks[taskID] = TaskResponse{
		TaskID:      taskID,
		UserID:      userID1,
		Title:       "测试任务",
		Description: "测试描述",
		Status:      "待办",
		Tags:        []string{"work"},
		CreatedAt:   "2023-06-01T10:00:00Z",
		UpdatedAt:   "2023-06-01T10:00:00Z",
	}

	req, _ := http.NewRequest("DELETE", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID2)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Errorf("Expected status code %d, got %d", http.StatusForbidden, w.Code)
	}

	delete(mockTasks, taskID)
}

func TestTaskWorkflow_Crud(t *testing.T) {
	router := setupTaskTestRouter()

	userID := "123e4567-e89b-12d3-a456-426614174000"

	createReqBody := TaskCreateRequest{
		Title:       "工作流测试任务",
		Description: "这是一个测试任务",
		Tags:        []string{"test", "workflow"},
	}

	jsonBody, _ := json.Marshal(createReqBody)
	createReq, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
	createReq.Header.Set("Content-Type", "application/json")
	createReq.Header.Set("Authorization", "Bearer default-token")
	createReq.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, createReq)

	if w.Code != http.StatusCreated {
		t.Fatalf("Failed to create task, status code %d", w.Code)
	}

	var createdTask TaskResponse
	err := json.Unmarshal(w.Body.Bytes(), &createdTask)
	if err != nil {
		t.Fatalf("Failed to parse create response: %v", err)
	}

	taskID := createdTask.TaskID

	getReq, _ := http.NewRequest("GET", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	getReq.Header.Set("Authorization", "Bearer default-token")
	getReq.Header.Set("X-User-ID", userID)

	w = httptest.NewRecorder()
	router.ServeHTTP(w, getReq)

	if w.Code != http.StatusOK {
		t.Fatalf("Failed to get task, status code %d", w.Code)
	}

	var retrievedTask TaskResponse
	err = json.Unmarshal(w.Body.Bytes(), &retrievedTask)
	if err != nil {
		t.Fatalf("Failed to parse get response: %v", err)
	}

	if retrievedTask.TaskID != taskID {
		t.Errorf("Task ID mismatch")
	}

	updateReqBody := TaskUpdateRequest{
		Status:      "进行中",
		Description: "更新后的描述",
	}

	jsonBody, _ = json.Marshal(updateReqBody)
	updateReq, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), bytes.NewBuffer(jsonBody))
	updateReq.Header.Set("Content-Type", "application/json")
	updateReq.Header.Set("Authorization", "Bearer default-token")
	updateReq.Header.Set("X-User-ID", userID)

	w = httptest.NewRecorder()
	router.ServeHTTP(w, updateReq)

	if w.Code != http.StatusOK {
		t.Fatalf("Failed to update task, status code %d", w.Code)
	}

	var updatedTask TaskResponse
	err = json.Unmarshal(w.Body.Bytes(), &updatedTask)
	if err != nil {
		t.Fatalf("Failed to parse update response: %v", err)
	}

	if updatedTask.Status != "进行中" {
		t.Errorf("Expected status '进行中', got '%s'", updatedTask.Status)
	}

	deleteReq, _ := http.NewRequest("DELETE", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, taskID), nil)
	deleteReq.Header.Set("Authorization", "Bearer default-token")
	deleteReq.Header.Set("X-User-ID", userID)

	w = httptest.NewRecorder()
	router.ServeHTTP(w, deleteReq)

	if w.Code != http.StatusOK {
		t.Fatalf("Failed to delete task, status code %d", w.Code)
	}

	if _, exists := mockTasks[taskID]; exists {
		t.Error("Task should be deleted after workflow")
	}
}
