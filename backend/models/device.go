package models

import (
	"time"

	"gorm.io/gorm"
)

type Device struct {
	ID         string         `gorm:"type:varchar(36);primaryKey" json:"id"`
	UserID     string         `gorm:"type:varchar(36);not null;index" json:"userId"`
	LastSeenAt time.Time      `gorm:"not null;default:CURRENT_TIMESTAMP" json:"lastSeenAt"`
	CreatedAt  time.Time      `gorm:"not null;default:CURRENT_TIMESTAMP" json:"createdAt"`
	UpdatedAt  time.Time      `gorm:"not null;default:CURRENT_TIMESTAMP" json:"updatedAt"`
	User       User           `gorm:"foreignKey:UserID" json:"user,omitempty"`
	DeletedAt  gorm.DeletedAt `gorm:"index" json:"-"`
}

func (Device) TableName() string {
	return "devices"
}
