package main

import (
	"fmt"
	"github.com/nexustodo/backend/api"
	"github.com/nexustodo/backend/config"
	"github.com/nexustodo/backend/models"
	"github.com/nexustodo/backend/services"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"log"
)

func main() {
	cfg := config.LoadConfig()

	db, err := gorm.Open(sqlite.Open(cfg.DatabasePath), &gorm.Config{})
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	if err := db.AutoMigrate(&models.User{}, &models.Device{}, &models.Task{}); err != nil {
		log.Fatalf("Failed to migrate database: %v", err)
	}

	deviceService := services.NewDeviceService(db)
	taskService := services.NewTaskService(db)

	router := api.SetupRouter(deviceService, taskService)

	fmt.Printf("Server starting on port %s...\n", cfg.Port)
	if err := router.Run(":" + cfg.Port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
