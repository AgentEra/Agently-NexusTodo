package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

type TestResponse struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

func setupExceptionTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()

	api := router.Group(baseURL)
	{
		device := api.Group(deviceEndpoint)
		{
			device.POST("/register", mockDeviceRegisterHandler)
			device.GET("/status", mockDeviceStatusHandler)
		}

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

func TestExceptionHandling_InvalidJSON(t *testing.T) {
	router := setupExceptionTestRouter()

	invalidJSON := `{"deviceId": "invalid-json`

	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBufferString(invalidJSON))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d for invalid JSON, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestExceptionHandling_InvalidContentType(t *testing.T) {
	router := setupExceptionTestRouter()

	xmlBody := `<deviceId>550e8400-e29b-41d4-a716-446655440000</deviceId>`
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBufferString(xmlBody))
	req.Header.Set("Content-Type", "application/xml")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d for invalid content type, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestExceptionHandling_MissingRequiredFields(t *testing.T) {
	router := setupExceptionTestRouter()

	reqBody := map[string]interface{}{}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d for missing required fields, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestExceptionHandling_EmptyRequestBody(t *testing.T) {
	router := setupExceptionTestRouter()

	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBufferString(""))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d for empty request body, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestExceptionHandling_InvalidUUIDFormat(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name     string
		deviceID string
	}{
		{"Invalid UUID - Too short", "123"},
		{"Invalid UUID - No hyphens", "550e8400e29b41d4a716446655440000"},
		{"Invalid UUID - Random string", "not-a-uuid"},
		{"Invalid UUID - Special characters", "550e8400-e29b-41d4-a716-44665544!!!!"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqBody := DeviceRegisterRequest{
				DeviceID: tc.deviceID,
			}

			jsonBody, _ := json.Marshal(reqBody)
			req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != http.StatusBadRequest {
				t.Errorf("Expected status code %d for invalid UUID, got %d", http.StatusBadRequest, w.Code)
			}
		})
	}
}

func TestExceptionHandling_AuthenticationFailure(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		authHeader     string
		expectedStatus int
	}{
		{"Missing Authorization header", "", http.StatusUnauthorized},
		{"Invalid token format", "invalid-token", http.StatusUnauthorized},
		{"Wrong token", "Bearer wrong-token", http.StatusUnauthorized},
		{"Empty token", "Bearer ", http.StatusUnauthorized},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
			if tc.authHeader != "" {
				req.Header.Set("Authorization", tc.authHeader)
			}
			req.Header.Set("X-Device-ID", "550e8400-e29b-41d4-a716-446655440000")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_AuthorizationFailure(t *testing.T) {
	router := setupExceptionTestRouter()

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

	testCases := []struct {
		name           string
		userID         string
		expectedStatus int
	}{
		{"Different user accessing task", userID2, http.StatusForbidden},
		{"Empty user ID", "", http.StatusForbidden},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest("GET", baseURL+taskEndpoint+"/"+taskID, nil)
			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", tc.userID)

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}

			if tc.expectedStatus == http.StatusForbidden {
				var response TestResponse
				err := json.Unmarshal(w.Body.Bytes(), &response)
				if err != nil {
					t.Errorf("Failed to parse response: %v", err)
				}

				if response.Error.Code != "FORBIDDEN" {
					t.Errorf("Expected error code 'FORBIDDEN', got '%s'", response.Error.Code)
				}
			}
		})
	}

	delete(mockTasks, taskID)
}

func TestExceptionHandling_ResourceNotFound(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		endpoint       string
		method         string
		expectedStatus int
	}{
		{"Get non-existent task", baseURL + taskEndpoint + "/non-existent-task-id", "GET", http.StatusNotFound},
		{"Update non-existent task", baseURL + taskEndpoint + "/non-existent-task-id", "PUT", http.StatusNotFound},
		{"Delete non-existent task", baseURL + taskEndpoint + "/non-existent-task-id", "DELETE", http.StatusNotFound},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			var req *http.Request

			if tc.method == "GET" || tc.method == "DELETE" {
				req, _ = http.NewRequest(tc.method, tc.endpoint, nil)
			} else {
				reqBody := TaskUpdateRequest{
					Status: "进行中",
				}
				jsonBody, _ := json.Marshal(reqBody)
				req, _ = http.NewRequest(tc.method, tc.endpoint, bytes.NewBuffer(jsonBody))
				req.Header.Set("Content-Type", "application/json")
			}

			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614000")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}

			var response TestResponse
			err := json.Unmarshal(w.Body.Bytes(), &response)
			if err != nil {
				t.Errorf("Failed to parse response: %v", err)
			}

			if response.Error.Code != "TASK_NOT_FOUND" {
				t.Errorf("Expected error code 'TASK_NOT_FOUND', got '%s'", response.Error.Code)
			}
		})
	}
}

