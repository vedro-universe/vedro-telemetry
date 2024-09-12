from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict, Union
from uuid import UUID

from ._utils import now

__all__ = ("StartedTelemetryEvent", "ArgParseTelemetryEvent", "ArgParsedTelemetryEvent",
           "StartupTelemetryEvent", "ExcRaisedTelemetryEvent", "EndedTelemetryEvent",
           "TelemetryEvent", "PluginInfo", "ExceptionInfo", "EnvironmentInfo",)


class PluginInfo(TypedDict):
    """
    Represents information about a plugin.

    This dictionary structure includes details about a plugin's name, module,
    whether it is enabled, and its version.

    :var name: The name of the plugin.
    :var module: The module name the plugin belongs to.
    :var enabled: Whether the plugin is currently enabled.
    :var version: The version of the plugin.
    """
    name: str
    module: str
    enabled: bool
    version: str


class ExceptionInfo(TypedDict):
    """
    Represents information about an exception.

    This dictionary contains the exception type, its message, and the traceback
    for debugging purposes.

    :var type: The type of the exception.
    :var message: A message describing the exception.
    :var traceback: A list of strings representing the traceback information.
    """
    type: str
    message: str
    traceback: List[str]


class EnvironmentInfo(TypedDict):
    """
    Represents information about the current runtime environment.

    This dictionary contains the versions of the Python interpreter and Vedro
    framework being used.

    :var python_version: The version of Python being used.
    :var vedro_version: The version of the Vedro framework being used.
    """
    python_version: str
    vedro_version: str


