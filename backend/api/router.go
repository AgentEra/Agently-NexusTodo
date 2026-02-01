package api

import (
	"github.com/gin-gonic/gin"
	"github.com/nexustodo/backend/middleware"
	"github.com/nexustodo/backend/services"
)

func SetupRouter(deviceService *services.DeviceService, taskService *services.TaskService) *gin.Engine {
	router := gin.New()
	
	router.Use(middleware.CORSMiddleware())
	router.Use(gin.Recovery())

	api := router.Group("/api")
	{
		device := api.Group("/device")
		{
			device.POST("/register", NewDeviceHandler(deviceService).RegisterDevice)
			device.GET("/status", middleware.AuthMiddleware(), NewDeviceHandler(deviceService).GetDeviceStatus)
		}

		task := api.Group("/tasks")
		task.Use(middleware.AuthMiddleware())
		{
			task.GET("", NewTaskHandler(taskService).GetTasks)
			task.POST("", NewTaskHandler(taskService).CreateTask)
			task.GET("/:taskId", NewTaskHandler(taskService).GetTask)
			task.PUT("/:taskId", NewTaskHandler(taskService).UpdateTask)
			task.DELETE("/:taskId", NewTaskHandler(taskService).DeleteTask)
		}
	}

	return router
}
