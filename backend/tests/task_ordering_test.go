package tests

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/nexustodo/backend/api"
	"github.com/nexustodo/backend/models"
	"github.com/nexustodo/backend/services"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func setupIntegrationTestRouter() (*gin.Engine, *gorm.DB, func()) {
	gin.SetMode(gin.TestMode)

	db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if err != nil {
		panic("Failed to connect to database: " + err.Error())
	}

	if err := db.AutoMigrate(&models.User{}, &models.Device{}, &models.Task{}); err != nil {
		panic("Failed to migrate database: " + err.Error())
	}

	deviceService := services.NewDeviceService(db)
	taskService := services.NewTaskService(db)

	router := api.SetupRouter(deviceService, taskService)

	cleanup := func() {
		db.Exec("DELETE FROM tasks")
		db.Exec("DELETE FROM devices")
		db.Exec("DELETE FROM users")
	}

	return router, db, cleanup
}

func TestTaskOrdering_Stability(t *testing.T) {
	router, _, cleanup := setupIntegrationTestRouter()
	defer cleanup()

	userID := "test-user-id"

	task1Req := TaskCreateRequest{
		Title:       "第一个任务",
		Description: "这是第一个测试任务",
		Tags:        []string{"test"},
	}

	task1ReqBody, _ := json.Marshal(task1Req)
	req1, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task1ReqBody))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("Authorization", "Bearer default-token")
	req1.Header.Set("X-User-ID", userID)

	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)

	if w1.Code != http.StatusCreated {
		t.Errorf("Expected status code %d, got %d", http.StatusCreated, w1.Code)
	}

	var task1 TaskResponse
	err := json.Unmarshal(w1.Body.Bytes(), &task1)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	task1ID := task1.TaskID
	if task1ID == "" {
		t.Error("Expected non-empty task ID")
	}

	if task1.Status != "待办" {
		t.Errorf("Expected status '待办', got '%s'", task1.Status)
	}

	updateReq := TaskUpdateRequest{
		Status: "进行中",
	}

	updateReqBody, _ := json.Marshal(updateReq)
	req2, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, task1ID), bytes.NewBuffer(updateReqBody))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", "Bearer default-token")
	req2.Header.Set("X-User-ID", userID)

	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)

	if w2.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w2.Code)
	}

	var updatedTask TaskResponse
	err = json.Unmarshal(w2.Body.Bytes(), &updatedTask)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if updatedTask.Status != "进行中" {
		t.Errorf("Expected status '进行中', got '%s'", updatedTask.Status)
	}

	task2Req := TaskCreateRequest{
		Title:       "第二个任务",
		Description: "这是第二个测试任务",
		Tags:        []string{"test"},
	}

	task2ReqBody, _ := json.Marshal(task2Req)
	req3, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task2ReqBody))
	req3.Header.Set("Content-Type", "application/json")
	req3.Header.Set("Authorization", "Bearer default-token")
	req3.Header.Set("X-User-ID", userID)

	w3 := httptest.NewRecorder()
	router.ServeHTTP(w3, req3)

	if w3.Code != http.StatusCreated {
		t.Errorf("Expected status code %d, got %d", http.StatusCreated, w3.Code)
	}

	var task2 TaskResponse
	err = json.Unmarshal(w3.Body.Bytes(), &task2)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	task2ID := task2.TaskID
	if task2ID == "" {
		t.Error("Expected non-empty task ID")
	}

	if task2.Status != "待办" {
		t.Errorf("Expected status '待办', got '%s'", task2.Status)
	}

	req4, _ := http.NewRequest("GET", baseURL+taskEndpoint, nil)
	req4.Header.Set("Authorization", "Bearer default-token")
	req4.Header.Set("X-User-ID", userID)

	w4 := httptest.NewRecorder()
	router.ServeHTTP(w4, req4)

	if w4.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w4.Code)
	}

	var tasks TaskListResponse
	err = json.Unmarshal(w4.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if len(tasks) != 2 {
		t.Errorf("Expected 2 tasks, got %d", len(tasks))
	}

	if tasks[0].TaskID != task1ID {
		t.Errorf("Expected first task ID %s, got %s", task1ID, tasks[0].TaskID)
	}

	if tasks[1].TaskID != task2ID {
		t.Errorf("Expected second task ID %s, got %s", task2ID, tasks[1].TaskID)
	}

	if tasks[0].Status != "进行中" {
		t.Errorf("Expected first task status '进行中', got '%s'", tasks[0].Status)
	}

	if tasks[1].Status != "待办" {
		t.Errorf("Expected second task status '待办', got '%s'", tasks[1].Status)
	}
}

