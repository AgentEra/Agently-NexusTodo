package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

const (
	baseURL        = "/api"
	deviceEndpoint = "/device"
)

type DeviceRegisterRequest struct {
	DeviceID string `json:"deviceId" binding:"required,uuid"`
}

type DeviceRegisterResponse struct {
	DeviceID string `json:"deviceId"`
	UserID   string `json:"userId"`
	Message  string `json:"message"`
}

type DeviceStatusResponse struct {
	DeviceID  string `json:"deviceId"`
	UserID    string `json:"userId"`
	LastSeenAt string `json:"lastSeenAt"`
}

type ErrorResponse struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

func setupTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	router := gin.New()
	
	api := router.Group(baseURL)
	{
		device := api.Group(deviceEndpoint)
		{
			device.POST("/register", mockDeviceRegisterHandler)
			device.GET("/status", mockDeviceStatusHandler)
		}
	}
	
	return router
}

func mockDeviceRegisterHandler(c *gin.Context) {
	var req DeviceRegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_DEVICE_ID",
				Message: "设备ID格式错误",
			},
		})
		return
	}

	response := DeviceRegisterResponse{
		DeviceID: req.DeviceID,
		UserID:   "123e4567-e89b-12d3-a456-426614174000",
		Message:  "注册成功",
	}
	c.JSON(http.StatusOK, response)
}

func mockDeviceStatusHandler(c *gin.Context) {
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

	deviceID := c.GetHeader("X-Device-ID")
	if deviceID == "" {
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_REQUEST",
				Message: "设备ID不能为空",
			},
		})
		return
	}

	response := DeviceStatusResponse{
		DeviceID:  deviceID,
		UserID:    "123e4567-e89b-12d3-a456-426614174000",
		LastSeenAt: "2023-06-01T13:00:00Z",
	}
	c.JSON(http.StatusOK, response)
}

func TestDeviceRegister_Success(t *testing.T) {
	router := setupTestRouter()

	reqBody := DeviceRegisterRequest{
		DeviceID: "550e8400-e29b-41d4-a716-446655440000",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response DeviceRegisterResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.DeviceID != reqBody.DeviceID {
		t.Errorf("Expected device ID %s, got %s", reqBody.DeviceID, response.DeviceID)
	}

	if response.UserID == "" {
		t.Error("Expected non-empty user ID")
	}

	if response.Message != "注册成功" {
		t.Errorf("Expected message '注册成功', got '%s'", response.Message)
	}
}

func TestDeviceRegister_InvalidDeviceID(t *testing.T) {
	router := setupTestRouter()

	reqBody := DeviceRegisterRequest{
		DeviceID: "invalid-uuid",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}

	var response ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.Error.Code != "INVALID_DEVICE_ID" {
		t.Errorf("Expected error code 'INVALID_DEVICE_ID', got '%s'", response.Error.Code)
	}
}

func TestDeviceRegister_EmptyDeviceID(t *testing.T) {
	router := setupTestRouter()

	reqBody := DeviceRegisterRequest{
		DeviceID: "",
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestDeviceRegister_MissingDeviceID(t *testing.T) {
	router := setupTestRouter()

	reqBody := map[string]interface{}{}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestDeviceRegister_DuplicateDevice(t *testing.T) {
	router := setupTestRouter()

	deviceID := "550e8400-e29b-41d4-a716-446655440000"

	reqBody := DeviceRegisterRequest{
		DeviceID: deviceID,
	}

	jsonBody, _ := json.Marshal(reqBody)
	req, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("First registration failed with status code %d", w.Code)
	}

	req2, _ := http.NewRequest("POST", baseURL+deviceEndpoint+"/register", bytes.NewBuffer(jsonBody))
	req2.Header.Set("Content-Type", "application/json")

	w2 := httptest.NewRecorder()
	router.ServeHTTP(w2, req2)

	if w2.Code != http.StatusOK {
		t.Errorf("Second registration failed with status code %d", w2.Code)
	}

	var response DeviceRegisterResponse
	err := json.Unmarshal(w2.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.DeviceID != deviceID {
		t.Errorf("Expected device ID %s, got %s", deviceID, response.DeviceID)
	}
}

func TestDeviceStatus_Success(t *testing.T) {
	router := setupTestRouter()

	deviceID := "550e8400-e29b-41d4-a716-446655440000"
	userID := "123e4567-e89b-12d3-a456-426614174000"

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-Device-ID", deviceID)
	req.Header.Set("X-User-ID", userID)

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response DeviceStatusResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.DeviceID != deviceID {
		t.Errorf("Expected device ID %s, got %s", deviceID, response.DeviceID)
	}

	if response.UserID != userID {
		t.Errorf("Expected user ID %s, got %s", userID, response.UserID)
	}

	if response.LastSeenAt == "" {
		t.Error("Expected non-empty lastSeenAt")
	}
}

func TestDeviceStatus_Unauthorized(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	req.Header.Set("X-Device-ID", "550e8400-e29b-41d4-a716-446655440000")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("Expected status code %d, got %d", http.StatusUnauthorized, w.Code)
	}

	var response ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}

	if response.Error.Code != "UNAUTHORIZED" {
		t.Errorf("Expected error code 'UNAUTHORIZED', got '%s'", response.Error.Code)
	}
}

func TestDeviceStatus_MissingAuthorization(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("X-Device-ID", "550e8400-e29b-41d4-a716-446655440000")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Errorf("Expected status code %d, got %d", http.StatusUnauthorized, w.Code)
	}
}

func TestDeviceStatus_MissingDeviceID(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}

	var response ErrorResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Errorf("Failed to parse response: %v", err)
	}
}

func TestDeviceStatus_MissingUserID(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-Device-ID", "550e8400-e29b-41d4-a716-446655440000")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}
}

func TestDeviceStatus_InvalidContentType(t *testing.T) {
	router := setupTestRouter()

	req, _ := http.NewRequest("GET", baseURL+deviceEndpoint+"/status", nil)
	req.Header.Set("Authorization", "Bearer default-token")
	req.Header.Set("X-Device-ID", "550e8400-e29b-41d4-a716-446655440000")
	req.Header.Set("X-User-ID", "123e4567-e89b-12d3-a456-426614174000")
	req.Header.Set("Content-Type", "application/xml")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}
}
