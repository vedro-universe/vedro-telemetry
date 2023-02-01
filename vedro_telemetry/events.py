from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict, Union
from uuid import UUID

from ._utils import now

__all__ = ("StartedTelemetryEvent", "ArgParseTelemetryEvent", "ArgParsedTelemetryEvent",
           "StartupTelemetryEvent", "ExcRaisedTelemetryEvent", "EndedTelemetryEvent",
           "TelemetryEvent", "PluginInfo", "ExceptionInfo", "EnvironmentInfo",)


class PluginInfo(TypedDict):
    name: str
    module: str
    enabled: bool
    version: str


class ExceptionInfo(TypedDict):
    type: str
    message: str
    traceback: List[str]


class EnvironmentInfo(TypedDict):
    python_version: str
    vedro_version: str


class TelemetryEvent(ABC):
    def __init__(self) -> None:
        self._created_at = now()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class StartedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, project_id: str, inited_at: int,
                 environment: EnvironmentInfo, plugins: List[PluginInfo]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._project_id = project_id
        self._inited_at = inited_at
        self._environment = environment
        self._plugins = plugins

    def to_dict(self) -> Dict[str, Any]:
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
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"project_id={self._project_id!r}>")


class ArgParseTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, cmd: List[str]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._cmd = cmd

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "cmd": self._cmd
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} session_id={self._session_id!r} cmd={self._cmd!r}>"


class ArgParsedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, args: Dict[str, Any]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._args = args

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "args": self._args
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} session_id={self._session_id!r} args={self._args!r}>"


class StartupTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, discovered: int, scheduled: int) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._discovered = discovered
        self._scheduled = scheduled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "discovered": self._discovered,
            "scheduled": self._scheduled
        }

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"discovered={self._discovered} scheduled={self._scheduled!r}>")


class ExcRaisedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, scenario_id: str, exception: ExceptionInfo) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._scenario_id = scenario_id
        self._exception = exception

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "scenario_id": self._scenario_id,
            "exception": self._exception,
        }

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"scenario_id={self._scenario_id!r} exc_type={self._exception['type']!r}>")


class EndedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, *, total: int, passed: int, failed: int,
                 skipped: int, interrupted: Union[ExceptionInfo, None]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._total = total
        self._passed = passed
        self._failed = failed
        self._skipped = skipped
        self._interrupted = interrupted

    def to_dict(self) -> Dict[str, Any]:
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
        is_interrupted = self._interrupted is not None
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"total={self._total} passed={self._passed} failed={self._failed} "
                f"skipped={self._skipped} is_interrupted={is_interrupted!r}>")
