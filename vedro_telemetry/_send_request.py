from http import HTTPStatus
from typing import Any, Callable, Tuple

from httpx import Client, RequestError

__all__ = ("send_request", "SendRequestFn",)

SendRequestFn = Callable[[str, float, Any], Tuple[int, Any]]


class TelemetryRequestError(Exception):
    """
    Represents an error that occurs when sending a telemetry request fails.

    This exception is raised when the request fails due to an issue such as a
    connection error or a non-OK response from the server.
    """
    pass


def send_request(url: str, timeout: float, payload: Any) -> Tuple[int, Any]:
    """
    Send an HTTP POST request with a JSON payload to the specified URL.

    This function sends a telemetry event to the provided URL using an HTTP POST
    request with a timeout. If the request fails due to a connection issue or
    the server returns a non-OK status, a `TelemetryRequestError` is raised.

    :param url: The target URL for the HTTP request.
    :param timeout: The maximum time to wait for the request to complete.
    :param payload: The JSON serializable data to send in the body of the request.

    :return: A tuple containing the HTTP status code and the response body. The
             response body is parsed as JSON if possible; otherwise, the raw
             text response is returned.

    :raises TelemetryRequestError: If the request fails due to a connection error
                                   or a non-OK status is received.
    """
    with Client() as client:
        try:
            response = client.post(url, json=payload, timeout=timeout)
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
