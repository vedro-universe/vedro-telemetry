from argparse import ArgumentParser, Namespace
from pathlib import Path
from unittest.mock import AsyncMock, Mock, call, patch

from baby_steps import given, then, when
from vedro.core import ConfigType, Dispatcher
from vedro.core import MonotonicScenarioScheduler as Scheduler
from vedro.core import Report, ScenarioResult, StepResult
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    CleanupEvent,
    ConfigLoadedEvent,
    ScenarioFailedEvent,
    StartupEvent,
)

from vedro_telemetry import VedroTelemetryPlugin

from ._utils import (
    assert_telemetry_event,
    config,
    dispatcher,
    get_telemetry_event,
    make_exc_info,
    make_vscenario,
    make_vstep,
    plugin,
    report_,
    send_request_,
)

__all__ = ("plugin", "dispatcher", "config", "send_request_", "report_")  # fixtures


async def test_started_telemetry(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                                 config: ConfigType, send_request_: AsyncMock):
    with given:
        event = ConfigLoadedEvent(Path(), config)
        await dispatcher.fire(event)

    with when:
        await dispatcher.fire(CleanupEvent(Report()))

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "StartedTelemetryEvent",
            "project_id": "vedro-telemetry",
            "plugins": [
                {
                    "name": "VedroTelemetryPlugin",
                    "module": "vedro_telemetry._vedro_telemetry",
                    "enabled": True,
                }
            ]
        })


async def test_arg_parse_event(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                               send_request_: AsyncMock):
    with given:
        event = ArgParseEvent(ArgumentParser())
        argv = ["prog", "run", "-vv"]
        with patch("sys.argv", argv):
            await dispatcher.fire(event)

    with when:
        await dispatcher.fire(CleanupEvent(Report()))

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "ArgParseTelemetryEvent",
            "cmd": ["./prog", "run", "-vv"],
        })


async def test_arg_parsed_event(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                                send_request_: AsyncMock):
    with given:
        event = ArgParsedEvent(Namespace())
        await dispatcher.fire(event)

    with when:
        await dispatcher.fire(CleanupEvent(Report()))

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "ArgParsedTelemetryEvent",
            "args": {},
        })


async def test_startup_event(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                             send_request_: AsyncMock):
    with given:
        scenarios = [make_vscenario(), make_vscenario(), make_vscenario()]
        scheduler = Scheduler(scenarios)
        scheduler.ignore(scenarios[0])

        event = StartupEvent(scheduler)
        await dispatcher.fire(event)

    with when:
        await dispatcher.fire(CleanupEvent(Report()))

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "StartupTelemetryEvent",
            "discovered": 3,
            "scheduled": 2,
        })


async def test_raised_exc_event(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                                send_request_: AsyncMock):
    with given:
        exc_info = make_exc_info(AssertionError("1 != 0"))

        scenario_result = ScenarioResult(make_vscenario())
        step_result = StepResult(make_vstep()).set_exc_info(exc_info)
        scenario_result.add_step_result(step_result)

        event = ScenarioFailedEvent(scenario_result)
        await dispatcher.fire(event)

    with when:
        await dispatcher.fire(CleanupEvent(Report()))

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "ExcRaisedTelemetryEvent",
            "scenario_id": f"{scenario_result.scenario.rel_path}::Scenario",
            "exception": {
                "type": "AssertionError",
                "message": "1 != 0",
                "traceback": [
                    '  File "./tests/_utils.py", line 75, in make_exc_info\n    raise exc_val\n'
                ]
            }
        })


async def test_ended_telemetry(*, plugin: VedroTelemetryPlugin, dispatcher: Dispatcher,
                               config: ConfigType, report_: Mock, send_request_: AsyncMock):
    with given:
        api_url = config.Plugins.VedroTelemetry.api_url
        timeout = config.Plugins.VedroTelemetry.timeout
        event = CleanupEvent(report_)

    with when:
        await dispatcher.fire(event)

    with then:
        telemetry_event = get_telemetry_event(send_request_)
        assert assert_telemetry_event(telemetry_event, {
            "event_id": "EndedTelemetryEvent",
            "total": report_.total,
            "passed": report_.passed,
            "failed": report_.failed,
            "skipped": report_.skipped,
        })
        assert send_request_.mock_calls == [
            call(api_url, timeout, [telemetry_event])
        ]
