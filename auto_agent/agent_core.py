from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from agently import Agently

from .config import settings
from .models import ChatMessage
from .task_api import ApiResult, TaskApi


VALID_STATUSES = ["待办", "进行中", "已完成", "已延期", "已取消"]

ACTION_TO_INTENT = {
    "list_tasks": "list",
    "get_task": "detail",
    "create_task": "create",
    "update_task": "update",
    "delete_task": "delete",
}


@dataclass
class SessionState:
    session_id: str
    messages: list[ChatMessage]
    updated_at: datetime
    pending_candidates: list[dict[str, Any]] = field(default_factory=list)
    pending_intent: Optional[str] = None
    recent_candidates: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    def __init__(self, max_messages: int) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()
        self._max_messages = max_messages

    async def get_or_create(self, session_id: Optional[str]) -> SessionState:
        async with self._lock:
            if session_id and session_id in self._sessions:
                state = self._sessions[session_id]
                state.updated_at = datetime.utcnow()
                return state
            new_id = session_id or str(uuid.uuid4())
            state = SessionState(
                session_id=new_id, messages=[], updated_at=datetime.utcnow()
            )
            self._sessions[new_id] = state
            return state

    async def replace_messages(
        self, session_id: str, messages: list[ChatMessage]
    ) -> None:
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionState(
                    session_id=session_id,
                    messages=messages[-self._max_messages :],
                    updated_at=datetime.utcnow(),
                )
                return
            state = self._sessions[session_id]
            state.messages = messages[-self._max_messages :]
            state.updated_at = datetime.utcnow()

    async def append_messages(
        self, session_id: str, messages: list[ChatMessage]
    ) -> None:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                state = SessionState(
                    session_id=session_id, messages=[], updated_at=datetime.utcnow()
                )
                self._sessions[session_id] = state
            state.messages.extend(messages)
            state.messages = state.messages[-self._max_messages :]
            state.updated_at = datetime.utcnow()

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                return []
            return list(state.messages)

    async def set_pending(
        self, session_id: str, intent: Optional[str], candidates: list[dict[str, Any]]
    ) -> None:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                state = SessionState(
                    session_id=session_id, messages=[], updated_at=datetime.utcnow()
                )
                self._sessions[session_id] = state
            state.pending_candidates = candidates
            state.pending_intent = intent
            state.updated_at = datetime.utcnow()

    async def clear_pending(self, session_id: str) -> None:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                return
            state.pending_candidates = []
            state.pending_intent = None
            state.updated_at = datetime.utcnow()

    async def get_pending(
        self, session_id: str
    ) -> tuple[Optional[str], list[dict[str, Any]]]:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                return None, []
            return state.pending_intent, list(state.pending_candidates)

    async def set_recent(self, session_id: str, candidates: list[dict[str, Any]]) -> None:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                state = SessionState(
                    session_id=session_id, messages=[], updated_at=datetime.utcnow()
                )
                self._sessions[session_id] = state
            state.recent_candidates = candidates
            state.updated_at = datetime.utcnow()

    async def clear_recent(self, session_id: str) -> None:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                return
            state.recent_candidates = []
            state.updated_at = datetime.utcnow()

    async def get_recent(self, session_id: str) -> list[dict[str, Any]]:
        async with self._lock:
            state = self._sessions.get(session_id)
            if not state:
                return []
            return list(state.recent_candidates)