func TestTaskOrdering_MultipleUpdates(t *testing.T) {
	router, _, cleanup := setupIntegrationTestRouter()
	defer cleanup()

	userID := "test-user-id"

	for i := 1; i <= 5; i++ {
		taskReq := TaskCreateRequest{
			Title:       fmt.Sprintf("任务%d", i),
			Description: fmt.Sprintf("这是第%d个测试任务", i),
			Tags:        []string{"test"},
		}

		taskReqBody, _ := json.Marshal(taskReq)
		req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(taskReqBody))
		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer default-token")
		req.Header.Set("X-User-ID", userID)

		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusCreated {
			t.Errorf("Failed to create task %d, status code: %d", i, w.Code)
		}
	}

	req, _ := http.NewRequest("GET", baseURL+taskEndpoint, nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var tasks TaskListResponse
	err := json.Unmarshal(w.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if len(tasks) != 5 {
		t.Errorf("Expected 5 tasks, got %d", len(tasks))
	}

	for i := 0; i < len(tasks)-1; i++ {
		if tasks[i].Title > tasks[i+1].Title {
			t.Errorf("Task order is incorrect: %s should come before %s", tasks[i].Title, tasks[i+1].Title)
		}
	}
}

func TestTaskOrdering_WithStatusFilter(t *testing.T) {
	router, _, cleanup := setupIntegrationTestRouter()
	defer cleanup()

	userID := "test-user-id"

	task1Req := TaskCreateRequest{
		Title:       "待办任务",
		Description: "这是一个待办任务",
		Tags:        []string{"todo"},
	}

	task1ReqBody, _ := json.Marshal(task1Req)
	req1, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task1ReqBody))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("Authorization", "Bearer default-token")
	req1.Header.Set("X-User-ID", userID)

	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)

	task2Req := TaskCreateRequest{
		Title:       "进行中任务",
		Description: "这是一个进行中任务",
		Tags:        []string{"inprogress"},
	}

	task2ReqBody, _ := json.Marshal(task2Req)
	req2, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task2ReqBody))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", "Bearer default-token")
	req2.Header.Set("X-User-ID", userID)

	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)

	req3, _ := http.NewRequest("GET", baseURL+taskEndpoint+"?status=待办", nil)
	req3.Header.Set("Authorization", "Bearer default-token")
	req3.Header.Set("X-User-ID", userID)

	w3 := httptest.NewRecorder()
	router.ServeHTTP(w3, req3)

	if w3.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w3.Code)
	}

	var tasks TaskListResponse
	err := json.Unmarshal(w3.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if len(tasks) != 1 {
		t.Errorf("Expected 1 task with status '待办', got %d", len(tasks))
	}

	if tasks[0].Title != "待办任务" {
		t.Errorf("Expected task title '待办任务', got '%s'", tasks[0].Title)
	}
}

func TestTaskOrdering_UpdateAfterCreation(t *testing.T) {
	router, _, cleanup := setupIntegrationTestRouter()
	defer cleanup()

	userID := "test-user-id"

	task1Req := TaskCreateRequest{
		Title:       "任务1",
		Description: "第一个任务",
		Tags:        []string{"test"},
	}

	task1ReqBody, _ := json.Marshal(task1Req)
	req1, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task1ReqBody))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("Authorization", "Bearer default-token")
	req1.Header.Set("X-User-ID", userID)

	w1 := httptest.NewRecorder()
	router.ServeHTTP(w1, req1)

	var task1 TaskResponse
	json.Unmarshal(w1.Body.Bytes(), &task1)

	task2Req := TaskCreateRequest{
		Title:       "任务2",
		Description: "第二个任务",
		Tags:        []string{"test"},
	}

	task2ReqBody, _ := json.Marshal(task2Req)
	req2, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(task2ReqBody))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", "Bearer default-token")
	req2.Header.Set("X-User-ID", userID)

	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)

	var task2 TaskResponse
	json.Unmarshal(w2.Body.Bytes(), &task2)

	updateReq := TaskUpdateRequest{
		Status: "已完成",
	}

	updateReqBody, _ := json.Marshal(updateReq)
	req3, _ := http.NewRequest("PUT", fmt.Sprintf("%s%s/%s", baseURL, taskEndpoint, task1.TaskID), bytes.NewBuffer(updateReqBody))
	req3.Header.Set("Content-Type", "application/json")
	req3.Header.Set("Authorization", "Bearer default-token")
	req3.Header.Set("X-User-ID", userID)

	w3 := httptest.NewRecorder()
	router.ServeHTTP(w3, req3)

	req4, _ := http.NewRequest("GET", baseURL+taskEndpoint, nil)
	req4.Header.Set("Authorization", "Bearer default-token")
	req4.Header.Set("X-User-ID", userID)

	w4 := httptest.NewRecorder()
	router.ServeHTTP(w4, req4)

	if w4.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w4.Code)
	}

	var tasks TaskListResponse
	err := json.Unmarshal(w4.Body.Bytes(), &tasks)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if len(tasks) != 2 {
		t.Errorf("Expected 2 tasks, got %d", len(tasks))
	}

	if tasks[0].TaskID != task1.TaskID {
		t.Errorf("Expected first task ID %s, got %s", task1.TaskID, tasks[0].TaskID)
	}

	if tasks[1].TaskID != task2.TaskID {
		t.Errorf("Expected second task ID %s, got %s", task2.TaskID, tasks[1].TaskID)
	}

	if tasks[0].Status != "已完成" {
		t.Errorf("Expected first task status '已完成', got '%s'", tasks[0].Status)
	}

	if tasks[1].Status != "待办" {
		t.Errorf("Expected second task status '待办', got '%s'", tasks[1].Status)
	}
}
