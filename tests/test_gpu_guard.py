import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "gpu_guard", Path(__file__).resolve().parents[1] / "scripts" / "gpu_guard.py"
)
gpu_guard = importlib.util.module_from_spec(_spec)
sys.modules["gpu_guard"] = gpu_guard  # dataclasses looks the module up by name
_spec.loader.exec_module(gpu_guard)

Sample = gpu_guard.Sample


def gpu(temp, headroom=None):
    values = [None] * len(gpu_guard.GPU_FIELDS)
    values[0], values[5] = temp, headroom
    return tuple(values)


def test_parse_gpu_line_handles_numbers_flags_and_missing_values():
    values = gpu_guard.parse_gpu_line("71, 118.42, 99, 6577, 2400, 18, Not Active, Active")
    assert values == (71.0, 118.42, 99.0, 6577.0, 2400.0, 18.0, False, True)
    assert gpu_guard.parse_gpu_line("[N/A], [N/A]") == (None,) * len(gpu_guard.GPU_FIELDS)


@pytest.mark.parametrize(
    "sample, unsafe",
    [
        (Sample(ac_online=True, gpu=gpu(70.0)), False),
        (Sample(ac_online=None, gpu=gpu(None)), False),   # desktop, no sensors: never blocks
        (Sample(ac_online=False, gpu=gpu(50.0)), True),   # on battery
        (Sample(ac_online=True, gpu=gpu(90.0)), True),    # at the limit
    ],
)
def test_unsafe_reason(sample, unsafe):
    assert bool(gpu_guard.unsafe_reason(sample, temp_limit=90)) is unsafe


def test_hotspot_headroom_trips_before_the_temperature_limit():
    # The real failure: 85 C on the main sensor, limit 90 C, but the hotspot already past its own limit.
    hot = Sample(ac_online=True, gpu=gpu(85.0, headroom=-1.0))
    assert gpu_guard.unsafe_reason(hot, temp_limit=90) is None
    assert "hotspot" in gpu_guard.unsafe_reason(hot, temp_limit=90, min_headroom=3)
    assert gpu_guard.unsafe_reason(Sample(ac_online=True, gpu=gpu(80.0, headroom=9.0)), 90, min_headroom=3) is None


def test_guard_trips_when_the_gpu_stops_answering():
    kills, logs = [], []
    guard = gpu_guard.Guard(temp_limit=90, kill=lambda: kills.append(1) or True, log=logs.append)
    assert guard.step(Sample(ac_online=True, gpu=gpu(None)), now=0) == ""       # no GPU sensors at all: fine
    assert guard.step(Sample(ac_online=True, gpu=gpu(80.0, headroom=9.0)), now=1) == ""
    # Hung GPU: stale numbers keep coming, the headroom reading is gone.
    assert "stopped answering" in guard.step(Sample(ac_online=True, gpu=gpu(80.0)), now=2)
    assert len(kills) == 1


def test_guard_stops_the_server_when_the_charger_drops_and_reports_recovery():
    kills, logs = [], []
    server_running = [True]

    def kill():
        kills.append(1)
        was_running, server_running[0] = server_running[0], False
        return was_running

    guard = gpu_guard.Guard(temp_limit=90, kill=kill, log=logs.append, rekill_every_s=5)
    on_ac = Sample(ac_online=True, gpu=gpu(70.0))
    on_battery = Sample(ac_online=False, gpu=gpu(70.0))

    assert guard.step(on_ac, now=0) == "" and not kills
    assert "TRIP" in guard.step(on_battery, now=1) and len(kills) == 1
    assert guard.step(on_battery, now=2) == "" and len(kills) == 1    # no kill storm
    server_running[0] = True                                           # something restarted it too early
    assert "stopped" in guard.step(on_battery, now=7) and len(kills) == 2
    assert guard.step(on_ac, now=8) == "safe again"
    assert [("TRIP" in line) for line in logs] == [True, True, False]