class ReActPlanner:
    def __init__(self) -> None:
        Agently.set_settings(
            "OpenAICompatible",
            {
                "base_url": settings.llm_base_url,
                "model": settings.llm_model,
                "api_key": settings.llm_api_key,
                "model_type": settings.llm_model_type,
                "request_options": {"temperature": 0},
            },
        )
        self._agent = Agently.create_agent()
        self._agent.set_agent_prompt(
            "system",
            (
                "你是 NexusTodo 对话式任务助手，使用 ReAct 工作流（思考->行动->观察）。\n"
                "请只输出 JSON，不要输出多余文本。\n"
                "action 只能是 list_tasks|get_task|create_task|update_task|delete_task|final。\n"
                "当信息不足时，可以通过 list_tasks/get_task 获取更多信息。\n"
                "若用户意图是删除/更新，且筛选条件明确，请直接调用 delete_task/update_task，\n"
                "仅在目标不明确时才使用 list_tasks 做候选筛选。\n"
                "写操作不需要二次确认。\n"
                "status 只允许：待办/进行中/已完成/已延期/已取消。\n"
                "若用户说“未完成/未结束/未办完”，请将 action_input.query.status_list 设为"
                "[\"待办\",\"进行中\",\"已延期\"]。\n"
                "若用户表达“完成/搞定/做完/标记为完成/已完成”，请使用 update_task 并将"
                "action_input.status 设为“已完成”。\n"
                "若用户表达“取消/不做了/终止/作废”，请使用 update_task 并将"
                "action_input.status 设为“已取消”。\n"
                "若用户表达“延期/推迟”，请使用 update_task 并将 action_input.status 设为“已延期”。\n"
                "若用户表达“开始/进行中/处理中”，请使用 update_task 并将 action_input.status 设为“进行中”。\n"
                "若用户表达“改名/重命名/改标题/修改任务名”，请使用 update_task 并将"
                "action_input.title 设置为新标题，同时将 action_input.query.keyword 设置为旧标题"
                "（不要带“任务”等后缀）。\n"
                "若用户表达“加标签/打标签/贴标签/标签为X”，请将 X 写入 action_input.tags。\n"
                "若用户表达“删除/移除/清理/清空/清除/处理掉”，请使用 delete_task。\n"
                "如果 list_tasks 只是用于定位待更新/删除的目标，请在下一步继续执行"
                "update_task/delete_task，不要直接结束。\n"
                "taskId 必须是 UUID，若不确定请留空。\n"
                "若用户说“这些/上述/刚才列出的任务”，请在 action_input.selection_indices 中给出序号列表。\n"
                "若用户表达“全部/所有/批量”，请在 action_input.bulk 中设置 true。\n"
                "若用户表达“包含/带有/含有/名字中有/标题含有 X”，请将 X 填到 action_input.query.keyword。\n"
                "若用户选择候选序号（如 删除3/选择2），请输出 action_input.selection_index 为数字。\n"
            ),
        )

    async def plan(self, conversation: str, scratchpad: str) -> dict[str, Any]:
        prompt = (
            "请返回 JSON：\n"
            "{\n"
            '  "thought": "简短推理",\n'
            '  "action": "list_tasks|get_task|create_task|update_task|delete_task|final",\n'
            '  "action_input": {\n'
            '    "taskId": "string?",\n'
            '    "title": "string?",\n'
            '    "description": "string?",\n'
            '    "status": "待办|进行中|已完成|已延期|已取消?",\n'
            '    "tags": ["string"],\n'
            '    "bulk": true,\n'
            '    "selection_index": 1,\n'
            '    "selection_indices": [1,2],\n'
            '    "query": {"status": "string?", "tags": ["string"], "keyword": "string?"}\n'
            "  },\n"
            '  "final": "当 action=final 时填写给用户的回复"\n'
            "}\n\n"
            f"对话内容：\n{conversation}\n\n"
            f"已有思考与观察：\n{scratchpad}\n"
        )

        try:
            response = await asyncio.to_thread(
                lambda: self._agent.input(prompt)
                .output(
                    {
                        "thought": (str, "reasoning"),
                        "action": (
                            str,
                            "list_tasks|get_task|create_task|update_task|delete_task|final",
                        ),
                        "action_input": {
                            "taskId": (str, "task id"),
                            "taskIds": [(str, "task id")],
                            "title": (str, "title"),
                            "description": (str, "description"),
                            "status": (str, "status"),
                            "tags": [(str, "tag")],
                            "bulk": (bool, "bulk"),
                            "selection_index": (int, "selected item index"),
                            "selection_indices": [(int, "selected item indices")],
                            "query": {
                                "status": (str, "status filter"),
                                "status_list": [(str, "status filter list")],
                                "tags": [(str, "tag filter")],
                                "keyword": (str, "keyword filter"),
                            },
                        },
                        "final": (str, "final response"),
                    }
                )
                .get_response()
            )
            data = await asyncio.to_thread(
                lambda: response.get_data(
                    ensure_keys=["thought", "action", "action_input", "final"],
                    key_style="dot",
                    max_retries=2,
                    raise_ensure_failure=False,
                )
            )
        except Exception:
            return _react_failure()

        if not isinstance(data, dict):
            return _react_failure()
        return data


