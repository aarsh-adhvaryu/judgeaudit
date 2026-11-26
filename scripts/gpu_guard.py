"""Power and temperature guard for long unattended GPU runs on a laptop.

Background: on the development laptop the whole machine lost power three times
under GPU load. The third time this log caught it: 44 seconds into the load, at
about 135 W, the GPU's hotspot passed its throttle limit (nvidia-smi's
temperature.gpu.tlimit went negative), the GPU stopped answering, and the machine
died 95 seconds later. A hard power-off leaves no application log, so this script
keeps one:

  watch   once a second, append charger state, battery level and GPU temperature,
          power and throttle flags to a CSV (flushed to disk on every row).
          Soft limit: while the hotspot is close to its limit, or the laptop is in
          a power mode above --max-power-limit, keep a pause file in place; the
          judgeaudit runner starts no new judge call while it exists, so the GPU
          cools with the model still loaded and nothing is lost.
          Hard limit: stop the judge server, so the load ends before the machine
          does, when the charger goes offline, the GPU passes the temperature
          limit, its hotspot gets within --min-headroom of its limit, or the GPU
          stops answering.
  check   exit 0 when it is safe to load the GPU, 1 when it is not yet, 2 when the
          GPU is gone and only a reboot brings it back (reason on stdout).

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
    "enforced.power.limit",
)
CSV_HEADER = (
    "time", "ac_online", "battery_pct", "gpu_temp_c", "gpu_power_w", "gpu_util_pct", "gpu_mem_mib",
    "gpu_clock_mhz", "gpu_temp_headroom_c", "thermal_slowdown", "power_brake_slowdown", "gpu_power_limit_w",
    "gpu_reading_age_s", "note",
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

    @property
    def headroom_c(self) -> float | None:
        # Degrees left before the GPU throttles itself, measured at its hottest sensor.
        return self.gpu[5]

    @property
    def power_limit_w(self) -> float | None:
        # What the laptop's current performance mode lets the GPU draw.
        return self.gpu[8]


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


def unsafe_reason(sample: Sample, temp_limit: float, min_headroom: float | None = None) -> str | None:
    """Why the GPU should not be under load right now, or None when it is fine."""
    if sample.ac_online is False:
        return "charger offline, running on battery"
    if sample.temp_c is not None and sample.temp_c >= temp_limit:
        return f"GPU at {sample.temp_c:.0f} C, limit {temp_limit:.0f} C"
    if min_headroom is not None and sample.headroom_c is not None and sample.headroom_c <= min_headroom:
        temp = "unknown" if sample.temp_c is None else f"{sample.temp_c:.0f} C"
        return (f"GPU hotspot {sample.headroom_c:.0f} C from its throttle limit "
                f"(stops at {min_headroom:.0f} C or less), GPU at {temp}")
    return None


def over_power_reason(sample: Sample, max_power_limit: float | None) -> str | None:
    if max_power_limit is not None and sample.power_limit_w is not None and sample.power_limit_w > max_power_limit:
        return (f"GPU power limit is {sample.power_limit_w:.0f} W, above the {max_power_limit:.0f} W allowed: "
                "switch the laptop to Balanced or Quiet mode (Fn+Q)")
    return None


class Pacer:
    """Soft limit with hysteresis: pause at pause_headroom, resume at resume_headroom."""

    def __init__(self, pause_headroom: float | None, resume_headroom: float, max_power_limit: float | None = None):
        self.pause_headroom = pause_headroom
        self.resume_headroom = resume_headroom
        self.max_power_limit = max_power_limit
        self._hot = False

    def step(self, sample: Sample) -> str | None:
        """Returns why new judge calls should wait, or None when they may run."""
        headroom = sample.headroom_c
        if self.pause_headroom is not None and headroom is not None:
            if headroom <= self.pause_headroom:
                self._hot = True
            elif headroom >= self.resume_headroom:
                self._hot = False
        elif headroom is None:
            self._hot = False  # no reading: the hard limit decides
        power = over_power_reason(sample, self.max_power_limit)
        if power:
            return power
        if self._hot:
            return (f"GPU hotspot {headroom:.0f} C from its throttle limit, "
                    f"cooling until {self.resume_headroom:.0f} C of headroom")
        return None


class Guard:
    """Decides, sample by sample, when to stop the server and what to log."""

    def __init__(self, temp_limit: float, kill, log, rekill_every_s: float = 5.0,
                 min_headroom: float | None = None):
        self.temp_limit = temp_limit
        self.min_headroom = min_headroom
        self._seen_temp = False
        self._seen_headroom = False
        self._kill = kill
        self._log = log
        self._rekill_every_s = rekill_every_s
        self._reason: str | None = None
        self._last_kill = float("-inf")

    def step(self, sample: Sample, now: float) -> str:
        """Returns the note for this sample's CSV row."""
        reason = unsafe_reason(sample, self.temp_limit, self.min_headroom)
        # A GPU that hangs keeps reporting its last numbers but loses the headroom reading;
        # a GPU the driver has dropped reports nothing at all.
        if (self._seen_temp and sample.temp_c is None) or (self._seen_headroom and sample.headroom_c is None):
            reason = reason or "GPU stopped answering (hung or dropped by the driver)"
        self._seen_temp = self._seen_temp or sample.temp_c is not None
        self._seen_headroom = self._seen_headroom or sample.headroom_c is not None
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

    guard = Guard(args.temp_limit, kill=lambda: kill_image(args.image), log=log, min_headroom=args.min_headroom)
    pacer = Pacer(args.pause_headroom if args.pause_file else None, args.resume_headroom, args.max_power_limit)
    pause_file = Path(args.pause_file) if args.pause_file else None
    pausing = False
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
            wait_reason = pacer.step(sample) if pause_file else None
            if wait_reason:
                pause_file.write_text(wait_reason + "\n", encoding="ascii", errors="replace")  # rewritten = kept fresh
                if not pausing:
                    note = note or f"PAUSE: {wait_reason}"
            elif pausing:
                pause_file.unlink(missing_ok=True)
                note = note or "resume"
            pausing = bool(wait_reason)
            writer.writerow([f"{datetime.now():%Y-%m-%d %H:%M:%S}", _cell(ac), _cell(pct),
                             *[_cell(v) for v in gpu], _cell(age), note])
            handle.flush()
            os.fsync(handle.fileno())  # a hard power-off must not take the last rows with it
            time.sleep(args.interval)


