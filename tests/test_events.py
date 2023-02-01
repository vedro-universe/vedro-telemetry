from uuid import uuid4

from baby_steps import given, then, when

from vedro_telemetry.events import (
    ArgParsedTelemetryEvent,
    ArgParseTelemetryEvent,
    EndedTelemetryEvent,
    ExcRaisedTelemetryEvent,
    StartedTelemetryEvent,
    StartupTelemetryEvent,
)


def test_started_telemetry_event_repr():
    with given:
        session_id = uuid4()
        project_id = "test"
        inited_at = 0
        event = StartedTelemetryEvent(session_id, project_id, inited_at,
                                      environment={}, plugins=[])

    with when:
        res = repr(event)

    with then:
        assert res == (f"<StartedTelemetryEvent session_id={str(session_id)!r} "
                       f"project_id={project_id!r}>")


def test_arg_parse_telemetry_event_repr():
    with given:
        session_id = uuid4()
        cmd = ["--help"]
        event = ArgParseTelemetryEvent(session_id, cmd)

    with when:
        res = repr(event)

    with then:
        assert res == f"<ArgParseTelemetryEvent session_id={str(session_id)!r} cmd={cmd!r}>"


def test_arg_parsed_telemetry_event_repr():
    with given:
        session_id = uuid4()
        args = {"--help": True}
        event = ArgParsedTelemetryEvent(session_id, args)

    with when:
        res = repr(event)

    with then:
        assert res == f"<ArgParsedTelemetryEvent session_id={str(session_id)!r} args={args!r}>"


def test_startup_telemetry_event_repr():
    with given:
        session_id = uuid4()
        discovered, scheduled = 1, 0
        event = StartupTelemetryEvent(session_id, discovered=discovered, scheduled=scheduled)

    with when:
        res = repr(event)

    with then:
        assert res == (f"<StartupTelemetryEvent session_id={str(session_id)!r} "
                       f"discovered={discovered!r} scheduled={scheduled!r}>")


def test_exc_raised_telemetry_event_repr():
    with given:
        session_id = uuid4()
        scenario_id = "scenarios/scenario.py::Scenario"
        event = ExcRaisedTelemetryEvent(session_id, scenario_id, {
            "type": "builtins.AssertionError",
            "message": "1 != 0",
            "traceback": []
        })

    with when:
        res = repr(event)

    with then:
        assert res == (f"<ExcRaisedTelemetryEvent session_id={str(session_id)!r} "
                       f"scenario_id={scenario_id!r} exc_type='builtins.AssertionError'>")


def test_ended_telemetry_event_repr():
    with given:
        session_id = uuid4()
        total, passed, failed, skipped = 6, 3, 2, 1
        event = EndedTelemetryEvent(session_id, total=total, passed=passed,
                                    failed=failed, skipped=skipped, interrupted=None)

    with when:
        res = repr(event)

    with then:
        assert res == (f"<EndedTelemetryEvent session_id={str(session_id)!r} "
                       f"total={total} passed={passed} failed={failed} "
                       f"skipped={skipped} is_interrupted=False>")
