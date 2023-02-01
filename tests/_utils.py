import sys
from pathlib import Path
from time import monotonic_ns
from types import TracebackType
from typing import Any, Dict, cast
from unittest.mock import Mock

import pytest
from vedro import Scenario as Scenario_
from vedro.core import (
    Config,
    ConfigType,
    Dispatcher,
    ExcInfo,
    Report,
    VirtualScenario,
    VirtualStep,
)

from vedro_telemetry import VedroTelemetry, VedroTelemetryPlugin

__all__ = ("dispatcher", "config", "plugin", "send_request_", "report_",
           "make_vscenario", "make_exc_info", "make_vstep", "get_telemetry_event",
           "assert_telemetry_event",)


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture()
def config() -> ConfigType:
    class Conf(Config):
        class Plugins(Config.Plugins):
            class VedroTelemetry(VedroTelemetry):
                enabled = True
    return Conf


@pytest.fixture()
def send_request_() -> Mock:
    response = 200, {}
    return Mock(return_value=response)


@pytest.fixture()
def plugin(dispatcher: Dispatcher, send_request_) -> VedroTelemetryPlugin:
    plugin = VedroTelemetryPlugin(VedroTelemetry, send_request=send_request_)
    plugin.subscribe(dispatcher)
    return plugin


@pytest.fixture()
def report_() -> Mock:
    return Mock(Report, total=6, passed=3, failed=2, skipped=1, interrupted=None)


def make_vscenario() -> VirtualScenario:
    class Scenario(Scenario_):
        __file__ = Path(f"scenario_{monotonic_ns()}.py").absolute()

    vsenario = VirtualScenario(Scenario, steps=[])
    return vsenario


def make_vstep() -> VirtualStep:
    def step():
        pass
    return VirtualStep(step)


def make_exc_info(exc_val: BaseException) -> ExcInfo:
    try:
        raise exc_val
    except type(exc_val):
        *_, traceback = sys.exc_info()
    return ExcInfo(type(exc_val), exc_val, cast(TracebackType, traceback))


def get_telemetry_event(mock: Mock) -> Dict[str, Any]:
    # send_request call
    assert len(mock.call_args_list) == 1, mock.call_args_list
    arg_list = mock.call_args_list[0]

    # send_request call args (url, timeout, payload)
    assert len(arg_list.args) == 3, arg_list.args
    last_arg = arg_list.args[-1]

    # first event in payload
    assert len(last_arg) >= 1, last_arg
    return last_arg[0]


def assert_telemetry_event(telemetry_event, body: Dict[str, Any]) -> bool:
    assert isinstance(telemetry_event["session_id"], str)
    assert isinstance(telemetry_event["created_at"], int)
    expected = {
        "session_id": telemetry_event["session_id"],
        "created_at": telemetry_event["created_at"],
        **body,
    }
    assert telemetry_event == expected, (telemetry_event, expected)
    return True
