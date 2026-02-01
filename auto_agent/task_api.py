from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class ApiResult:
    ok: bool
    status_code: int
    data: Any = None
    error: Optional[dict[str, Any]] = None


class TaskApi:
    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def list_tasks(
        self,
        headers: dict[str, str],
        status: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> ApiResult:
        params: dict[str, str] = {}
        if status:
            params["status"] = status
        if tags:
            params["tags"] = ",".join(tags)
        return await self._request("GET", "/tasks", headers=headers, params=params)

    async def get_task(self, task_id: str, headers: dict[str, str]) -> ApiResult:
        return await self._request("GET", f"/tasks/{task_id}", headers=headers)

    async def create_task(
        self,
        headers: dict[str, str],
        title: str,
        description: Optional[str],
        tags: Optional[list[str]],
    ) -> ApiResult:
        payload: dict[str, Any] = {"title": title}
        if description:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags
        return await self._request("POST", "/tasks", headers=headers, json=payload)

    async def update_task(
        self,
        task_id: str,
        headers: dict[str, str],
        title: Optional[str],
        description: Optional[str],
        status: Optional[str],
        tags: Optional[list[str]],
    ) -> ApiResult:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        if tags is not None:
            payload["tags"] = tags
        return await self._request("PUT", f"/tasks/{task_id}", headers=headers, json=payload)

    async def delete_task(self, task_id: str, headers: dict[str, str]) -> ApiResult:
        return await self._request("DELETE", f"/tasks/{task_id}", headers=headers)

    async def _request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        params: Optional[dict[str, str]] = None,
        json: Any = None,
    ) -> ApiResult:
        url = f"{self.base_url}{path}"
        try:
            response = await self.client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            )
        except httpx.RequestError as exc:
            return ApiResult(
                ok=False,
                status_code=502,
                error={"code": "BAD_GATEWAY", "message": f"任务服务不可用: {exc}"},
            )

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.status_code >= 400:
            error_payload = None
            if isinstance(payload, dict) and "error" in payload:
                error_payload = payload.get("error")
            if not error_payload:
                error_payload = {
                    "code": "TASK_API_ERROR",
                    "message": f"任务服务错误 (HTTP {response.status_code})",
                }
            return ApiResult(
                ok=False,
                status_code=response.status_code,
                error=error_payload,
                data=payload,
            )

        if isinstance(payload, dict) and "data" in payload:
            payload = payload.get("data")

        return ApiResult(ok=True, status_code=response.status_code, data=payload)