func TestExceptionHandling_InvalidTaskStatus(t *testing.T) {
	router := setupExceptionTestRouter()

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

	testCases := []struct {
		name           string
		status         string
		expectedStatus int
	}{
		{"Invalid status - Random string", "invalid-status", http.StatusBadRequest},
		{"Invalid status - Empty string", "", http.StatusBadRequest},
		{"Invalid status - Number", "123", http.StatusBadRequest},
		{"Invalid status - Special characters", "待办!", http.StatusBadRequest},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqBody := TaskUpdateRequest{
				Status: tc.status,
			}

			jsonBody, _ := json.Marshal(reqBody)
			req, _ := http.NewRequest("PUT", baseURL+taskEndpoint+"/"+taskID, bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", userID)

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}

	delete(mockTasks, taskID)
}

func TestExceptionHandling_MissingHeaders(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		method         string
		endpoint       string
		headers        map[string]string
		expectedStatus int
	}{
		{
			name:     "Missing X-Device-ID header",
			method:   "GET",
			endpoint: baseURL + deviceEndpoint + "/status",
			headers: map[string]string{
				"Authorization": "Bearer default-token",
			},
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:     "Missing X-User-ID header",
			method:   "GET",
			endpoint: baseURL + taskEndpoint,
			headers: map[string]string{
				"Authorization": "Bearer default-token",
			},
			expectedStatus: http.StatusOK,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest(tc.method, tc.endpoint, nil)
			for key, value := range tc.headers {
				req.Header.Set(key, value)
			}

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_InvalidQueryParameters(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		queryParams    string
		expectedStatus int
	}{
		{"Invalid status parameter", "?status=invalid-status", http.StatusOK},
		{"Empty status parameter", "?status=", http.StatusOK},
		{"Multiple status parameters", "?status=待办&status=进行中", http.StatusOK},
		{"Invalid tags format", "?tags=work,urgent,extra", http.StatusOK},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest("GET", baseURL+taskEndpoint+tc.queryParams, nil)
			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614000")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_InvalidHTTPMethod(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		method         string
		endpoint       string
		expectedStatus int
	}{
		{"POST on task detail endpoint", "POST", baseURL + taskEndpoint + "/task-id", http.StatusNotFound},
		{"PATCH on task endpoint", "PATCH", baseURL + taskEndpoint + "/task-id", http.StatusNotFound},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest(tc.method, tc.endpoint, nil)
			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614000")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_MalformedURL(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		endpoint       string
		expectedStatus int
	}{
		{"URL with special characters", baseURL + taskEndpoint + "/task-id%20with%20spaces", http.StatusNotFound},
		{"URL with invalid characters", baseURL + taskEndpoint + "/task-id<script>", http.StatusNotFound},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req, _ := http.NewRequest("GET", tc.endpoint, nil)
			req.Header.Set("Authorization", "Bearer default-token")
			req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614000")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_EmptyTaskTitle(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		title          string
		expectedStatus int
	}{
		{"Empty title", "", http.StatusBadRequest},
		{"Whitespace only title", "   ", http.StatusBadRequest},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqBody := TaskCreateRequest{
				Title: tc.title,
			}

			jsonBody, _ := json.Marshal(reqBody)
			req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Authorization", "Bearer default-token")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}

func TestExceptionHandling_VeryLongInput(t *testing.T) {
	router := setupExceptionTestRouter()

	longTitle := ""
	for i := 0; i < 10000; i++ {
		longTitle += "a"
	}

	reqBody := TaskCreateRequest{
		Title: longTitle,
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer default-token")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status code %d for very long input, got %d", http.StatusCreated, w.Code)
	}
}

func TestExceptionHandling_SpecialCharactersInInput(t *testing.T) {
	router := setupExceptionTestRouter()

	testCases := []struct {
		name           string
		title          string
		expectedStatus int
	}{
		{"Title with HTML tags", "<script>alert('test')</script>", http.StatusCreated},
		{"Title with SQL injection", "'; DROP TABLE tasks; --", http.StatusCreated},
		{"Title with special characters", "任务@#$%^&*()", http.StatusCreated},
		{"Title with emojis", "任务🎉🚀", http.StatusCreated},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reqBody := TaskCreateRequest{
				Title: tc.title,
			}

			jsonBody, _ := json.Marshal(reqBody)
			req, _ := http.NewRequest("POST", baseURL+taskEndpoint, bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Authorization", "Bearer default-token")

			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			if w.Code != tc.expectedStatus {
				t.Errorf("Expected status code %d, got %d", tc.expectedStatus, w.Code)
			}
		})
	}
}
