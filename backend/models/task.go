package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"

	"gorm.io/gorm"
)

type StringArray []string

func (sa *StringArray) Scan(value interface{}) error {
	if value == nil {
		*sa = nil
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("failed to unmarshal StringArray value")
	}
	return json.Unmarshal(bytes, sa)
}

func (sa StringArray) Value() (driver.Value, error) {
	if sa == nil {
		return nil, nil
	}
	return json.Marshal(sa)
}

type Task struct {
	ID          string         `gorm:"type:varchar(36);primaryKey" json:"id"`
	UserID      string         `gorm:"type:varchar(36);not null;index" json:"userId"`
	Title       string         `gorm:"type:varchar(255);not null" json:"title"`
	Description string         `gorm:"type:text" json:"description"`
	Status      string         `gorm:"type:varchar(20);not null;default:'待办'" json:"status"`
	Tags        StringArray    `gorm:"type:text" json:"tags"`
	CreatedAt   time.Time      `gorm:"not null;default:CURRENT_TIMESTAMP" json:"createdAt"`
	UpdatedAt   time.Time      `gorm:"not null;default:CURRENT_TIMESTAMP" json:"updatedAt"`
	User        User           `gorm:"foreignKey:UserID" json:"user,omitempty"`
	DeletedAt   gorm.DeletedAt `gorm:"index" json:"-"`
}

func (Task) TableName() string {
	return "tasks"
}
