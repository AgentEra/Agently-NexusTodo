package utils

import (
	"github.com/nexustodo/backend/models"
	"github.com/nexustodo/backend/schemas"
	"time"
)

func ModelToTaskResponse(task *models.Task) *schemas.TaskResponse {
	return &schemas.TaskResponse{
		TaskID:      task.ID,
		UserID:      task.UserID,
		Title:       task.Title,
		Description: task.Description,
		Status:      task.Status,
		Tags:        []string(task.Tags),
		CreatedAt:   task.CreatedAt.Format(time.RFC3339),
		UpdatedAt:   task.UpdatedAt.Format(time.RFC3339),
	}
}

func ModelToTaskResponseList(tasks []*models.Task) []schemas.TaskResponse {
	responses := make([]schemas.TaskResponse, len(tasks))
	for i, task := range tasks {
		responses[i] = *ModelToTaskResponse(task)
	}
	return responses
}
