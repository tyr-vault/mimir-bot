from __future__ import annotations

import httpx
import pytest

from schemas.api import CategoryDraftPayload, CreateDraftBody
from services.api_client import MimirApiClient, MimirApiError


def _envelope(data: object, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json={"statusCode": status, "data": data, "message": "ok", "success": True},
    )


@pytest.mark.asyncio
async def test_login_and_list_categories() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path == "/auth/login":
            return _envelope({"token": "tok", "user": {"id": "1", "email": "a", "name": "A"}})
        if request.url.path == "/categories":
            assert request.headers.get("Authorization") == "Bearer tok"
            return _envelope(
                [
                    {
                        "id": "c1",
                        "userId": "u",
                        "name": "Food",
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-01-01T00:00:00Z",
                    }
                ]
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as http:
        client = MimirApiClient("http://api", "a@b.c", "secret")
        client._client = http  # noqa: SLF001
        await client.login()
        cats = await client.list_categories()
        assert len(cats) == 1
        assert cats[0].name == "Food"
        assert "POST /auth/login" in calls


@pytest.mark.asyncio
async def test_401_retries_on_get() -> None:
    tokens = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            tokens["n"] += 1
            return _envelope(
                {"token": f"tok{tokens['n']}", "user": {"id": "1", "email": "a", "name": "A"}}
            )
        if request.url.path == "/summary":
            auth = request.headers.get("Authorization")
            if auth == "Bearer tok1":
                return httpx.Response(401, json={"message": "expired"})
            return _envelope(
                {
                    "totalIncome": 0,
                    "totalExpense": 0,
                    "net": 0,
                    "count": 0,
                }
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as http:
        client = MimirApiClient("http://api", "a@b.c", "secret")
        client._client = http  # noqa: SLF001
        await client.login()
        summary = await client.get_summary(from_date="2026-11-01", to_date="2026-11-03")
        assert summary.count == 0
        assert tokens["n"] == 2


@pytest.mark.asyncio
async def test_post_draft_no_blind_retry_on_401() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            return _envelope({"token": "tok", "user": {"id": "1", "email": "a", "name": "A"}})
        if request.url.path == "/drafts":
            return httpx.Response(401, json={"message": "unauthorized"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as http:
        client = MimirApiClient("http://api", "a@b.c", "secret")
        client._client = http  # noqa: SLF001
        await client.login()
        with pytest.raises(MimirApiError) as exc:
            await client.create_draft(
                CreateDraftBody(kind="category", payload=CategoryDraftPayload(name="Pets"))
            )
        assert exc.value.kind == "auth"


@pytest.mark.asyncio
async def test_network_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as http:
        client = MimirApiClient("http://api", "a@b.c", "secret")
        client._client = http  # noqa: SLF001
        with pytest.raises(MimirApiError) as exc:
            await client.login()
        assert exc.value.kind == "network"