class TelemetryEvent(ABC):
    """
    Abstract base class for telemetry events.

    This class defines the interface for telemetry events, including methods
    for converting events to dictionary format and representing them as strings.
    It also stores the time of event creation.
    """

    def __init__(self) -> None:
        """
        Initialize the telemetry event and record its creation timestamp.
        """
        self._created_at = now()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the telemetry event into a dictionary format.

        :return: A dictionary representing the telemetry event.
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the telemetry event.

        :return: A string that describes the telemetry event.
        """
        pass


class StartedTelemetryEvent(TelemetryEvent):
    """
    Represents the event when a telemetry session starts.

    This event is generated when a telemetry session begins, containing details
    such as session ID, project ID, initialization time, environment information,
    and loaded plugins.
    """

    def __init__(self,
                 session_id: UUID,
                 project_id: str, inited_at: int,
                 environment: EnvironmentInfo,
                 plugins: List[PluginInfo]) -> None:
        """
        Initialize the StartedTelemetryEvent with session, project, environment,
        and plugin information.

        :param session_id: A unique identifier for the session.
        :param project_id: The ID of the project being tracked.
        :param inited_at: The timestamp of when the session was initialized.
        :param environment: Information about the runtime environment.
        :param plugins: A list of plugins loaded during the session.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._project_id = project_id
        self._inited_at = inited_at
        self._environment = environment
        self._plugins = plugins

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the StartedTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "project_id": self._project_id,
            "inited_at": self._inited_at,
            "environment": self._environment,
            "plugins": self._plugins,
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the StartedTelemetryEvent.

        :return: A string describing the event.
        """
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"project_id={self._project_id!r}>")


class ArgParseTelemetryEvent(TelemetryEvent):
    """
    Represents the event when command-line arguments are parsed.

    This event stores the session ID and the parsed command-line arguments.
    """

    def __init__(self, session_id: UUID, cmd: List[str]) -> None:
        """
        Initialize the ArgParseTelemetryEvent with session ID and command-line arguments.

        :param session_id: A unique identifier for the session.
        :param cmd: A list of parsed command-line arguments.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._cmd = cmd

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ArgParseTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "cmd": self._cmd
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the ArgParseTelemetryEvent.

        :return: A string describing the event.
        """
        return f"<{self.__class__.__name__} session_id={self._session_id!r} cmd={self._cmd!r}>"


class ArgParsedTelemetryEvent(TelemetryEvent):
    """
    Represents the event after command-line arguments are parsed into a dictionary.

    This event stores the session ID and the parsed arguments as a dictionary.
    """

    def __init__(self, session_id: UUID, args: Dict[str, Any]) -> None:
        """
        Initialize the ArgParsedTelemetryEvent with session ID and parsed arguments.

        :param session_id: A unique identifier for the session.
        :param args: A dictionary of parsed command-line arguments.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._args = args

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ArgParsedTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "args": self._args
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the ArgParsedTelemetryEvent.

        :return: A string describing the event.
        """
        return f"<{self.__class__.__name__} session_id={self._session_id!r} args={self._args!r}>"


class StartupTelemetryEvent(TelemetryEvent):
    """
    Represents the event when a session starts discovering and scheduling scenarios.

    This event stores the session ID, the number of discovered and scheduled scenarios.
    """

    def __init__(self, session_id: UUID, discovered: int, scheduled: int) -> None:
        """
        Initialize the StartupTelemetryEvent with session ID, discovered, and scheduled counts.

        :param session_id: A unique identifier for the session.
        :param discovered: The number of scenarios discovered.
        :param scheduled: The number of scenarios scheduled.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._discovered = discovered
        self._scheduled = scheduled

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the StartupTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "discovered": self._discovered,
            "scheduled": self._scheduled
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the StartupTelemetryEvent.

        :return: A string describing the event.
        """
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"discovered={self._discovered} scheduled={self._scheduled!r}>")


class ExcRaisedTelemetryEvent(TelemetryEvent):
    """
    Represents the event when an exception is raised during a scenario.

    This event stores the session ID, scenario ID, and details about the raised exception.
    """

    def __init__(self, session_id: UUID, scenario_id: str, exception: ExceptionInfo) -> None:
        """
        Initialize the ExcRaisedTelemetryEvent with session ID, scenario ID, and exception details.

        :param session_id: A unique identifier for the session.
        :param scenario_id: The ID of the scenario in which the exception occurred.
        :param exception: Details about the raised exception.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._scenario_id = scenario_id
        self._exception = exception

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ExcRaisedTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "scenario_id": self._scenario_id,
            "exception": self._exception,
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the ExcRaisedTelemetryEvent.

        :return: A string describing the event.
        """
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"scenario_id={self._scenario_id!r} exc_type={self._exception['type']!r}>")


class EndedTelemetryEvent(TelemetryEvent):
    """
    Represents the event when a telemetry session ends.

    This event stores the session ID, the total number of scenarios, and the count of
    passed, failed, skipped, and interrupted scenarios.
    """

    def __init__(self, session_id: UUID, *,
                 total: int,
                 passed: int,
                 failed: int,
                 skipped: int,
                 interrupted: Union[ExceptionInfo, None]) -> None:
        """
        Initialize the EndedTelemetryEvent with session ID and scenario results.

        :param session_id: A unique identifier for the session.
        :param total: The total number of scenarios executed.
        :param passed: The number of scenarios that passed.
        :param failed: The number of scenarios that failed.
        :param skipped: The number of scenarios that were skipped.
        :param interrupted: Information about an exception if the session was interrupted.
        """
        super().__init__()
        self._session_id = str(session_id)
        self._total = total
        self._passed = passed
        self._failed = failed
        self._skipped = skipped
        self._interrupted = interrupted

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the EndedTelemetryEvent into a dictionary format.

        :return: A dictionary representing the event.
        """
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "total": self._total,
            "passed": self._passed,
            "failed": self._failed,
            "skipped": self._skipped,
            "interrupted": self._interrupted,
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the EndedTelemetryEvent.

        :return: A string describing the event.
        """
        is_interrupted = self._interrupted is not None
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"total={self._total} passed={self._passed} failed={self._failed} "
                f"skipped={self._skipped} is_interrupted={is_interrupted!r}>")
