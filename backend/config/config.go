package config

import (
	"os"
)

type Config struct {
	DatabasePath string
	Port         string
	DefaultToken string
}

var AppConfig *Config

func LoadConfig() *Config {
	if AppConfig != nil {
		return AppConfig
	}

	AppConfig = &Config{
		DatabasePath: getEnv("DATABASE_PATH", "./nexustodo.db"),
		Port:         getEnv("PORT", "8080"),
		DefaultToken: getEnv("DEFAULT_TOKEN", "default-token"),
	}

	return AppConfig
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
