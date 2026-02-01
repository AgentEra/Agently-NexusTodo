package services

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/nexustodo/backend/models"
	"gorm.io/gorm"
)

type TaskService struct {
	db *gorm.DB
}

func NewTaskService(db *gorm.DB) *TaskService {
	return &TaskService{db: db}
}

func (s *TaskService) GetTasks(userID string, status string, tags []string) ([]*models.Task, error) {
	var tasks []*models.Task
	query := s.db.Where("user_id = ?", userID)

	if status != "" {
		query = query.Where("status = ?", status)
	}

	if len(tags) > 0 {
		for _, tag := range tags {
			query = query.Where("json_array_length(tags) > 0 AND json_extract(tags, '$') LIKE ?", "%"+tag+"%")
		}
	}

	if err := query.Order("created_at ASC").Find(&tasks).Error; err != nil {
		return nil, err
	}

	return tasks, nil
}

func (s *TaskService) GetTaskByID(taskID string) (*models.Task, error) {
	var task models.Task
	result := s.db.Where("id = ?", taskID).First(&task)

	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		return nil, errors.New("任务不存在")
	}

	if result.Error != nil {
		return nil, result.Error
	}

	return &task, nil
}

func (s *TaskService) CreateTask(userID string, title string, description string, tags []string) (*models.Task, error) {
	task := models.Task{
		ID:          uuid.New().String(),
		UserID:      userID,
		Title:       title,
		Description: description,
		Status:      "待办",
		Tags:        models.StringArray(tags),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	if err := s.db.Create(&task).Error; err != nil {
		return nil, err
	}

	return &task, nil
}

func (s *TaskService) UpdateTask(taskID string, userID string, title *string, description *string, status *string, tags []string) (*models.Task, error) {
	var task models.Task
	result := s.db.Where("id = ?", taskID).First(&task)

	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		return nil, errors.New("任务不存在")
	}

	if result.Error != nil {
		return nil, result.Error
	}

	if task.UserID != userID {
		return nil, errors.New("无权访问该任务")
	}

	updates := make(map[string]interface{})
	updates["updated_at"] = time.Now()

	if title != nil {
		updates["title"] = *title
	}
	if description != nil {
		updates["description"] = *description
	}
	if status != nil {
		updates["status"] = *status
	}
	if tags != nil {
		updates["tags"] = models.StringArray(tags)
	}

	if err := s.db.Model(&task).Updates(updates).Error; err != nil {
		return nil, err
	}

	if err := s.db.Where("id = ?", taskID).First(&task).Error; err != nil {
		return nil, err
	}

	return &task, nil
}

func (s *TaskService) DeleteTask(taskID string, userID string) error {
	var task models.Task
	result := s.db.Where("id = ?", taskID).First(&task)

	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		return errors.New("任务不存在")
	}

	if result.Error != nil {
		return result.Error
	}

	if task.UserID != userID {
		return errors.New("无权访问该任务")
	}

	if err := s.db.Delete(&task).Error; err != nil {
		return err
	}

	return nil
}
