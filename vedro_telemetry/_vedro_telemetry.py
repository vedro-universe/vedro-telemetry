import atexit
import os
import sys
from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path
from traceback import format_tb
from types import TracebackType
from typing import Any, List, Type, Union, final
from uuid import uuid4

from vedro.core import ConfigType, Dispatcher, ExcInfo, Plugin, PluginConfig, VirtualScenario
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


@final
class VedroTelemetryPlugin(Plugin):
    """
    A plugin for capturing and sending telemetry data from Vedro test runs.

    This plugin collects telemetry events throughout the Vedro test execution process,
    including events like argument parsing, startup, scenario failure, and cleanup. The
    events are sent to a specified API endpoint at the end of the test session.

    Telemetry events are generated and buffered during the test run, and then they are
    sent to the API either when the session ends or when explicitly triggered.
    """

    _inited_at = now()

    def __init__(self, config: Type["VedroTelemetry"], *,
                 send_request: SendRequestFn = send_request) -> None:
        """
        Initialize the VedroTelemetryPlugin with the provided configuration.

        :param config: The configuration for the plugin, including the API URL, timeout, etc.
        :param send_request: A function used to send requests to the API (defaults to the
                             built-in `send_request` function).
        """
        super().__init__(config)
        self._api_url = config.api_url.strip("/")
        self._timeout = config.timeout
        self._raise_exception = config.raise_exception_on_failure
        self._send_request = send_request
        self._session_id = uuid4()
        self._project_id = config.project_id or get_project_name(default="unknown")
        self._events: List[TelemetryEvent] = []
        self._arg_parser: Union[ArgumentParser, None] = None
        self._global_config: Union[ConfigType, None] = None

    def subscribe(self, dispatcher: Dispatcher) -> None:
        """
        Subscribe to various Vedro events for telemetry collection.

        This method registers event listeners that will trigger when specific Vedro
        events occur, such as configuration loading, argument parsing, startup, and
        scenario failure.

        :param dispatcher: The event dispatcher used to listen for Vedro events.
        """
        dispatcher.listen(ConfigLoadedEvent, self.on_config_loaded) \
            .listen(ArgParseEvent, self.on_arg_parse) \
            .listen(ArgParsedEvent, self.on_arg_parsed) \
            .listen(StartupEvent, self.on_startup) \
            .listen(ScenarioFailedEvent, self.on_scenario_failed) \
            .listen(CleanupEvent, self.on_cleanup)

    async def on_config_loaded(self, event: ConfigLoadedEvent) -> None:
        """
        Handle the ConfigLoadedEvent to capture plugin and environment information.

        This method collects data about the loaded plugins and the runtime environment,
        which is used to generate a `StartedTelemetryEvent`.

        :param event: The `ConfigLoadedEvent` from which to extract configuration details.
        """
        self._global_config = event.config

        plugins: List[PluginInfo] = []
        for _, section in self._global_config.Plugins.items():
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
        self._events.append(
            StartedTelemetryEvent(
                session_id=self._session_id,
                project_id=self._project_id,
                inited_at=self._inited_at,
                environment=environment,
                plugins=plugins,
            )
        )
        atexit.register(self._send_events)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        """
        Handle the ArgParseEvent to capture command-line argument information.

        This method records the command-line arguments provided during the session
        by generating an `ArgParseTelemetryEvent`.

        :param event: The `ArgParseEvent` containing the argument parser information.
        """
        self._arg_parser = event.arg_parser
        path, *args = sys.argv
        prog = self._cleanup_arg(os.path.abspath(path))
        self._events.append(
            ArgParseTelemetryEvent(self._session_id, [prog] + args)
        )

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        """
        Handle the ArgParsedEvent to capture parsed argument information.

        This method collects the parsed arguments and generates an `ArgParsedTelemetryEvent`.

        :param event: The `ArgParsedEvent` containing the parsed argument values.
        """
        args = {}
        actions = getattr(self._arg_parser, "_actions", [])
        for action in actions:
            if action.dest not in event.args:
                continue
            arg = max(action.option_strings, key=len) if action.option_strings else action.dest
            val = getattr(event.args, action.dest)
            if val != action.default:
                args[arg] = self._cleanup_arg(val)

        self._events.append(
            ArgParsedTelemetryEvent(self._session_id, args)
        )

    def on_startup(self, event: StartupEvent) -> None:
        """
        Handle the StartupEvent to capture information about discovered and scheduled scenarios.

        This method generates a `StartupTelemetryEvent` with the number of discovered and
        scheduled scenarios.

        :param event: The `StartupEvent` containing information about discovered and
                      scheduled scenarios.
        """
        discovered = len(list(event.scheduler.discovered))
        scheduled = len(list(event.scheduler.scheduled))
        self._events.append(
            StartupTelemetryEvent(self._session_id, discovered, scheduled)
        )

    def _get_scenario_id(self, scenario: VirtualScenario) -> str:
        """
        Extract the unique scenario ID.

        :param scenario: The `VirtualScenario` object containing the unique ID.
        :return: The decoded unique ID of the scenario.
        """
        # Ensure compatibility with Vedro v1.10 by checking the format of the unique_id
        if "::" not in scenario.unique_id:
            return b64decode(scenario.unique_id + "===").decode()
        return scenario.unique_id

    def on_scenario_failed(self, event: ScenarioFailedEvent) -> None:
        """
        Handle the ScenarioFailedEvent to capture exception information.

        This method collects details about failed scenarios, including the raised exceptions,
        and generates `ExcRaisedTelemetryEvent` for each failed step.

        :param event: The `ScenarioFailedEvent` containing scenario failure information.
        """
        scenario_result = event.scenario_result
        scenario_id = self._get_scenario_id(event.scenario_result.scenario)

        for step_result in scenario_result.step_results:
            exc_info = step_result.exc_info
            if exc_info is None:
                continue
            exception = self._format_exception(exc_info)
            self._events.append(
                ExcRaisedTelemetryEvent(self._session_id, scenario_id, exception)
            )

    def on_cleanup(self, event: CleanupEvent) -> None:
        """
        Handle the CleanupEvent to finalize the telemetry session and send all collected events.

        This method generates an `EndedTelemetryEvent` and sends the buffered telemetry events
        to the API endpoint.

        :param event: The `CleanupEvent` signaling the end of the test session.
        """
        report = event.report

        interrupted = None
        if getattr(report, "interrupted", None):
            interrupted = self._format_exception(report.interrupted)  # type: ignore

        self._events.append(
            EndedTelemetryEvent(
                session_id=self._session_id,
                total=report.total,
                passed=report.passed,
                failed=report.failed,
                skipped=report.skipped,
                interrupted=interrupted,
            )
        )
        try:
            self._send_events()
        finally:
            atexit.unregister(self._send_events)

    def _send_events(self) -> None:
        """
        Send the buffered telemetry events to the API endpoint.

        This method sends the collected telemetry data as a payload to the configured API URL.
        In case of a failure, it either raises an exception or logs the error to stderr.
        """
        payload = [e.to_dict() for e in self._events]
        try:
            self._send_request(f"{self._api_url}/v1/events", self._timeout, payload)
        except BaseException as e:
            if self._raise_exception:
                raise
            else:
                # Log the error to stderr instead of raising an exception
                print(f"[Error] {e!r}", file=sys.stderr)
        self._events = []

    def _format_exception(self, exc_info: ExcInfo) -> ExceptionInfo:
        """
        Format the exception information for telemetry reporting.

        This method formats the exception type, message, and traceback into a dictionary
        for reporting as part of the telemetry data.

        :param exc_info: The `ExcInfo` object containing exception details.
        :return: A dictionary representing the formatted exception information.
        """
        exc_type = exc_info.type
        return {
            "type": f"{exc_type.__module__}.{exc_type.__name__}",
            "message": str(exc_info.value),
            "traceback": self._format_traceback(exc_info.traceback),
        }

    def _format_traceback(self, tb: TracebackType) -> List[str]:
        """
        Format the traceback for telemetry reporting.

        This method extracts and cleans up the traceback information to ensure it is ready
        for inclusion in telemetry events.

        :param tb: The traceback object to format.
        :return: A list of formatted traceback strings.
        """
        return [self._cleanup_arg(x) for x in format_tb(tb, limit=100)]

    def _get_project_dir(self) -> Path:
        """
        Retrieve the project directory from the global configuration.

        :return: The resolved project directory as a `Path` object.
        """
        project_dir = getattr(self._global_config, "project_dir", Path.cwd())
        return project_dir.resolve()

    def _cleanup_arg(self, arg: Any) -> Any:
        """
        Clean up command-line arguments or other data before reporting.

        This method replaces absolute paths with relative paths, among other cleanups,
        to avoid reporting sensitive information.

        :param arg: The argument or data to clean up.
        :return: The cleaned-up argument or data.
        """
        if isinstance(arg, dict):
            return {k: self._cleanup_arg(v) for k, v in arg.items()}
        elif isinstance(arg, list):
            return [self._cleanup_arg(v) for v in arg]
        elif isinstance(arg, (type(None), bool, int, float)):
            return arg
        else:
            cwd = str(self._get_project_dir())
            return str(arg).replace(cwd, ".")


class VedroTelemetry(PluginConfig):
    """
    Configuration for the VedroTelemetryPlugin.

    This configuration class defines settings for the telemetry plugin, such as the
    API URL, request timeout, and project ID.
    """
    plugin = VedroTelemetryPlugin

    # The URL for the Vedro Telemetry API
    api_url: str = "http://localhost:8080"

    # Timeout duration (in seconds) for requests to the API
    timeout: float = 5.0

    # Unique Project ID, can be None if not set
    project_id: Union[str, None] = None

    # If True, raise an exception if telemetry data fails to send
    raise_exception_on_failure: bool = True
