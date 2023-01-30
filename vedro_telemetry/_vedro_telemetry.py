import os
import sys
from argparse import ArgumentParser
from http import HTTPStatus
from traceback import format_tb
from types import TracebackType
from typing import Any, List, Type, Union
from uuid import uuid4

from vedro.core import Dispatcher, Plugin, PluginConfig
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ConfigLoadedEvent,
    ExceptionRaisedEvent,
    StartupEvent,
)

from ._send_request import SendRequestType, send_request
from .events import (
    ArgParsedTelemetryEvent,
    ArgParseTelemetryEvent,
    EndedTelemetryEvent,
    ExcRaisedTelemetryEvent,
    PluginInfo,
    StartedTelemetryEvent,
    StartupTelemetryEvent,
    TelemetryEvent,
)

__all__ = ("VedroTelemetry", "VedroTelemetryPlugin",)


class VedroTelemetryPlugin(Plugin):
    def __init__(self, config: Type["VedroTelemetry"], *,
                 send_request: SendRequestType = send_request) -> None:
        super().__init__(config)
        self._api_url = config.api_url
        self._timeout = config.timeout
        self._send_request = send_request
        self._session_id = uuid4()
        self._events: List[TelemetryEvent] = []
        self._arg_parser: Union[ArgumentParser, None] = None

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ConfigLoadedEvent, self.on_config_loaded) \
                  .listen(ArgParseEvent, self.on_arg_parse) \
                  .listen(ArgParsedEvent, self.on_arg_parsed) \
                  .listen(StartupEvent, self.on_startup) \
                  .listen(ExceptionRaisedEvent, self.on_exception_raised) \
                  .listen(CleanupEvent, self.on_cleanup)

    def on_config_loaded(self, event: ConfigLoadedEvent) -> None:
        plugins: List[PluginInfo] = []
        for _, section in event.config.Plugins.items():
            plugins.append({
                "name": section.plugin.__name__,
                "module": section.plugin.__module__,
                "enabled": section.enabled,
            })
        self._events += [StartedTelemetryEvent(self._session_id, plugins)]

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        self._arg_parser = event.arg_parser  # needed for on_arg_parsed

        path, *args = sys.argv
        prog = self._cleanup_arg(os.path.abspath(path))
        self._events += [ArgParseTelemetryEvent(self._session_id, [prog] + args)]

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        args = {}
        actions = getattr(self._arg_parser, "_actions", [])
        for action in actions:
            if action.dest not in event.args:
                continue
            arg = max(action.option_strings, key=len) if action.option_strings else action.dest
            val = getattr(event.args, action.dest)
            if val != action.default:
                args[arg] = self._cleanup_arg(val)

        self._events += [ArgParsedTelemetryEvent(self._session_id, args)]

    def on_startup(self, event: StartupEvent) -> None:
        discovered = len(list(event.scheduler.discovered))
        scheduled = len(list(event.scheduler.scheduled))
        self._events += [StartupTelemetryEvent(self._session_id, discovered, scheduled)]

    def on_exception_raised(self, event: ExceptionRaisedEvent) -> None:
        exc_info = event.exc_info
        tb = self._format_traceback(exc_info.traceback)
        self._events += [ExcRaisedTelemetryEvent(self._session_id, exc_info.value, tb)]

    async def on_cleanup(self, event: CleanupEvent) -> None:
        report = event.report
        self._events += [
            EndedTelemetryEvent(
                session_id=self._session_id,
                total=report.total,
                passed=report.passed,
                failed=report.failed,
                skipped=report.skipped,
            )
        ]
        try:
            await self._send_events()
        finally:
            pass

    async def _send_events(self) -> None:
        payload = [e.to_dict() for e in self._events]
        status, body = await self._send_request(self._api_url, self._timeout, payload)
        if status != HTTPStatus.OK:
            raise RuntimeError(f"Failed to send events: {status} {body}")

    def _format_traceback(self, tb: TracebackType) -> List[str]:
        return [self._cleanup_arg(x) for x in format_tb(tb, limit=100)]

    def _cleanup_arg(self, arg: Any, cwd: str = os.getcwd()) -> Any:
        if isinstance(arg, dict):
            return {k: self._cleanup_arg(v) for k, v in arg.items()}
        elif isinstance(arg, list):
            return [self._cleanup_arg(v) for v in arg]
        elif isinstance(arg, (type(None), bool, int, float)):
            return arg
        else:
            return str(arg).replace(cwd, ".")


class VedroTelemetry(PluginConfig):
    plugin = VedroTelemetryPlugin

    # Vedro Telemetry API
    api_url: str = "http://localhost:8080"

    # Timeout for requests
    timeout: float = 5.0
