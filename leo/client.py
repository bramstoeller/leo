from typing import Any

import httpx
import structlog

from leo.exceptions import FetchError

log = structlog.get_logger()


class AsyncHttpClient:
    """Async HTTP client with lazy initialization, error mapping, and explicit close."""

    def __init__(self, headers: dict[str, str] | None = None):
        self._client: httpx.AsyncClient | None = None
        self._headers = headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(headers=self._headers)
            log.debug("http_client_created")
        return self._client

    async def get(self, url: str, timeout: float = 15) -> httpx.Response:
        try:
            client = await self._get_client()
            log.debug("http_get", url=url, timeout=timeout)
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            log.debug("http_get_ok", url=url, status=response.status_code)
            return response
        except httpx.ConnectError as e:
            log.debug("http_get_error", url=url, error="connect_error")
            raise FetchError(f"Cannot connect to {url}") from e
        except httpx.TimeoutException as e:
            log.debug("http_get_error", url=url, error="timeout")
            raise FetchError(f"Connection timed out for {url}") from e
        except httpx.HTTPStatusError as e:
            log.debug("http_get_error", url=url, error="http_status", status=e.response.status_code)
            raise FetchError(f"HTTP error: {e}") from e

    async def post(self, url: str, json: dict[str, Any] | None = None, timeout: float = 15) -> httpx.Response:
        try:
            client = await self._get_client()
            log.debug("http_post", url=url, timeout=timeout)
            response = await client.post(url, json=json, timeout=timeout)
            response.raise_for_status()
            log.debug("http_post_ok", url=url, status=response.status_code)
            return response
        except httpx.ConnectError as e:
            log.debug("http_post_error", url=url, error="connect_error")
            raise FetchError(f"Cannot connect to {url}") from e
        except httpx.TimeoutException as e:
            log.debug("http_post_error", url=url, error="timeout")
            raise FetchError(f"Connection timed out for {url}") from e
        except httpx.HTTPStatusError as e:
            log.debug("http_post_error", url=url, error="http_status", status=e.response.status_code)
            raise FetchError(f"HTTP error: {e}") from e

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            log.debug("http_client_closed")
