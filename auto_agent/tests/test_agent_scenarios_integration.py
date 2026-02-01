"""Integration scenarios using real Auto Agent + backend API."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid

import pytest


def _read_json(resp):
    raw = resp.read().decode("utf-8")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 60):
    body = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _read_json(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, _read_json(exc)


def _api_request(base_url: str, path: str, method: str, headers: dict, body=None, timeout: int = 10):
    url = f"{base_url.rstrip('/')}{path}"
    req_headers = {"Content-Type": "application/json", **headers}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, _read_json(resp)


def _create_task(base_url: str, headers: dict, title: str, tags=None, status=None):
    payload = {"title": title}
    if tags:
        payload["tags"] = tags
    status_code, data = _api_request(base_url, "/tasks", "POST", headers, payload)
    assert status_code in {200, 201}
    task = data
    task_id = task.get("taskId") or task.get("id")
    if status and status != task.get("status"):
        _api_request(base_url, f"/tasks/{task_id}", "PUT", headers, {"status": status})
    return task_id


def _delete_task(base_url: str, headers: dict, task_id: str):
    try:
        _api_request(base_url, f"/tasks/{task_id}", "DELETE", headers, None)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise


def _list_tasks(base_url: str, headers: dict):
    status_code, data = _api_request(base_url, "/tasks", "GET", headers, None)
    assert status_code == 200
    return data or []


def _find_task_by_title(tasks: list[dict], title: str) -> dict | None:
    for task in tasks:
        if task.get("title") == title:
            return task
    return None


@pytest.mark.integration
def test_scenario_list_pending_tasks(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景待办-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))
        task_ids.append(
            _create_task(task_api_base, agent_config["headers"], f"{keyword}-B", status="已完成")
        )

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"请列出包含{keyword}的待办任务",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"
        tasks = data.get("execution", {}).get("result") or []
        titles = [task.get("title") for task in tasks]
        assert any(keyword in title for title in titles if title)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_delete_by_keyword(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景删除-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-B"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"删除所有包含{keyword}的任务",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        assert all(keyword not in (task.get("title") or "") for task in tasks)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_bulk_update(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景更新-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-B"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"把包含{keyword}的任务都标记为已完成",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        filtered = [task for task in tasks if keyword in (task.get("title") or "")]
        assert filtered
        assert all(task.get("status") == "已完成" for task in filtered)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_list_unfinished_by_keyword(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景未完成-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-B", status="进行中"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-C", status="已完成"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-D", status="已延期"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"列出包含{keyword}的未完成任务",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"
        tasks = data.get("execution", {}).get("result") or []
        assert tasks
        assert all(task.get("status") != "已完成" for task in tasks)
        assert any(keyword in (task.get("title") or "") for task in tasks)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
@pytest.mark.parametrize("verb", ["清理掉", "移除"])
def test_scenario_delete_by_synonym(agent_config, verb):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景删除同义-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-B"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"{verb}包含{keyword}的任务",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        assert all(keyword not in (task.get("title") or "") for task in tasks)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_update_title(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景改名-{uuid.uuid4().hex[:8]}"
    new_title = f"已改名-{uuid.uuid4().hex[:6]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"把{keyword}-A任务改名为{new_title}",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        assert any(task.get("title") == new_title for task in tasks)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_detail_by_keyword(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    keyword = f"场景详情-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], f"{keyword}-A"))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"查看{keyword}-A任务详情",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        result = data.get("execution", {}).get("result")
        if isinstance(result, list):
            assert any(keyword in (task.get("title") or "") for task in result)
        elif isinstance(result, dict):
            assert keyword in (result.get("title") or "")
        else:
            pytest.fail("Unexpected execution result format")
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_create_with_tags(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    title = f"场景创建标签-{uuid.uuid4().hex[:8]}"
    tag = f"tag-{uuid.uuid4().hex[:6]}"
    task_ids = []
    try:
        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"请帮我创建一个任务：{title}，标签为{tag}",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        task = _find_task_by_title(tasks, title)
        assert task is not None
        assert tag in (task.get("tags") or [])
        task_id = task.get("taskId") or task.get("id")
        if task_id:
            task_ids.append(task_id)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_list_by_tag(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    tag = f"tag-query-{uuid.uuid4().hex[:6]}"
    task_ids = []
    try:
        task_ids.append(
            _create_task(
                task_api_base,
                agent_config["headers"],
                f"场景标签查询-{uuid.uuid4().hex[:6]}",
                tags=[tag],
            )
        )
        task_ids.append(
            _create_task(
                task_api_base,
                agent_config["headers"],
                f"场景标签查询-{uuid.uuid4().hex[:6]}",
                tags=[tag],
            )
        )
        task_ids.append(
            _create_task(
                task_api_base,
                agent_config["headers"],
                f"场景标签查询-{uuid.uuid4().hex[:6]}",
            )
        )

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"列出标签为{tag}的任务",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"
        tasks = data.get("execution", {}).get("result") or []
        assert tasks
        assert all(tag in (task.get("tags") or []) for task in tasks)
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_mark_done(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    title = f"场景完成-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], title))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"把{title}任务标记为已完成",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        task = _find_task_by_title(tasks, title)
        assert task is not None
        assert task.get("status") == "已完成"
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_add_tag(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    title = f"场景加标签-{uuid.uuid4().hex[:8]}"
    tag = f"tag-add-{uuid.uuid4().hex[:6]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], title))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"给{title}任务加上标签{tag}",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        task = _find_task_by_title(tasks, title)
        assert task is not None
        assert tag in (task.get("tags") or [])
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)


@pytest.mark.integration
def test_scenario_cancel_task(agent_config):
    task_api_base = os.getenv("TASK_API_BASE_URL", "http://localhost:8080/api")
    title = f"场景取消-{uuid.uuid4().hex[:8]}"
    task_ids = []
    try:
        task_ids.append(_create_task(task_api_base, agent_config["headers"], title))

        url = agent_config["build_url"]("/agent/chat")
        payload = {
            "userId": agent_config["user_id"],
            "deviceId": agent_config["device_id"],
            "messages": [
                {
                    "role": "user",
                    "content": f"把{title}任务标记为已取消",
                }
            ],
        }
        status, data = _post_json(url, payload, agent_config["headers"], timeout=60)
        assert status == 200
        assert data.get("execution", {}).get("status") == "success"

        tasks = _list_tasks(task_api_base, agent_config["headers"])
        task = _find_task_by_title(tasks, title)
        assert task is not None
        assert task.get("status") == "已取消"
    finally:
        for task_id in task_ids:
            _delete_task(task_api_base, agent_config["headers"], task_id)
