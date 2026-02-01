package api

import (
	"github.com/gin-gonic/gin"
	"github.com/nexustodo/backend/schemas"
	"github.com/nexustodo/backend/services"
	"net/http"
)

type DeviceHandler struct {
	deviceService *services.DeviceService
}

func NewDeviceHandler(deviceService *services.DeviceService) *DeviceHandler {
	return &DeviceHandler{deviceService: deviceService}
}

func (h *DeviceHandler) RegisterDevice(c *gin.Context) {
	var req schemas.DeviceRegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
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

	device, user, err := h.deviceService.RegisterDevice(req.DeviceID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, schemas.ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INTERNAL_ERROR",
				Message: "服务器内部错误",
			},
		})
		return
	}

	c.JSON(http.StatusOK, schemas.DeviceRegisterResponse{
		DeviceID: device.ID,
		UserID:   user.ID,
		Message:  "注册成功",
	})
}

func (h *DeviceHandler) GetDeviceStatus(c *gin.Context) {
	deviceID := c.GetHeader("X-Device-ID")
	if deviceID == "" {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
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

	device, err := h.deviceService.GetDeviceStatus(deviceID)
	if err != nil {
		c.JSON(http.StatusNotFound, schemas.ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "DEVICE_NOT_FOUND",
				Message: "设备不存在",
			},
		})
		return
	}

	c.JSON(http.StatusOK, schemas.DeviceStatusResponse{
		DeviceID:  device.ID,
		UserID:    device.UserID,
		LastSeenAt: device.LastSeenAt.Format("2006-01-02T15:04:05Z"),
	})
}
