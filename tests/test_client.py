"""Tests for AsyncHttpClient."""

import httpx
import pytest

from leo.client import AsyncHttpClient
from leo.exceptions import FetchError


class TestAsyncHttpClient:
    async def test_get_success(self) -> None:
        client = AsyncHttpClient()
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"ok": True}))
        client._client = httpx.AsyncClient(transport=transport)

        response = await client.get("http://test.local/api")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    async def test_post_success(self) -> None:
        client = AsyncHttpClient()
        transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"result": "ok"}))
        client._client = httpx.AsyncClient(transport=transport)

        response = await client.post("http://test.local/api", json={"query": "test"})
        assert response.status_code == 200

    async def test_get_http_error_raises_fetch_error(self) -> None:
        client = AsyncHttpClient()
        transport = httpx.MockTransport(lambda req: httpx.Response(500))
        client._client = httpx.AsyncClient(transport=transport)

        with pytest.raises(FetchError, match="HTTP error"):
            await client.get("http://test.local/api")

    async def test_post_http_error_raises_fetch_error(self) -> None:
        client = AsyncHttpClient()
        transport = httpx.MockTransport(lambda req: httpx.Response(500))
        client._client = httpx.AsyncClient(transport=transport)

        with pytest.raises(FetchError, match="HTTP error"):
            await client.post("http://test.local/api")

    async def test_headers_passed_to_client(self) -> None:
        client = AsyncHttpClient(headers={"X-Custom": "value"})
        await client._get_client()
        assert client._client is not None
        assert client._client.headers["X-Custom"] == "value"
        await client.close()

    async def test_lazy_initialization(self) -> None:
        client = AsyncHttpClient()
        assert client._client is None
        await client._get_client()
        assert client._client is not None
        await client.close()

    async def test_close(self) -> None:
        client = AsyncHttpClient()
        await client._get_client()
        assert client._client is not None
        await client.close()
        assert client._client is None

    async def test_close_when_not_initialized(self) -> None:
        client = AsyncHttpClient()
        await client.close()
        assert client._client is None