class AgentCore:
    def __init__(
        self, task_api: TaskApi, session_store: SessionStore, planner: ReActPlanner
    ) -> None:
        self.task_api = task_api
        self.session_store = session_store
        self.planner = planner

    async def handle_chat(
        self,
        session_id: Optional[str],
        messages: list[ChatMessage],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        return await self._run_react(session_id, messages, headers, emit=None)

    async def handle_chat_stream(
        self,
        session_id: Optional[str],
        messages: list[ChatMessage],
        headers: dict[str, str],
    ):
        queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()

        async def emit(event_type: str, payload: dict[str, Any]) -> None:
            await queue.put((event_type, payload))

        task = asyncio.create_task(
            self._run_react(session_id, messages, headers, emit=emit)
        )

        while True:
            event_type, payload = await queue.get()
            yield event_type, payload
            if event_type in {"done", "error"}:
                break

        await task

    async def _build_conversation(self, session_id: str) -> str:
        messages = await self.session_store.get_messages(session_id)
        lines = [f"{msg.role}: {msg.content}" for msg in messages]
        pending_intent, candidates = await self.session_store.get_pending(session_id)
        if candidates:
            context_lines = [
                "system: 以下是待处理的候选任务列表（可用于选择序号或 taskId）：",
                f"system: 待处理意图: {pending_intent or '未知'}",
            ]
            for idx, task in enumerate(candidates[:8], start=1):
                title = task.get("title") or "(无标题)"
                status = task.get("status") or ""
                tags = task.get("tags") or []
                tag_text = f"标签：{', '.join(tags)}" if tags else "无标签"
                task_id = task.get("taskId") or task.get("id") or ""
                context_lines.append(
                    f"system: {idx}. {title}（{status}，{tag_text}，id: {task_id}）"
                )
            lines = context_lines + lines
        else:
            recent_candidates = await self.session_store.get_recent(session_id)
            if recent_candidates:
                context_lines = [
                    "system: 最近一次任务列表（可按序号选择/筛选）：",
                ]
                for idx, task in enumerate(recent_candidates[:8], start=1):
                    title = task.get("title") or "(无标题)"
                    status = task.get("status") or ""
                    tags = task.get("tags") or []
                    tag_text = f"标签：{', '.join(tags)}" if tags else "无标签"
                    task_id = task.get("taskId") or task.get("id") or ""
                    context_lines.append(
                        f"system: {idx}. {title}（{status}，{tag_text}，id: {task_id}）"
                    )
                lines = context_lines + lines
        return "\n".join(lines)

    async def _apply_pending_selection(
        self, session_id: str, entities: dict[str, Any]
    ) -> dict[str, Any]:
        selections = entities.get("selection_indices") or []
        selection = entities.get("selection_index")
        if selection is not None:
            selections = [selection]
        if not selections:
            return entities

        _pending_intent, candidates = await self.session_store.get_pending(session_id)
        if not candidates:
            candidates = await self.session_store.get_recent(session_id)
        if not candidates:
            return entities

        task_ids: list[str] = []
        for raw_index in selections:
            index = int(raw_index)
            if index < 1 or index > len(candidates):
                continue
            task = candidates[index - 1]
            task_id = task.get("taskId") or task.get("id")
            task_id = normalize_task_id(task_id)
            if task_id and task_id not in task_ids:
                task_ids.append(task_id)
        if not task_ids:
            return entities

        if len(task_ids) == 1:
            entities["taskId"] = task_ids[0]
        else:
            entities["taskIds"] = task_ids
        return entities

    async def _run_react(
        self,
        session_id: Optional[str],
        messages: list[ChatMessage],
        headers: dict[str, str],
        emit: Optional[callable] = None,
    ) -> dict[str, Any]:
        session = await self.session_store.get_or_create(session_id)
        if len(messages) > 1:
            await self.session_store.replace_messages(session.session_id, messages)
        else:
            await self.session_store.append_messages(session.session_id, messages)

        conversation = await self._build_conversation(session.session_id)
        scratchpad = ""
        trace_parts: list[str] = []
        last_execution: dict[str, Any] = {
            "status": "skipped",
            "result": {"reason": "no_action"},
        }
        last_action: dict[str, Any] = {"intent": "clarify", "params": {}}
        last_action_key = ""
        last_result_key = ""

        for step in range(1, settings.react_max_steps + 1):
            plan = await self.planner.plan(conversation, scratchpad)
            thought = _clean_text(plan.get("thought")) or ""
            action = str(plan.get("action", "final")).strip().lower()
            action_input = self._normalize_action_input(action, plan.get("action_input"))
            action_input = await self._apply_pending_selection(
                session.session_id, action_input
            )

            if thought:
                trace_parts.append(f"思考({step}): {thought}")
                if emit:
                    await emit(
                        "delta",
                        {
                            "sessionId": session.session_id,
                            "content": f"思考({step}): {thought}\n",
                        },
                    )

            if action == "final":
                final_text = _clean_text(plan.get("final")) or "已完成。"
                trace_parts.append(f"结论: {final_text}")
                if emit:
                    await emit(
                        "delta",
                        {
                            "sessionId": session.session_id,
                            "content": f"结论: {final_text}\n",
                        },
                    )
                assistant_message = "\n".join(trace_parts)
                await self.session_store.append_messages(
                    session.session_id,
                    [ChatMessage(role="assistant", content=assistant_message)],
                )
                if emit:
                    await emit(
                        "done",
                        {
                            "sessionId": session.session_id,
                            "assistantMessage": assistant_message,
                        },
                    )
                return {
                    "sessionId": session.session_id,
                    "assistantMessage": assistant_message,
                    "action": last_action,
                    "execution": last_execution,
                }

            if emit:
                await emit(
                    "action",
                    {
                        "step": step,
                        "action": action,
                        "intent": ACTION_TO_INTENT.get(action, "clarify"),
                        "input": action_input,
                    },
                )

            result = await self._execute_tool(
                action, action_input, session.session_id, headers
            )
            last_execution = result["execution"]
            last_action = result["action"]
            observation = result["observation"]
            trace_parts.append(f"行动({step}): {action}")
            trace_parts.append(f"观察({step}): {observation}")

            if emit:
                await emit("execution", last_execution)
                await emit(
                    "delta",
                    {
                        "sessionId": session.session_id,
                        "content": f"观察({step}): {observation}\n",
                    },
                )

            if last_execution.get("status") != "skipped":
                await self.session_store.clear_pending(session.session_id)
                if action == "list_tasks":
                    result_payload = last_execution.get("result")
                    if isinstance(result_payload, list):
                        await self.session_store.set_recent(session.session_id, result_payload)
                if action in {"create_task", "update_task", "delete_task"}:
                    await self.session_store.clear_recent(session.session_id)

            action_key = f"{action}:{safe_json(action_input)}"
            result_key = safe_json(last_execution.get("result"))

            if (
                action_key == last_action_key
                and result_key == last_result_key
                and last_execution.get("status") == "success"
            ):
                assistant_message = "\n".join(
                    trace_parts
                    + [
                        f"结论: {result.get('assistantMessage') or '已完成。'}"
                    ]
                )
                await self.session_store.append_messages(
                    session.session_id,
                    [ChatMessage(role="assistant", content=assistant_message)],
                )
                if emit:
                    await emit(
                        "done",
                        {
                            "sessionId": session.session_id,
                            "assistantMessage": assistant_message,
                        },
                    )
                return {
                    "sessionId": session.session_id,
                    "assistantMessage": assistant_message,
                    "action": last_action,
                    "execution": last_execution,
                }

            if last_execution.get("status") == "success" and action in {
                "create_task",
                "update_task",
                "delete_task",
                "get_task",
            }:
                assistant_message = "\n".join(
                    trace_parts
                    + [
                        f"结论: {result.get('assistantMessage') or '已完成。'}"
                    ]
                )
                await self.session_store.append_messages(
                    session.session_id,
                    [ChatMessage(role="assistant", content=assistant_message)],
                )
                if emit:
                    await emit(
                        "done",
                        {
                            "sessionId": session.session_id,
                            "assistantMessage": assistant_message,
                        },
                    )
                return {
                    "sessionId": session.session_id,
                    "assistantMessage": assistant_message,
                    "action": last_action,
                    "execution": last_execution,
                }

            scratchpad += (
                f"Thought: {thought}\n"
                f"Action: {action}\n"
                f"Action Input: {safe_json(action_input)}\n"
                f"Observation: {safe_json(last_execution.get('result'))}\n\n"
            )

            last_action_key = action_key
            last_result_key = result_key

        assistant_message = "\n".join(trace_parts + ["结论: 已达到最大步骤限制。"])
        await self.session_store.append_messages(
            session.session_id,
            [ChatMessage(role="assistant", content=assistant_message)],
        )
        if emit:
            await emit(
                "done",
                {
                    "sessionId": session.session_id,
                    "assistantMessage": assistant_message,
                },
            )
        return {
            "sessionId": session.session_id,
            "assistantMessage": assistant_message,
            "action": last_action,
            "execution": last_execution,
        }

    def _normalize_action_input(self, action: str, value: Any) -> dict[str, Any]:
        action_input = value if isinstance(value, dict) else {}
        query = action_input.get("query") or {}
        raw_status = action_input.get("status")
        raw_query_status = query.get("status")
        raw_query_status_list = query.get("status_list")
        title = _clean_text(action_input.get("title"))
        keyword = _clean_text(query.get("keyword"))
        if not keyword and action not in {"update_task", "create_task"}:
            keyword = title
        status_list = coerce_status_list(raw_query_status_list)
        return {
            "taskId": normalize_task_id(action_input.get("taskId")),
            "taskIds": normalize_task_ids(action_input.get("taskIds")),
            "title": title,
            "description": _clean_text(action_input.get("description")),
            "status": normalize_status(raw_status),
            "tags": coerce_list(action_input.get("tags")),
            "bulk": bool(action_input.get("bulk", False)),
            "selection_index": coerce_int(action_input.get("selection_index")),
            "selection_indices": coerce_int_list(action_input.get("selection_indices")),
            "query": {
                "status": normalize_status(raw_query_status),
                "status_list": status_list,
                "tags": coerce_list(query.get("tags")),
                "keyword": keyword,
            },
        }

    async def _execute_tool(
        self,
        action: str,
        entities: dict[str, Any],
        session_id: str,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        intent = ACTION_TO_INTENT.get(action, "clarify")
        if action == "list_tasks":
            query_payload = entities.get("query", {})
            result = await self._list_tasks(query_payload, headers)
            return self._wrap_result(intent, entities, result)
        if action == "get_task":
            if not entities.get("taskId") and not (
                entities.get("query", {}).get("keyword") or entities.get("title")
            ):
                return self._wrap_result(
                    intent,
                    entities,
                    {
                        "assistantMessage": "需要提供任务ID或关键词才能查看详情。",
                        "execution": {
                            "status": "skipped",
                            "result": {"reason": "missing_identifier"},
                        },
                    },
                )
            result = await self._detail_task(session_id, entities, headers)
            return self._wrap_result(intent, entities, result)
        if action == "create_task":
            if not entities.get("title"):
                return self._wrap_result(
                    intent,
                    entities,
                    {
                        "assistantMessage": "缺少任务标题，无法创建。",
                        "execution": {
                            "status": "skipped",
                            "result": {"reason": "missing_title"},
                        },
                    },
                )
            result = await self._create_task(entities, headers)
            return self._wrap_result(intent, entities, result)
        if action == "update_task":
            has_update_fields = bool(
                entities.get("title")
                or entities.get("description")
                or entities.get("status")
                or entities.get("tags")
            )
            if not has_update_fields:
                return self._wrap_result(
                    intent,
                    entities,
                    {
                        "assistantMessage": "缺少更新字段，无法更新。",
                        "execution": {
                            "status": "skipped",
                            "result": {"reason": "missing_updates"},
                        },
                    },
                )
            result = await self._update_task(session_id, entities, headers)
            return self._wrap_result(intent, entities, result)
        if action == "delete_task":
            if not entities.get("taskId") and not (
                entities.get("query", {}).get("keyword")
                or entities.get("query", {}).get("status")
                or entities.get("query", {}).get("tags")
                or entities.get("title")
                or entities.get("taskIds")
                or entities.get("bulk")
            ):
                return self._wrap_result(
                    intent,
                    entities,
                    {
                        "assistantMessage": "缺少任务标识或筛选条件，无法删除。",
                        "execution": {
                            "status": "skipped",
                            "result": {"reason": "missing_identifier"},
                        },
                    },
                )
            result = await self._delete_task(session_id, entities, headers)
            return self._wrap_result(intent, entities, result)

        return self._wrap_result(
            "clarify",
            entities,
            {
                "assistantMessage": "动作未识别。",
                "execution": {
                    "status": "skipped",
                    "result": {"reason": "unknown_action"},
                },
            },
        )

    def _wrap_result(
        self, intent: str, entities: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        observation = summarize_execution(result.get("execution", {}))
        return {
            "action": {"intent": intent, "params": entities},
            "execution": result.get("execution", {"status": "skipped", "result": {}}),
            "observation": observation,
            "assistantMessage": result.get("assistantMessage", ""),
        }

    async def _create_task(
        self, entities: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        result = await self.task_api.create_task(
            headers,
            title=entities.get("title"),
            description=entities.get("description"),
            tags=entities.get("tags"),
        )
        if not result.ok:
            return self._error_response(result)

        task = result.data or {}
        title = task.get("title") or entities.get("title")
        status = task.get("status") or "待办"
        tags = task.get("tags") or []
        tag_text = f"，标签：{', '.join(tags)}" if tags else ""
        assistant_message = f"已创建任务：{title}（状态：{status}{tag_text}）。"
        return {
            "assistantMessage": assistant_message,
            "execution": {"status": "success", "result": task},
        }

    async def _list_tasks(
        self, query: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        tasks, error = await self._get_tasks_for_query(query, headers)
        if error is not None:
            return self._error_response(error)

        assistant_message = format_task_list(tasks)
        return {
            "assistantMessage": assistant_message,
            "execution": {"status": "success", "result": tasks},
        }

    async def _get_tasks_for_query(
        self, query: dict[str, Any], headers: dict[str, str]
    ) -> tuple[list[dict[str, Any]], Optional[ApiResult]]:
        statuses = query.get("status_list") or []
        status = query.get("status")
        tags = query.get("tags")

        collected: list[dict[str, Any]] = []
        if statuses:
            seen_ids = set()
            for item in statuses:
                result = await self.task_api.list_tasks(headers, status=item, tags=tags)
                if not result.ok:
                    return [], result
                for task in result.data or []:
                    task_id = task.get("taskId") or task.get("id")
                    if task_id and task_id in seen_ids:
                        continue
                    if task_id:
                        seen_ids.add(task_id)
                    collected.append(task)
        else:
            result = await self.task_api.list_tasks(headers, status=status, tags=tags)
            if not result.ok:
                return [], result
            collected = list(result.data or [])

        keyword = query.get("keyword")
        if keyword:
            collected = filter_tasks(collected, keyword)

        return collected, None

    async def _detail_task(
        self, session_id: str, entities: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        if (
            entities.get("title")
            and not entities.get("taskId")
            and not query.get("keyword")
            and not (entities.get("status") or entities.get("tags") or entities.get("description"))
        ):
            return {
                "assistantMessage": "缺少任务标识，无法更新标题。",
                "execution": {
                    "status": "skipped",
                    "result": {"reason": "missing_identifier"},
                },
            }

        task_id, candidates, error = await self._resolve_task(entities, headers)
        if error is not None:
            return self._error_response(error)
        if candidates is not None:
            await self.session_store.set_pending(session_id, "detail", candidates)
            return self._clarify_candidates(candidates)
        if not task_id:
            return {
                "assistantMessage": "我没有找到对应的任务，请提供更具体的信息。",
                "execution": {
                    "status": "skipped",
                    "result": {"reason": "task_not_found"},
                },
            }

        result = await self.task_api.get_task(task_id, headers)
        if not result.ok:
            return self._error_response(result)

        task = result.data or {}
        assistant_message = format_task_detail(task)
        return {
            "assistantMessage": assistant_message,
            "execution": {"status": "success", "result": task},
        }

    async def _update_task(
        self, session_id: str, entities: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        task_ids = entities.get("taskIds") or []
        if task_ids:
            results: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            for task_id in task_ids:
                update_result = await self.task_api.update_task(
                    task_id,
                    headers,
                    title=entities.get("title"),
                    description=entities.get("description"),
                    status=entities.get("status"),
                    tags=entities.get("tags"),
                )
                if update_result.ok:
                    results.append(update_result.data or {"taskId": task_id})
                else:
                    failed.append({"taskId": task_id, "error": update_result.error})

            assistant_message = f"已更新 {len(results)} 个任务。"
            if failed:
                assistant_message += f" 另有 {len(failed)} 个任务更新失败。"
            return {
                "assistantMessage": assistant_message,
                "execution": {
                    "status": "success" if not failed else "failed",
                    "result": {"updated": results, "failed": failed},
                },
            }

        bulk = bool(entities.get("bulk"))
        query = entities.get("query", {})
        has_query = bool(
            query.get("status")
            or query.get("status_list")
            or query.get("tags")
            or query.get("keyword")
        )

        if bulk or has_query:
            tasks, error = await self._get_tasks_for_query(query, headers)
            if error is not None:
                return self._error_response(error)

            if not tasks:
                return {
                    "assistantMessage": "没有找到符合条件的任务。",
                    "execution": {"status": "success", "result": []},
                }

            if not bulk and len(tasks) > 1:
                await self.session_store.set_pending(session_id, "update", tasks)
                return self._clarify_candidates(tasks)

            results: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            for task in tasks:
                task_id = task.get("taskId") or task.get("id")
                if not task_id:
                    continue
                update_result = await self.task_api.update_task(
                    task_id,
                    headers,
                    title=entities.get("title"),
                    description=entities.get("description"),
                    status=entities.get("status"),
                    tags=entities.get("tags"),
                )
                if update_result.ok:
                    results.append(update_result.data or {"taskId": task_id})
                else:
                    failed.append({"taskId": task_id, "error": update_result.error})

            assistant_message = f"已更新 {len(results)} 个任务。"
            if failed:
                assistant_message += f" 另有 {len(failed)} 个任务更新失败。"
            return {
                "assistantMessage": assistant_message,
                "execution": {
                    "status": "success" if not failed else "failed",
                    "result": {"updated": results, "failed": failed},
                },
            }

        task_id, candidates, error = await self._resolve_task(entities, headers)
        if error is not None:
            return self._error_response(error)
        if candidates is not None:
            await self.session_store.set_pending(session_id, "update", candidates)
            return self._clarify_candidates(candidates)
        if not task_id:
            return {
                "assistantMessage": "我没有找到对应的任务，请提供更具体的信息。",
                "execution": {
                    "status": "skipped",
                    "result": {"reason": "task_not_found"},
                },
            }

        result = await self.task_api.update_task(
            task_id,
            headers,
            title=entities.get("title"),
            description=entities.get("description"),
            status=entities.get("status"),
            tags=entities.get("tags"),
        )
        if not result.ok:
            return self._error_response(result)

        task = result.data or {}
        assistant_message = f"已更新任务：{task.get('title') or task_id}。"
        return {
            "assistantMessage": assistant_message,
            "execution": {"status": "success", "result": task},
        }

    async def _delete_task(
        self, session_id: str, entities: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:
        task_ids = entities.get("taskIds") or []
        if task_ids:
            deleted: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            for task_id in task_ids:
                delete_result = await self.task_api.delete_task(task_id, headers)
                if delete_result.ok:
                    deleted.append({"taskId": task_id})
                else:
                    failed.append({"taskId": task_id, "error": delete_result.error})

            assistant_message = f"已删除 {len(deleted)} 个任务。"
            if failed:
                assistant_message += f" 另有 {len(failed)} 个任务删除失败。"
            return {
                "assistantMessage": assistant_message,
                "execution": {
                    "status": "success" if not failed else "failed",
                    "result": {"deleted": deleted, "failed": failed},
                },
            }

        bulk = bool(entities.get("bulk"))
        query = entities.get("query", {})
        has_query = bool(
            query.get("status")
            or query.get("status_list")
            or query.get("tags")
            or query.get("keyword")
        )

        if not bulk and query.get("keyword"):
            bulk = True

        if bulk or has_query:
            tasks, error = await self._get_tasks_for_query(query, headers)
            if error is not None:
                return self._error_response(error)

            if not tasks:
                return {
                    "assistantMessage": "没有找到符合条件的任务。",
                    "execution": {"status": "success", "result": []},
                }

            deleted: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            for task in tasks:
                task_id = task.get("taskId") or task.get("id")
                if not task_id:
                    continue
                delete_result = await self.task_api.delete_task(task_id, headers)
                if delete_result.ok:
                    deleted.append({"taskId": task_id})
                else:
                    failed.append({"taskId": task_id, "error": delete_result.error})

            assistant_message = f"已删除 {len(deleted)} 个任务。"
            if failed:
                assistant_message += f" 另有 {len(failed)} 个任务删除失败。"
            return {
                "assistantMessage": assistant_message,
                "execution": {
                    "status": "success" if not failed else "failed",
                    "result": {"deleted": deleted, "failed": failed},
                },
            }

        task_id, candidates, error = await self._resolve_task(entities, headers)
        if error is not None:
            return self._error_response(error)
        if candidates is not None:
            await self.session_store.set_pending(session_id, "delete", candidates)
            return self._clarify_candidates(candidates)
        if not task_id:
            return {
                "assistantMessage": "我没有找到对应的任务，请提供更具体的信息。",
                "execution": {
                    "status": "skipped",
                    "result": {"reason": "task_not_found"},
                },
            }

        result = await self.task_api.delete_task(task_id, headers)
        if not result.ok:
            return self._error_response(result)

        assistant_message = "已删除任务。"
        return {
            "assistantMessage": assistant_message,
            "execution": {
                "status": "success",
                "result": result.data or {"taskId": task_id},
            },
        }

    async def _resolve_task(
        self, entities: dict[str, Any], headers: dict[str, str]
    ) -> tuple[Optional[str], Optional[list[dict[str, Any]]], Optional[ApiResult]]:
        task_id = entities.get("taskId")
        if task_id:
            return task_id, None, None

        keyword = entities.get("query", {}).get("keyword") or entities.get("title")
        if not keyword:
            return None, None, None

        list_result = await self.task_api.list_tasks(headers)
        if not list_result.ok:
            return None, None, list_result

        tasks = list_result.data or []
        filtered = filter_tasks(tasks, keyword)

        if len(filtered) == 1:
            return filtered[0].get("taskId"), None, None
        if len(filtered) == 0:
            return None, None, None

        return None, filtered, None

    def _clarify_candidates(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        lines = []
        for idx, task in enumerate(candidates[:5], start=1):
            title = task.get("title") or "(无标题)"
            status = task.get("status") or ""
            task_id = task.get("taskId") or task.get("id") or ""
            lines.append(f"{idx}. {title}（{status}） id: {task_id}")
        assistant_message = "找到多个匹配任务，请选择或补充信息：\n" + "\n".join(lines)
        return {
            "assistantMessage": assistant_message,
            "execution": {
                "status": "skipped",
                "result": {"reason": "multiple_matches", "candidates": candidates[:5]},
            },
        }

    def _error_response(self, result: ApiResult) -> dict[str, Any]:
        error = result.error or {"code": "TASK_API_ERROR", "message": "任务服务错误"}
        assistant_message = f"操作失败：{error.get('message')}"
        return {
            "assistantMessage": assistant_message,
            "execution": {"status": "failed", "result": error},
        }


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return str(value)


def normalize_task_id(value: Any) -> Optional[str]:
    text = _clean_text(value)
    if not text:
        return None
    try:
        return str(uuid.UUID(text))
    except (ValueError, AttributeError):
        return None


def normalize_task_ids(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        items = [normalize_task_id(item) for item in value]
        items = [item for item in items if item]
        return items or None
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        items = [normalize_task_id(part) for part in parts if part]
        items = [item for item in items if item]
        return items or None
    normalized = normalize_task_id(value)
    return [normalized] if normalized else None


def coerce_list(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or None
    if isinstance(value, str):
        if "," in value:
            parts = [part.strip() for part in value.split(",")]
            items = [part for part in parts if part]
            return items or None
        if value.strip():
            return [value.strip()]
        return None
    text = str(value).strip()
    return [text] if text else None


def coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            return None
    return None


def coerce_int_list(value: Any) -> Optional[list[int]]:
    if value is None:
        return None
    if isinstance(value, list):
        items = [coerce_int(item) for item in value]
        items = [item for item in items if item is not None]
        return items or None
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace("，", ",").split(",")]
        items = [coerce_int(part) for part in parts if part]
        items = [item for item in items if item is not None]
        return items or None
    item = coerce_int(value)
    return [item] if item is not None else None


def coerce_status_list(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        statuses = [str(item).strip() for item in value if str(item).strip()]
        statuses = [status for status in statuses if status in VALID_STATUSES]
        return statuses or None
    return None


def normalize_status(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return text if text in VALID_STATUSES else None
    return None


def filter_tasks(tasks: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
    def _variants(text: str) -> list[str]:
        base = text.strip()
        if not base:
            return []
        variants = {base}
        for suffix in ("任务", "事项", "事情"):
            if base.endswith(suffix) and len(base) > len(suffix):
                variants.add(base[: -len(suffix)].strip())
        if len(base) >= 2 and base[0] == base[-1] and base[0] in "\"'“”":
            variants.add(base[1:-1].strip())
        return [item for item in variants if item]

    keywords = [item.lower() for item in _variants(keyword)]
    filtered: list[dict[str, Any]] = []
    for task in tasks:
        title = str(task.get("title", "")).lower()
        description = str(task.get("description", "")).lower()
        if any(key in title or key in description for key in keywords):
            filtered.append(task)
    return filtered


def format_task_list(tasks: list[dict[str, Any]]) -> str:
    if not tasks:
        return "没有找到符合条件的任务。"
    lines = []
    for idx, task in enumerate(tasks[:8], start=1):
        title = task.get("title") or "(无标题)"
        status = task.get("status") or ""
        tags = task.get("tags") or []
        tag_text = f"，标签：{', '.join(tags)}" if tags else ""
        lines.append(f"{idx}. {title}（{status}{tag_text}）")
    suffix = "" if len(tasks) <= 8 else f"\n...共 {len(tasks)} 条任务"
    return "找到以下任务：\n" + "\n".join(lines) + suffix


def format_task_detail(task: dict[str, Any]) -> str:
    title = task.get("title") or "(无标题)"
    status = task.get("status") or ""
    description = task.get("description") or ""
    tags = task.get("tags") or []
    parts = [f"任务：{title}", f"状态：{status}"]
    if description:
        parts.append(f"描述：{description}")
    if tags:
        parts.append(f"标签：{', '.join(tags)}")
    return "\n".join(parts)


def summarize_execution(execution: dict[str, Any]) -> str:
    status = execution.get("status")
    result = execution.get("result")
    if status == "success" and isinstance(result, list):
        if not result:
            return "没有找到符合条件的任务。"
        titles = [task.get("title") or "(无标题)" for task in result[:5]]
        suffix = "" if len(result) <= 5 else f" 等共 {len(result)} 条"
        return f"找到任务：{', '.join(titles)}{suffix}"
    if status == "success" and isinstance(result, dict):
        if "updated" in result:
            return f"已更新 {len(result.get('updated', []))} 个任务。"
        if "deleted" in result:
            return f"已删除 {len(result.get('deleted', []))} 个任务。"
        title = result.get("title")
        if title:
            return f"已获取任务：{title}"
    if status == "failed":
        return "执行失败。"
    if status == "skipped":
        return "步骤未执行。"
    return "执行完成。"


def safe_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def _react_failure() -> dict[str, Any]:
    return {
        "thought": "",
        "action": "final",
        "action_input": {},
        "final": "抱歉，我暂时无法解析你的需求，请换一种说法。",
    }
