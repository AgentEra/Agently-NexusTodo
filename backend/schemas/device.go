package schemas

type DeviceRegisterRequest struct {
	DeviceID string `json:"deviceId" binding:"required,uuid"`
}

type DeviceRegisterResponse struct {
	DeviceID string `json:"deviceId"`
	UserID   string `json:"userId"`
	Message  string `json:"message"`
}

type DeviceStatusResponse struct {
	DeviceID  string `json:"deviceId"`
	UserID    string `json:"userId"`
	LastSeenAt string `json:"lastSeenAt"`
}
