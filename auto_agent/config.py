from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
import os


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Settings:
    def __init__(self) -> None:
        # self.llm_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        # self.llm_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        # self.llm_model_type = os.getenv("OLLAMA_MODEL_TYPE", "chat")
        self.llm_base_url = os.getenv("DEEPSEEK_BASE_URL", "http://localhost:11434/v1")
        self.llm_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.llm_api_key = os.getenv("DEEPSEEK_API_KEY", "nothing")
        self.llm_model_type = os.getenv("DEEPSEEK_MODEL_TYPE", "chat")
        self.task_api_base_url = os.getenv(
            "TASK_API_BASE_URL", "http://localhost:8080/api"
        )
        self.request_timeout = _get_float("TASK_API_TIMEOUT", 60.0)
        self.max_session_messages = _get_int("AGENT_MAX_SESSION_MESSAGES", 12)
        self.react_max_steps = _get_int("REACT_MAX_STEPS", 10)
        self.sse_chunk_size = _get_int("SSE_CHUNK_SIZE", 20)


settings = Settings()
