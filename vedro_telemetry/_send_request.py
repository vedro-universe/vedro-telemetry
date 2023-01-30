from typing import Any, Awaitable, Callable, Tuple

from httpx import AsyncClient

__all__ = ("send_request", "SendRequestType",)

SendRequestType = Callable[[str, float, Any], Awaitable[Tuple[int, Any]]]


async def send_request(url: str, timeout: float, payload: Any) -> Tuple[int, Any]:
    async with AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=timeout)
    return response.status_code, response.json()
