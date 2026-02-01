package services

import (
	"errors"
	"github.com/google/uuid"
	"github.com/nexustodo/backend/models"
	"gorm.io/gorm"
	"time"
)

type DeviceService struct {
	db *gorm.DB
}

func NewDeviceService(db *gorm.DB) *DeviceService {
	return &DeviceService{db: db}
}

func (s *DeviceService) RegisterDevice(deviceID string) (*models.Device, *models.User, error) {
	var device models.Device
	result := s.db.Where("id = ?", deviceID).First(&device)

	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		var user models.User
		userResult := s.db.First(&user)
		
		if errors.Is(userResult.Error, gorm.ErrRecordNotFound) {
			user = models.User{
				ID:        uuid.New().String(),
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			if err := s.db.Create(&user).Error; err != nil {
				return nil, nil, err
			}
		}

		device = models.Device{
			ID:         deviceID,
			UserID:     user.ID,
			LastSeenAt: time.Now(),
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		if err := s.db.Create(&device).Error; err != nil {
			return nil, nil, err
		}
	} else if result.Error != nil {
		return nil, nil, result.Error
	} else {
		device.LastSeenAt = time.Now()
		device.UpdatedAt = time.Now()
		if err := s.db.Save(&device).Error; err != nil {
			return nil, nil, err
		}
	}

	var user models.User
	if err := s.db.Where("id = ?", device.UserID).First(&user).Error; err != nil {
		return nil, nil, err
	}

	return &device, &user, nil
}

func (s *DeviceService) GetDeviceStatus(deviceID string) (*models.Device, error) {
	var device models.Device
	result := s.db.Where("id = ?", deviceID).First(&device)
	
	if errors.Is(result.Error, gorm.ErrRecordNotFound) {
		return nil, errors.New("设备不存在")
	}
	
	if result.Error != nil {
		return nil, result.Error
	}

	device.LastSeenAt = time.Now()
	device.UpdatedAt = time.Now()
	if err := s.db.Save(&device).Error; err != nil {
		return nil, err
	}

	return &device, nil
}
