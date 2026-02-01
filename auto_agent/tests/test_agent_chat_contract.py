"""Contract tests for POST /agent/chat.

Required env:
- AUTO_AGENT_BASE_URL (default http://localhost:8080)
- AUTO_AGENT_USER_ID
- AUTO_AGENT_DEVICE_ID
Optional env:
- AUTO_AGENT_TOKEN (default default-token)
"""

import json
import urllib.error
import urllib.request

ALLOWED_INTENTS = {"create", "list", "detail", "update", "delete", "clarify"}
ALLOWED_EXECUTION_STATUS = {"success", "failed", "skipped"}


def _read_json_or_text(resp) -> object:
    raw = resp.read().decode("utf-8")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 10):
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _read_json_or_text(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, _read_json_or_text(exc)


def test_chat_contract(agent_config):
    url = agent_config["build_url"]("/agent/chat")
    payload = {
        "userId": agent_config["user_id"],
        "deviceId": agent_config["device_id"],
        "messages": [
            {"role": "user", "content": "帮我创建一个任务：测试任务A，标签 demo"}
        ],
    }

    status, data = _post_json(url, payload, agent_config["headers"])
    assert status == 200
    assert isinstance(data, dict)

    assert isinstance(data.get("sessionId"), str) and data.get("sessionId")
    assert isinstance(data.get("assistantMessage"), str)

    action = data.get("action")
    execution = data.get("execution")
    assert isinstance(action, dict)
    assert isinstance(execution, dict)

    intent = action.get("intent")
    assert intent in ALLOWED_INTENTS

    status_value = execution.get("status")
    assert status_value in ALLOWED_EXECUTION_STATUS
    if intent == "clarify":
        assert status_value == "skipped"
    else:
        assert status_value != "skipped"


def test_chat_missing_auth_headers_returns_error(agent_config):
    url = agent_config["build_url"]("/agent/chat")
    payload = {
        "userId": agent_config["user_id"],
        "deviceId": agent_config["device_id"],
        "messages": [{"role": "user", "content": "列出任务"}],
    }

    status, _data = _post_json(url, payload, headers={})
    assert status in {400, 401, 403}


def test_chat_missing_messages_returns_400(agent_config):
    url = agent_config["build_url"]("/agent/chat")
    payload = {
        "userId": agent_config["user_id"],
        "deviceId": agent_config["device_id"],
    }

    status, _data = _post_json(url, payload, agent_config["headers"])
    assert status in {400, 422}
