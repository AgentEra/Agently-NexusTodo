"""Contract test for GET /agent/chat/stream (SSE).

Required env:
- AUTO_AGENT_BASE_URL (default http://localhost:8080)
- AUTO_AGENT_USER_ID
- AUTO_AGENT_DEVICE_ID
Optional env:
- AUTO_AGENT_TOKEN (default default-token)
- AUTO_AGENT_ENABLE_SSE_TEST=1 to enable this test
"""

import json
import os
import urllib.parse
import urllib.request

import pytest


@pytest.mark.integration
def test_sse_stream_contract(agent_config):
    if os.getenv("AUTO_AGENT_ENABLE_SSE_TEST") != "1":
        pytest.skip("Set AUTO_AGENT_ENABLE_SSE_TEST=1 to enable SSE contract test")

    params = {
        "sessionId": "",
        "userId": agent_config["user_id"],
        "deviceId": agent_config["device_id"],
        "message": "帮我创建一个任务：测试任务B，标签 demo",
    }
    query = urllib.parse.urlencode(params)
    url = agent_config["build_url"](f"/agent/chat/stream?{query}")

    req = urllib.request.Request(
        url,
        headers={"Accept": "text/event-stream", **agent_config["headers"]},
        method="GET",
    )

    allowed_events = {"delta", "action", "execution", "done", "error"}
    seen_events = set()
    last_event = None

    with urllib.request.urlopen(req, timeout=15) as resp:
        content_type = resp.getheader("Content-Type", "")
        assert content_type.startswith("text/event-stream")

        for idx, raw in enumerate(resp):
            if idx > 200:
                pytest.fail("SSE stream did not finish within 200 lines")

            line = raw.decode("utf-8").strip()
            if not line:
                continue

            if line.startswith("event:"):
                last_event = line.split(":", 1)[1].strip()
                assert last_event in allowed_events
                seen_events.add(last_event)
                if last_event == "error":
                    pytest.fail("SSE returned error event")
                continue

            if line.startswith("data:"):
                data_str = line.split(":", 1)[1].strip()
                if last_event == "done":
                    payload = json.loads(data_str)
                    assert isinstance(payload.get("assistantMessage"), str)
                    break

    assert "done" in seen_events