def check(args) -> int:
    ac, pct = read_power()
    sample = Sample(ac_online=ac, battery_pct=pct, gpu=read_gpu_once(), gpu_age_s=0.0)
    if args.require_gpu and sample.temp_c is None:
        print("nvidia-smi does not see the GPU (hung or dropped by the driver): reboot before running again")
        return 2
    reason = unsafe_reason(sample, args.temp_limit) or over_power_reason(sample, args.max_power_limit)
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
    w.add_argument("--min-headroom", type=float,
                   help="also trip when the hotspot is this many C or fewer from its throttle limit")
    w.add_argument("--pause-file", help="keep this file in place while new judge calls should wait")
    w.add_argument("--pause-headroom", type=float, default=8.0, help="pause when the hotspot headroom is this low")
    w.add_argument("--resume-headroom", type=float, default=20.0, help="resume when it has recovered to this")
    w.add_argument("--max-power-limit", type=float, help="pause while the GPU power limit (W) is above this")
    w.add_argument("--interval", type=float, default=1.0)
    w.add_argument("--image", default="llama-server.exe", help="process image to stop on a trip")
    w.add_argument("--parent-pid", type=int, help="exit when this process is gone")
    w.set_defaults(func=watch)
    c = sub.add_parser("check", help="exit 0 when it is safe to load the GPU")
    c.add_argument("--temp-limit", type=float, default=75.0)
    c.add_argument("--require-gpu", action="store_true", help="exit 2 when nvidia-smi reports no GPU")
    c.add_argument("--max-power-limit", type=float, help="not safe while the GPU power limit (W) is above this")
    c.set_defaults(func=check)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
