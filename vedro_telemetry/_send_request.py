from http import HTTPStatus
from typing import Any, Awaitable, Callable, Tuple

from httpx import AsyncClient, RequestError

__all__ = ("send_request", "SendRequestFn",)

SendRequestFn = Callable[[str, float, Any], Awaitable[Tuple[int, Any]]]


class TelemetryRequestError(Exception):
    pass


async def send_request(url: str, timeout: float, payload: Any) -> Tuple[int, Any]:
    async with AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=timeout)
        except RequestError as e:
            raise TelemetryRequestError(f"Failed to send events to {url!r}: «{e!r}»") from None

        status = response.status_code
        try:
            body = response.json()
        except:  # noqa: E722
            body = response.text

    if status != HTTPStatus.OK:
        raise TelemetryRequestError(f"Failed to send events to {url!r}: {status} «{body}»")
    return status, body
