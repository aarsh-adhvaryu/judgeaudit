"""Power and temperature guard for long unattended GPU runs on a laptop.

Background: on the development laptop the whole machine lost power twice, each
time after about three minutes of sustained GPU load, and once Windows logged the
charger going offline 20 seconds earlier. A hard power-off leaves no application
log, so this script keeps one:

  watch   once a second, append charger state, battery level and GPU temperature,
          power and throttle flags to a CSV (flushed to disk on every row). If the
          charger goes offline or the GPU passes the temperature limit, stop the
          judge server so the load ends before the machine does.
  check   exit 0 when it is safe to load the GPU, 1 otherwise (reason on stdout).

Standard library only. scripts/run_all.ps1 starts and stops it.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

GPU_FIELDS = (
    "temperature.gpu",
    "power.draw",
    "utilization.gpu",
    "memory.used",
    "clocks.gr",
    "temperature.gpu.tlimit",
    "clocks_event_reasons.hw_thermal_slowdown",
    "clocks_event_reasons.hw_power_brake_slowdown",
)
CSV_HEADER = (
    "time", "ac_online", "battery_pct", "gpu_temp_c", "gpu_power_w", "gpu_util_pct", "gpu_mem_mib",
    "gpu_clock_mhz", "gpu_temp_headroom_c", "thermal_slowdown", "power_brake_slowdown", "gpu_reading_age_s", "note",
)


@dataclass
class Sample:
    ac_online: bool | None = None      # None: unknown (desktop, or not Windows)
    battery_pct: int | None = None
    gpu: tuple = (None,) * len(GPU_FIELDS)
    gpu_age_s: float | None = None     # seconds since nvidia-smi last answered

    @property
    def temp_c(self) -> float | None:
        return self.gpu[0]


def parse_gpu_line(line: str) -> tuple:
    """One nvidia-smi csv,noheader,nounits line -> one value per GPU_FIELDS entry."""
    out = []
    for cell in [c.strip() for c in line.split(",")]:
        if cell in ("Active", "Not Active"):
            out.append(cell == "Active")
            continue
        try:
            out.append(float(cell))
        except ValueError:
            out.append(None)  # "[N/A]" and anything unexpected
    out = out[: len(GPU_FIELDS)]
    return tuple(out + [None] * (len(GPU_FIELDS) - len(out)))


def unsafe_reason(sample: Sample, temp_limit: float) -> str | None:
    """Why the GPU should not be under load right now, or None when it is fine."""
    if sample.ac_online is False:
        return "charger offline, running on battery"
    if sample.temp_c is not None and sample.temp_c >= temp_limit:
        return f"GPU at {sample.temp_c:.0f} C, limit {temp_limit:.0f} C"
    return None


class Guard:
    """Decides, sample by sample, when to stop the server and what to log."""

    def __init__(self, temp_limit: float, kill, log, rekill_every_s: float = 5.0):
        self.temp_limit = temp_limit
        self._kill = kill
        self._log = log
        self._rekill_every_s = rekill_every_s
        self._reason: str | None = None
        self._last_kill = float("-inf")

    def step(self, sample: Sample, now: float) -> str:
        """Returns the note for this sample's CSV row."""
        reason = unsafe_reason(sample, self.temp_limit)
        note = ""
        if reason:
            if now - self._last_kill >= self._rekill_every_s:
                killed = self._kill()
                self._last_kill = now
                if reason != self._reason or killed:
                    note = f"TRIP: {reason}; judge server {'stopped' if killed else 'was not running'}"
                    self._log(note)
        elif self._reason:
            note = "safe again"
            self._log(note)
            self._last_kill = float("-inf")
        self._reason = reason
        return note


