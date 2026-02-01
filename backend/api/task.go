package api

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/nexustodo/backend/schemas"
	"github.com/nexustodo/backend/services"
	"github.com/nexustodo/backend/utils"
)

type TaskHandler struct {
	taskService *services.TaskService
}

func NewTaskHandler(taskService *services.TaskService) *TaskHandler {
	return &TaskHandler{taskService: taskService}
}

func (h *TaskHandler) GetTasks(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_REQUEST",
				Message: "用户ID不能为空",
			},
		})
		return
	}

	status := c.Query("status")
	tagsStr := c.Query("tags")

	var tags []string
	if tagsStr != "" {
		tags = strings.Split(tagsStr, ",")
		for i := range tags {
			tags[i] = strings.TrimSpace(tags[i])
		}
	}

	tasks, err := h.taskService.GetTasks(userID, status, tags)
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

	c.JSON(http.StatusOK, utils.ModelToTaskResponseList(tasks))
}

func (h *TaskHandler) GetTask(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	taskID := c.Param("taskId")

	task, err := h.taskService.GetTaskByID(taskID)
	if err != nil {
		c.JSON(http.StatusNotFound, schemas.ErrorResponse{
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

	if task.UserID != userID {
		c.JSON(http.StatusForbidden, schemas.ErrorResponse{
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

	c.JSON(http.StatusOK, utils.ModelToTaskResponse(task))
}

func (h *TaskHandler) CreateTask(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	if userID == "" {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
			Error: struct {
				Code    string `json:"code"`
				Message string `json:"message"`
			}{
				Code:    "INVALID_REQUEST",
				Message: "用户ID不能为空",
			},
		})
		return
	}

	var req schemas.TaskCreateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
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

	if req.Title == "" || strings.TrimSpace(req.Title) == "" {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
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

	task, err := h.taskService.CreateTask(userID, req.Title, req.Description, req.Tags)
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

	c.JSON(http.StatusCreated, utils.ModelToTaskResponse(task))
}

func (h *TaskHandler) UpdateTask(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	taskID := c.Param("taskId")

	var req schemas.TaskUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, schemas.ErrorResponse{
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

	var title, description, status *string
	if req.Title != "" {
		title = &req.Title
	}
	if req.Description != "" {
		description = &req.Description
	}
	if req.Status != "" {
		status = &req.Status
	}

	task, err := h.taskService.UpdateTask(taskID, userID, title, description, status, req.Tags)
	if err != nil {
		if err.Error() == "任务不存在" {
			c.JSON(http.StatusNotFound, schemas.ErrorResponse{
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
		if err.Error() == "无权访问该任务" {
			c.JSON(http.StatusForbidden, schemas.ErrorResponse{
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

	c.JSON(http.StatusOK, utils.ModelToTaskResponse(task))
}

func (h *TaskHandler) DeleteTask(c *gin.Context) {
	userID := c.GetHeader("X-User-ID")
	taskID := c.Param("taskId")

	err := h.taskService.DeleteTask(taskID, userID)
	if err != nil {
		if err.Error() == "任务不存在" {
			c.JSON(http.StatusNotFound, schemas.ErrorResponse{
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
		if err.Error() == "无权访问该任务" {
			c.JSON(http.StatusForbidden, schemas.ErrorResponse{
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

	c.JSON(http.StatusOK, schemas.SuccessResponse{
		Message: "删除成功",
	})
}
