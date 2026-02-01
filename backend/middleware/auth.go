package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/nexustodo/backend/config"
	"github.com/nexustodo/backend/schemas"
	"net/http"
)

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		cfg := config.LoadConfig()

		if authHeader != "Bearer "+cfg.DefaultToken {
			c.JSON(http.StatusUnauthorized, schemas.ErrorResponse{
				Error: struct {
					Code    string `json:"code"`
					Message string `json:"message"`
				}{
					Code:    "UNAUTHORIZED",
					Message: "认证失败",
				},
			})
			c.Abort()
			return
		}

		c.Next()
	}
}
