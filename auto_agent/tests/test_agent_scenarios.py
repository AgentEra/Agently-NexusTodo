import pytest

from auto_agent.agent_core import AgentCore, SessionStore
from auto_agent.models import ChatMessage
from auto_agent.task_api import ApiResult


class FakeTaskApi:
    def __init__(self, tasks):
        self.tasks = tasks

    async def list_tasks(self, headers, status=None, tags=None):
        tasks = list(self.tasks)
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        if tags:
            required = set(tags)
            tasks = [
                task
                for task in tasks
                if required.issubset(set(task.get("tags") or []))
            ]
        return ApiResult(ok=True, status_code=200, data=tasks)

    async def get_task(self, task_id, headers):
        for task in self.tasks:
            if task.get("taskId") == task_id:
                return ApiResult(ok=True, status_code=200, data=task)
        return ApiResult(
            ok=False,
            status_code=404,
            error={"code": "TASK_NOT_FOUND", "message": "任务不存在"},
        )

    async def create_task(self, headers, title, description, tags):
        task_id = f"task-{len(self.tasks) + 1}"
        task = {
            "taskId": task_id,
            "title": title,
            "description": description or "",
            "status": "待办",
            "tags": tags or [],
        }
        self.tasks.append(task)
        return ApiResult(ok=True, status_code=201, data=task)

    async def update_task(self, task_id, headers, title, description, status, tags):
        for task in self.tasks:
            if task.get("taskId") == task_id:
                if title is not None:
                    task["title"] = title
                if description is not None:
                    task["description"] = description
                if status is not None:
                    task["status"] = status
                if tags is not None:
                    task["tags"] = tags
                return ApiResult(ok=True, status_code=200, data=task)
        return ApiResult(
            ok=False,
            status_code=404,
            error={"code": "TASK_NOT_FOUND", "message": "任务不存在"},
        )

    async def delete_task(self, task_id, headers):
        for idx, task in enumerate(self.tasks):
            if task.get("taskId") == task_id:
                self.tasks.pop(idx)
                return ApiResult(ok=True, status_code=200, data={"taskId": task_id})
        return ApiResult(
            ok=False,
            status_code=404,
            error={"code": "TASK_NOT_FOUND", "message": "任务不存在"},
        )


class StepPlanner:
    def __init__(self, steps):
        self.steps = steps
        self.index = 0

    async def plan(self, _conversation, _scratchpad):
        if self.index >= len(self.steps):
            return {
                "thought": "",
                "action": "final",
                "action_input": {},
                "final": "已完成。",
            }
        step = self.steps[self.index]
        self.index += 1
        return step


@pytest.mark.asyncio
async def test_list_pending_tasks_stops_after_query():
    tasks = [
        {
            "taskId": "1",
            "title": "任务A",
            "description": "",
            "status": "待办",
            "tags": [],
        },
        {
            "taskId": "2",
            "title": "任务B",
            "description": "",
            "status": "已完成",
            "tags": [],
        },
    ]
    planner = StepPlanner(
        [
            {
                "thought": "列出未完成任务",
                "action": "list_tasks",
                "action_input": {
                    "query": {"status_list": ["待办", "进行中", "已延期"]}
                },
                "final": "",
            }
        ]
    )
    agent = AgentCore(FakeTaskApi(tasks), SessionStore(6), planner)

    result = await agent.handle_chat(
        None,
        [ChatMessage(role="user", content="我有哪些待办任务")],
        headers={},
    )

    assert result["execution"]["status"] == "success"
    assert result["action"]["intent"] == "list"
    assert "结论" in result["assistantMessage"]


@pytest.mark.asyncio
async def test_delete_task_by_title():
    tasks = [
        {
            "taskId": "1",
            "title": "测试任务A",
            "description": "",
            "status": "待办",
            "tags": [],
        },
        {
            "taskId": "2",
            "title": "其他任务",
            "description": "",
            "status": "待办",
            "tags": [],
        },
    ]
    planner = StepPlanner(
        [
            {
                "thought": "删除测试任务A",
                "action": "delete_task",
                "action_input": {"title": "测试任务A"},
                "final": "",
            }
        ]
    )
    agent = AgentCore(FakeTaskApi(tasks), SessionStore(6), planner)

    result = await agent.handle_chat(
        None,
        [ChatMessage(role="user", content="删除测试任务A")],
        headers={},
    )

    assert result["execution"]["status"] == "success"
    assert all(task["title"] != "测试任务A" for task in tasks)


@pytest.mark.asyncio
async def test_bulk_update_tasks_by_status():
    tasks = [
        {
            "taskId": "1",
            "title": "任务A",
            "description": "",
            "status": "待办",
            "tags": ["work"],
        },
        {
            "taskId": "2",
            "title": "任务B",
            "description": "",
            "status": "待办",
            "tags": ["home"],
        },
    ]
    planner = StepPlanner(
        [
            {
                "thought": "批量完成待办任务",
                "action": "update_task",
                "action_input": {
                    "status": "已完成",
                    "bulk": True,
                    "query": {"status": "待办"},
                },
                "final": "",
            }
        ]
    )
    agent = AgentCore(FakeTaskApi(tasks), SessionStore(6), planner)

    result = await agent.handle_chat(
        None,
        [ChatMessage(role="user", content="把待办任务都标记完成")],
        headers={},
    )

    assert result["execution"]["status"] == "success"
    assert all(task["status"] == "已完成" for task in tasks)


@pytest.mark.asyncio
async def test_delete_tasks_by_recent_selection_indices():
    tasks = [
        {
            "taskId": "11111111-1111-1111-1111-111111111111",
            "title": "测试任务A",
            "description": "",
            "status": "待办",
            "tags": [],
        },
        {
            "taskId": "22222222-2222-2222-2222-222222222222",
            "title": "场景任务B",
            "description": "",
            "status": "待办",
            "tags": [],
        },
        {
            "taskId": "33333333-3333-3333-3333-333333333333",
            "title": "正式任务C",
            "description": "",
            "status": "待办",
            "tags": [],
        },
    ]
    planner = StepPlanner(
        [
            {
                "thought": "列出未完成任务",
                "action": "list_tasks",
                "action_input": {
                    "query": {"status_list": ["待办", "进行中", "已延期"]}
                },
                "final": "",
            },
            {
                "thought": "",
                "action": "final",
                "action_input": {},
                "final": "已列出任务。",
            },
            {
                "thought": "删除明显是测试任务的条目",
                "action": "delete_task",
                "action_input": {"selection_indices": [1, 2]},
                "final": "",
            },
        ]
    )
    agent = AgentCore(FakeTaskApi(tasks), SessionStore(6), planner)

    first = await agent.handle_chat(
        None,
        [ChatMessage(role="user", content="列出未完成任务")],
        headers={},
    )
    session_id = first["sessionId"]

    second = await agent.handle_chat(
        session_id,
        [ChatMessage(role="user", content="删除这些任务中明显是测试任务的")],
        headers={},
    )

    assert second["execution"]["status"] == "success"
    remaining_titles = [task["title"] for task in tasks]
    assert remaining_titles == ["正式任务C"]
