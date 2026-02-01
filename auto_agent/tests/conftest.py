import json
import os
import socket
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request

import pytest



def _normalize_base_url(raw_url: str) -> str:
    base = raw_url.rstrip("/")
    if base.endswith("/agent"):
        base = base[:-6]
    return base


def _is_agent_available(base_url: str) -> bool:
    url = f"{base_url.rstrip('/')}/agent/chat"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status != 404
    except urllib.error.HTTPError as exc:
        return exc.code != 404
    except OSError:
        return False


def _register_device(task_api_base: str) -> tuple[str, str]:
    device_id = str(uuid.uuid4())
    url = f"{task_api_base.rstrip('/')}/device/register"
    payload = json.dumps({"deviceId": device_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("userId"), data.get("deviceId")


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_agent_server(task_api_base: str) -> tuple[str, subprocess.Popen]:
    port = _pick_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env.setdefault("TASK_API_BASE_URL", task_api_base)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "auto_agent.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    deadline = time.time() + 8
    while time.time() < deadline:
        if _is_agent_available(base_url):
            return base_url, proc
        if proc.poll() is not None:
            break
        time.sleep(0.2)

    proc.terminate()
    raise RuntimeError("Failed to start Auto Agent server for tests")


@pytest.fixture(scope="session")
def agent_server():
    raw_base = os.getenv("AUTO_AGENT_BASE_URL")
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    proc = None

    if raw_base:
        base_url = _normalize_base_url(raw_base)
        if _is_agent_available(base_url):
            yield base_url
            return

    try:
        base_url, proc = _start_agent_server(task_api_base)
        yield base_url
    finally:
        if proc and proc.poll() is None:
            proc.terminate()


@pytest.fixture(scope="session")
def agent_config(agent_server):
    base_url = agent_server
    user_id = os.getenv("AUTO_AGENT_USER_ID")
    device_id = os.getenv("AUTO_AGENT_DEVICE_ID")
    token = os.getenv("AUTO_AGENT_TOKEN", "default-token")
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")

    if not user_id or not device_id:
        try:
            user_id, device_id = _register_device(task_api_base)
        except Exception as exc:
            pytest.skip(f"Unable to register device against task API: {exc}")

    if not user_id or not device_id:
        pytest.skip("AUTO_AGENT_USER_ID/AUTO_AGENT_DEVICE_ID not set")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id,
        "X-Device-ID": device_id,
    }

    def build_url(path: str) -> str:
        return f"{base_url}{path}"

    return {
        "base_url": base_url,
        "user_id": user_id,
        "device_id": device_id,
        "headers": headers,
        "build_url": build_url,
    }
