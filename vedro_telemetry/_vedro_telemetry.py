import atexit
import os
import sys
from argparse import ArgumentParser
from base64 import b64decode
from traceback import format_tb
from types import TracebackType
from typing import Any, List, Type, Union
from uuid import uuid4

from vedro.core import Dispatcher, ExcInfo, Plugin, PluginConfig
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ConfigLoadedEvent,
    ScenarioFailedEvent,
    StartupEvent,
)

from ._send_request import SendRequestFn, send_request
from ._utils import get_package_version, get_project_name, now
from .events import (
    ArgParsedTelemetryEvent,
    ArgParseTelemetryEvent,
    EndedTelemetryEvent,
    EnvironmentInfo,
    ExceptionInfo,
    ExcRaisedTelemetryEvent,
    PluginInfo,
    StartedTelemetryEvent,
    StartupTelemetryEvent,
    TelemetryEvent,
)

__all__ = ("VedroTelemetry", "VedroTelemetryPlugin",)


class VedroTelemetryPlugin(Plugin):
    _inited_at = now()

    def __init__(self, config: Type["VedroTelemetry"], *,
                 send_request: SendRequestFn = send_request) -> None:
        super().__init__(config)
        self._api_url = config.api_url.strip("/")
        self._timeout = config.timeout
        self._send_request = send_request
        self._session_id = uuid4()
        self._project_id = config.project_id or get_project_name(default="unknown")
        self._events: List[TelemetryEvent] = []
        self._arg_parser: Union[ArgumentParser, None] = None

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ConfigLoadedEvent, self.on_config_loaded) \
                  .listen(ArgParseEvent, self.on_arg_parse) \
                  .listen(ArgParsedEvent, self.on_arg_parsed) \
                  .listen(StartupEvent, self.on_startup) \
                  .listen(ScenarioFailedEvent, self.on_scenario_failed) \
                  .listen(CleanupEvent, self.on_cleanup)

    async def on_config_loaded(self, event: ConfigLoadedEvent) -> None:
        plugins: List[PluginInfo] = []
        for _, section in event.config.Plugins.items():
            name, module = section.plugin.__name__, section.plugin.__module__
            package = module.split(".")[0]
            if module.startswith("vedro.plugins") and section.enabled:
                continue
            plugins.append({
                "name": name,
                "module": module,
                "enabled": section.enabled,
                "version": get_package_version(package),
            })
        environment: EnvironmentInfo = {
            "python_version": sys.version,
            "vedro_version": get_package_version("vedro"),
        }
        self._events += [
            StartedTelemetryEvent(
                session_id=self._session_id,
                project_id=self._project_id,
                inited_at=self._inited_at,
                environment=environment,
                plugins=plugins,
            )
        ]
        atexit.register(self._send_events)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        self._arg_parser = event.arg_parser
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

    def on_scenario_failed(self, event: ScenarioFailedEvent) -> None:
        scenario_result = event.scenario_result
        # hacky way
        scenario_id = b64decode(scenario_result.scenario.unique_id + "===").decode()

        for step_result in scenario_result.step_results:
            exc_info = step_result.exc_info
            if exc_info is None:
                continue
            exception = self._format_exception(exc_info)
            self._events += [
                ExcRaisedTelemetryEvent(self._session_id, scenario_id, exception)
            ]

    def on_cleanup(self, event: CleanupEvent) -> None:
        report = event.report
        interrupted = self._format_exception(report.interrupted) if report.interrupted else None
        self._events += [
            EndedTelemetryEvent(
                session_id=self._session_id,
                total=report.total,
                passed=report.passed,
                failed=report.failed,
                skipped=report.skipped,
                interrupted=interrupted,
            )
        ]
        try:
            self._send_events()
        finally:
            atexit.unregister(self._send_events)

    def _send_events(self) -> None:
        payload = [e.to_dict() for e in self._events]
        self._send_request(f"{self._api_url}/v1/events", self._timeout, payload)
        self._events = []

    def _format_exception(self, exc_info: ExcInfo) -> ExceptionInfo:
        exc_type = exc_info.type
        return {
            "type": f"{exc_type.__module__}.{exc_type.__name__}",
            "message": str(exc_info.value),
            "traceback": self._format_traceback(exc_info.traceback),
        }

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

    # Vedro Telemetry API URL
    api_url: str = "http://localhost:8080"

    # Timeout for requests to the API
    timeout: float = 5.0

    # Project ID
    project_id: Union[str, None] = None
