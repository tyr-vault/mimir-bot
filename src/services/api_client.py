from __future__ import annotations

import logging
from typing import Any, Literal, TypeVar

import httpx
from pydantic import TypeAdapter

from schemas.api import (
    Category,
    CreateDraftBody,
    Draft,
    LoginResponse,
    PeriodSummary,
    Transaction,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")
ApiErrorKind = Literal["network", "http", "auth"]


class MimirApiError(Exception):
    def __init__(self, kind: ApiErrorKind, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status


class MimirApiClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        *,
        timeout: float = 15.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def login(self) -> None:
        try:
            response = await self._client.post(
                "/auth/login",
                json={"email": self._email, "password": self._password},
            )
        except httpx.HTTPError as exc:
            raise MimirApiError("network", f"Login request failed: {exc}") from exc

        if response.status_code >= 400:
            raise MimirApiError(
                "auth",
                f"Login failed with status {response.status_code}",
                response.status_code,
            )

        envelope = response.json()
        data = envelope.get("data") if isinstance(envelope, dict) else None
        if not isinstance(data, dict) or not data.get("token"):
            raise MimirApiError("auth", "Login response missing token")

        parsed = LoginResponse.model_validate(data)
        self._token = parsed.token

    async def list_categories(self) -> list[Category]:
        data = await self._request("GET", "/categories")
        return TypeAdapter(list[Category]).validate_python(data)

    async def create_draft(self, body: CreateDraftBody) -> Draft:
        data = await self._request(
            "POST",
            "/drafts",
            json=body.to_api_dict(),
            allow_retry_on_401=False,
        )
        return Draft.model_validate(data)

    async def list_transactions(
        self,
        *,
        from_date: str,
        to_date: str,
        limit: int | None = None,
    ) -> list[Transaction]:
        params: dict[str, str] = {"from": from_date, "to": to_date}
        if limit is not None:
            params["limit"] = str(limit)
        data = await self._request("GET", "/transactions", params=params)
        return TypeAdapter(list[Transaction]).validate_python(data)

    async def get_summary(self, *, from_date: str, to_date: str) -> PeriodSummary:
        data = await self._request(
            "GET",
            "/summary",
            params={"from": from_date, "to": to_date},
        )
        return PeriodSummary.model_validate(data)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        allow_retry_on_401: bool = True,
        retried: bool = False,
    ) -> Any:
        if not self._token:
            await self.login()

        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            response = await self._client.request(
                method,
                path,
                headers=headers,
                json=json,
                params=params,
            )
        except httpx.HTTPError as exc:
            raise MimirApiError("network", f"Request to {path} failed: {exc}") from exc

        if response.status_code == 401 and allow_retry_on_401 and not retried:
            await self.login()
            return await self._request(
                method,
                path,
                json=json,
                params=params,
                allow_retry_on_401=False,
                retried=True,
            )

        if response.status_code >= 400:
            kind: ApiErrorKind = "auth" if response.status_code == 401 else "http"
            detail = f"HTTP {response.status_code}"
            try:
                body = response.json()
                if isinstance(body, dict) and body.get("message"):
                    detail = str(body["message"])
            except ValueError:
                pass
            raise MimirApiError(kind, detail, response.status_code)

        envelope = response.json()
        if isinstance(envelope, dict) and "data" in envelope:
            return envelope["data"]
        return envelope