class _PowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_ubyte),
        ("BatteryFlag", ctypes.c_ubyte),
        ("BatteryLifePercent", ctypes.c_ubyte),
        ("SystemStatusFlag", ctypes.c_ubyte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


def read_power() -> tuple[bool | None, int | None]:
    if os.name != "nt":
        return None, None
    status = _PowerStatus()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        return None, None
    ac = {0: False, 1: True}.get(status.ACLineStatus)
    pct = status.BatteryLifePercent if status.BatteryLifePercent <= 100 else None
    return ac, pct


def _smi_command(loop_ms: int | None = None) -> list[str]:
    cmd = ["nvidia-smi", f"--query-gpu={','.join(GPU_FIELDS)}", "--format=csv,noheader,nounits"]
    if loop_ms:
        cmd += ["-lms", str(loop_ms)]
    return cmd


def read_gpu_once(timeout_s: float = 10.0) -> tuple:
    try:
        out = subprocess.run(_smi_command(), capture_output=True, text=True, timeout=timeout_s).stdout
        return parse_gpu_line(out.strip().splitlines()[0])
    except (OSError, subprocess.SubprocessError, IndexError):
        return (None,) * len(GPU_FIELDS)


class GpuReader(threading.Thread):
    """Keeps the latest nvidia-smi reading. A frozen GPU shows up as a growing age."""

    def __init__(self, interval_s: float):
        super().__init__(daemon=True)
        self._interval_ms = max(250, int(interval_s * 1000))
        self._lock = threading.Lock()
        self._values: tuple = (None,) * len(GPU_FIELDS)
        self._at: float | None = None

    def run(self) -> None:
        while True:
            try:
                proc = subprocess.Popen(_smi_command(self._interval_ms), stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True)
                for line in proc.stdout:
                    if line.strip():
                        with self._lock:
                            self._values, self._at = parse_gpu_line(line), time.monotonic()
            except OSError:
                pass
            time.sleep(5)  # nvidia-smi missing or exited (driver reset): try again

    def latest(self) -> tuple[tuple, float | None]:
        with self._lock:
            age = None if self._at is None else round(time.monotonic() - self._at, 1)
            return self._values, age


def process_alive(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        return False
    try:
        return kernel32.WaitForSingleObject(handle, 0) == 0x102  # WAIT_TIMEOUT: still running
    finally:
        kernel32.CloseHandle(handle)


def kill_image(image: str) -> bool:
    """Force-stops every process with this image name. True when at least one was stopped."""
    try:
        if os.name == "nt":
            return subprocess.run(["taskkill", "/F", "/IM", image], capture_output=True).returncode == 0
        return subprocess.run(["pkill", "-9", "-f", image], capture_output=True).returncode == 0
    except OSError:
        return False


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def watch(args) -> int:
    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    reader = GpuReader(args.interval)
    reader.start()

    def log(text: str) -> None:
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  gpu_guard: {text}"
        print(f"[gpu_guard] {text}", flush=True)
        if args.trip_log:
            with open(args.trip_log, "a", encoding="ascii", errors="replace") as handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    guard = Guard(args.temp_limit, kill=lambda: kill_image(args.image), log=log)
    new_file = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="ascii") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(CSV_HEADER)
        while True:
            if args.parent_pid and not process_alive(args.parent_pid):
                return 0  # the script that started us is gone: never linger as an orphan
            ac, pct = read_power()
            gpu, age = reader.latest()
            sample = Sample(ac_online=ac, battery_pct=pct, gpu=gpu, gpu_age_s=age)
            note = guard.step(sample, time.monotonic())
            writer.writerow([f"{datetime.now():%Y-%m-%d %H:%M:%S}", _cell(ac), _cell(pct),
                             *[_cell(v) for v in gpu], _cell(age), note])
            handle.flush()
            os.fsync(handle.fileno())  # a hard power-off must not take the last rows with it
            time.sleep(args.interval)


def check(args) -> int:
    ac, pct = read_power()
    sample = Sample(ac_online=ac, battery_pct=pct, gpu=read_gpu_once(), gpu_age_s=0.0)
    reason = unsafe_reason(sample, args.temp_limit)
    temp = "unknown" if sample.temp_c is None else f"{sample.temp_c:.0f} C"
    print(reason or f"ok (charger {'online' if ac else 'state unknown'}, GPU {temp})")
    return 1 if reason else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("watch", help="log telemetry and stop the judge server when it is not safe")
    w.add_argument("--csv", required=True)
    w.add_argument("--trip-log", help="append a line here whenever the guard trips")
    w.add_argument("--temp-limit", type=float, default=90.0)
    w.add_argument("--interval", type=float, default=1.0)
    w.add_argument("--image", default="llama-server.exe", help="process image to stop on a trip")
    w.add_argument("--parent-pid", type=int, help="exit when this process is gone")
    w.set_defaults(func=watch)
    c = sub.add_parser("check", help="exit 0 when it is safe to load the GPU")
    c.add_argument("--temp-limit", type=float, default=75.0)
    c.set_defaults(func=check)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
