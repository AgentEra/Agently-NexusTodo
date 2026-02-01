package schemas

type TaskCreateRequest struct {
	Title       string   `json:"title" binding:"required"`
	Description string   `json:"description"`
	Tags        []string `json:"tags"`
}

type TaskUpdateRequest struct {
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Status      string   `json:"status" binding:"omitempty,oneof=待办 进行中 已完成 已延期 已取消"`
	Tags        []string `json:"tags"`
}

type TaskResponse struct {
	TaskID      string   `json:"taskId"`
	UserID      string   `json:"userId"`
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Status      string   `json:"status"`
	Tags        []string `json:"tags"`
	CreatedAt   string   `json:"createdAt"`
	UpdatedAt   string   `json:"updatedAt"`
}

type SuccessResponse struct {
	Message string `json:"message"`
}

type ErrorResponse struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}
