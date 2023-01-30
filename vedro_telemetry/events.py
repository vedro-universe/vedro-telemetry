from abc import ABC, abstractmethod
from time import time
from typing import Any, Dict, List, TypedDict
from uuid import UUID

__all__ = ("StartedTelemetryEvent", "ArgParseTelemetryEvent", "ArgParsedTelemetryEvent",
           "StartupTelemetryEvent", "ExcRaisedTelemetryEvent", "EndedTelemetryEvent",
           "TelemetryEvent", "PluginInfo", "ExceptionInfo",)


class PluginInfo(TypedDict):
    name: str
    module: str
    enabled: bool


class ExceptionInfo(TypedDict):
    type: str
    message: str
    traceback: List[str]


class TelemetryEvent(ABC):
    def __init__(self) -> None:
        self._created_at = round(time() * 1000)

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class StartedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, plugins: List[PluginInfo]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._plugins = plugins

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "plugins": self._plugins,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} session_id={self._session_id!r}>"


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
    def __init__(self, session_id: UUID, exception: BaseException, traceback: List[str]) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._exception = exception
        self._traceback = traceback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "exception": {
                "type": type(self._exception).__name__,
                "message": str(self._exception),
                "traceback": self._traceback,
            }
        }

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"exception={self._exception!r}>")


class EndedTelemetryEvent(TelemetryEvent):
    def __init__(self, session_id: UUID, *, total: int, passed: int, failed: int,
                 skipped: int) -> None:
        super().__init__()
        self._session_id = str(session_id)
        self._total = total
        self._passed = passed
        self._failed = failed
        self._skipped = skipped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": f"{self.__class__.__name__}",
            "session_id": self._session_id,
            "created_at": self._created_at,
            "total": self._total,
            "passed": self._passed,
            "failed": self._failed,
            "skipped": self._skipped
        }

    def __repr__(self) -> str:
        return (f"<{self.__class__.__name__} session_id={self._session_id!r} "
                f"total={self._total} passed={self._passed} failed={self._failed} "
                f"skipped={self._skipped}>")
