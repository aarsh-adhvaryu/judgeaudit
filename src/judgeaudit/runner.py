"""Run an audit: build cases, ask the judge (through the cache), write results."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import yaml

from . import __version__
from . import guard as guards
from .cache import VerdictCache, make_key
from .judges import JudgeError, JudgeRequest, JudgeUnreachable, build_judge
from .metrics import compute_summary
from .parsing import parse_verdict
from .prompts import PROMPT_VERSION
from .report import write_reports
from .tasks import load_cases


class PauseGate:
    """Cooperative back-pressure for a judge that shares a machine with a thermal budget.

    While the pause file exists and is fresh, no new judge call starts; calls already
    in flight finish. Whoever watches the hardware (scripts/gpu_guard.py) creates the
    file when the GPU is close to its limit and removes it when it has cooled. The
    file must be refreshed while the pause lasts: a file left behind by a watcher that
    died is ignored once it is stale_after_s old, so a run can never hang on it.
    """

    def __init__(self, path: str | Path | None, log=print, stale_after_s: float = 30.0, poll_s: float = 0.25):
        self.path = Path(path) if path else None
        self.paused_s = 0.0
        self.pauses = 0
        self._log = log
        self._stale_after_s = stale_after_s
        self._poll_s = poll_s
        self._lock = threading.Lock()
        self._since: float | None = None

    def reason(self) -> str | None:
        if self.path is None:
            return None
        try:
            if time.time() - self.path.stat().st_mtime > self._stale_after_s:
                return None
            return self.path.read_text(encoding="utf-8", errors="replace").strip() or "pause requested"
        except OSError:
            return None

    def wait(self) -> None:
        reason = self.reason()
        if reason is None:
            return
        with self._lock:
            if self._since is None:
                self._since = time.perf_counter()
                self.pauses += 1
                self._log(f"[judgeaudit] paused: {reason}")
        while self.reason() is not None:
            time.sleep(self._poll_s)
        with self._lock:
            if self._since is not None:
                self.paused_s += time.perf_counter() - self._since
                self._since = None
                self._log("[judgeaudit] resumed")


def _file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def _previous_run(out_dir: Path) -> dict:
    try:
        return json.loads((out_dir / "summary.json").read_text(encoding="utf-8")).get("run", {})
    except (OSError, ValueError):
        return {}


def _sum(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) if values else None


def _row(case, repeat: int, subs: list, payloads: dict, guard: dict, cached: bool, error: str | None) -> dict:
    """subs: [(role, mode, key)]. One row per verdict, however many judge calls it took."""
    row = asdict(case)
    row.update(repeat=repeat, cached=cached, error=error, calls=len(subs))
    got = {role: payloads.get(key) for role, _, key in subs}
    if error or any(p is None for p in got.values()):
        row.update(raw=None, parsed_ok=False, verdict=None, score=None, winner=None,
                   abstained=False, flagged=None, flag_reason=None)
        return row
    modes = {role: mode for role, mode, _ in subs}
    parsed = {role: parse_verdict(p["text"], modes[role]) for role, p in got.items()}
    outcome = guards.combine(case, guard, parsed)
    if parsed.get("main") is None:
        outcome.update(verdict=None, score=None, winner=None)
    raw = got["main"]["text"] if len(got) == 1 else json.dumps({r: p["text"] for r, p in got.items()})
    row.update(
        raw=raw,
        parsed_ok=all(v is not None for v in parsed.values()),
        **outcome,
        # cost of the whole verdict: every call it needed
        latency_s=_sum([p.get("latency_s") for p in got.values()]),
        prompt_tokens=_sum([p.get("prompt_tokens") for p in got.values()]),
        completion_tokens=_sum([p.get("completion_tokens") for p in got.values()]),
        timings=got["main"].get("timings"),
    )
    return row


def run_audit(
    cfg: dict,
    *,
    split: str = "all",
    dry_run: bool = False,
    limit_items: int | None = None,
    use_cache: bool = True,
    judge=None,
    log=print,
) -> dict:
    cases = load_cases(cfg["task"], cfg["suite"], cfg["reference"])
    if split != "all":
        cases = [case for case in cases if case.split == split]
    if limit_items:
        keep = list(dict.fromkeys(case.item_id for case in cases))[:limit_items]
        cases = [case for case in cases if case.item_id in set(keep)]
    if not cases:
        raise ValueError("no cases to run (check the suite path and --split)")

    judge = judge or build_judge(cfg["judge"])
    fingerprint = dict(judge.fingerprint(), prompt_version=PROMPT_VERSION)
    style = cfg["prompt_style"]
    guard = guards.normalise_guard(cfg.get("guard"))
    # use_cache=False is for speed measurements: every call really hits the judge.
    cache = VerdictCache(cfg["cache"]) if use_cache else None

    # A verdict may need several judge calls (a guard asks in both orders, or screens
    # the answer first). Identical calls are made once: the swapped half of one pair is
    # often exactly another case's call.
    jobs = []  # (case, repeat, [(role, mode, key)])
    calls: dict = {}  # key -> (SubCall, repeat)
    for case in cases:
        planned = guards.plan_calls(case, style, guard)
        for repeat in range(int(cfg["repeats"])):
            subs = []
            for sub in planned:
                key = make_key(fingerprint, sub.messages, sub.schema, repeat)
                subs.append((sub.role, sub.mode, key))
                calls.setdefault(key, (sub, repeat))
            jobs.append((case, repeat, subs))

    payloads = {key: (cache.get(key) if cache is not None else None) for key in calls}
    pending = [(key, sub, repeat) for key, (sub, repeat) in calls.items() if payloads[key] is None]
    n_items = len({case.item_id for case in cases})
    prompt_chars = sum(len(m["content"]) for _, sub, _ in pending for m in sub.messages)
    guard_note = "" if not guards.is_active(guard) else f", guard {guards.describe(guard)}"
    log(
        f"[judgeaudit] {n_items} items, {len(jobs)} verdicts, {len(calls)} judge calls{guard_note}: "
        f"{len(calls) - len(pending)} cached, {len(pending)} to run "
        f"(~{prompt_chars // 4:,} prompt tokens)"
    )
    if dry_run:
        if cache is not None:
            cache.close()
        return {"dry_run": True, "n_verdicts": len(jobs), "n_calls": len(calls), "n_pending": len(pending)}

    errors: dict[str, str] = {}
    fresh: set[str] = set()
    aborted = False
    gate = PauseGate(os.environ.get("JUDGEAUDIT_PAUSE_FILE"), log=log)

    def call(request: JudgeRequest):
        gate.wait()
        return judge.judge(request)

    started = time.perf_counter()
    if pending:
        concurrency = int(cfg["concurrency"])
        # Circuit breaker: this many unreachable calls in a row means the server is gone.
        breaker = max(4, 2 * concurrency)
        unreachable_streak = 0
        pool = ThreadPoolExecutor(max_workers=concurrency)
        futures = {
            pool.submit(
                call,
                JudgeRequest(messages=sub.messages, mode=sub.mode, schema=sub.schema, repeat=rep, case=sub.case),
            ): key
            for key, sub, rep in pending
        }
        try:
            for done, future in enumerate(as_completed(futures), 1):
                key = futures[future]
                try:
                    response = future.result()
                except JudgeUnreachable as exc:
                    errors[key] = str(exc)
                    unreachable_streak += 1
                    if unreachable_streak >= breaker:
                        aborted = True
                        break
                except JudgeError as exc:
                    errors[key] = str(exc)
                    unreachable_streak = 0
                else:
                    unreachable_streak = 0
                    payload = asdict(response)
                    if cache is not None:
                        cache.put(key, payload)  # written as each call lands, so a crash loses nothing
                    payloads[key] = payload
                    fresh.add(key)
                if done % 50 == 0 or done == len(pending):
                    log(f"[judgeaudit] {done}/{len(pending)} calls done")
        finally:
            pool.shutdown(wait=True, cancel_futures=aborted)
        if aborted:
            for key in futures.values():
                if payloads[key] is None and key not in errors:
                    errors[key] = "not run: the judge server became unreachable and the run was stopped"
            log(
                f"[judgeaudit] judge server unreachable: stopped after {len(fresh)} of {len(pending)} calls. "
                "Finished calls are cached; restart the server and run again to resume."
            )
    wall_s = time.perf_counter() - started
    # Throughput is measured over the time the judge was allowed to work.
    active_s = max(wall_s - gate.paused_s, 1e-9)
    if cache is not None:
        cache.close()

    rows = []
    for case, repeat, subs in jobs:
        keys = [key for _, _, key in subs]
        error = next((errors[k] for k in keys if k in errors), None)
        rows.append(_row(case, repeat, subs, payloads, guard, cached=not any(k in fresh for k in keys), error=error))
    calls_per_verdict = sum(len(subs) for _, _, subs in jobs) / len(jobs)
    calls_per_s = round(len(fresh) / active_s, 3) if fresh and wall_s > 0 else None
    run_info = {
        "run_name": cfg["run_name"],
        "judgeaudit_version": __version__,
        "task": cfg["task"],
        "suite": str(cfg["suite"]),
        "suite_sha256": _file_hash(cfg["suite"]),
        "split": split,
        "reference": cfg["reference"],
        "prompt_style": style,
        "prompt_version": PROMPT_VERSION,
        "guard": guard,
        "guard_name": guards.describe(guard),
        "calls_per_verdict": round(calls_per_verdict, 3),
        "repeats": int(cfg["repeats"]),
        "concurrency": int(cfg["concurrency"]),
        "judge": fingerprint,
        "new_calls": len(fresh),
        "cached_calls": len(jobs) - len(pending),
        "failed_calls": len(errors),
        "wall_s": round(wall_s, 3),
        "paused_s": round(gate.paused_s, 3),
        "pauses": gate.pauses,
        "calls_per_s": calls_per_s,
        # what a deployment would get: judge calls per second / calls each verdict needs
        "verdicts_per_s": round(calls_per_s / calls_per_verdict, 3) if calls_per_s else None,
        "use_cache": use_cache,
        "aborted": aborted,
        "meta": cfg.get("meta") or {},
    }
    out_dir = Path(cfg["out_dir"]) / cfg["run_name"]
    if not fresh:
        # A fully cached re-run measures no speed: keep the figure from the run that did.
        previous = _previous_run(out_dir)
        if (
            previous.get("calls_per_s")
            and previous.get("judge") == fingerprint
            and previous.get("concurrency") == run_info["concurrency"]
        ):
            run_info["calls_per_s"] = previous["calls_per_s"]
            run_info["verdicts_per_s"] = round(previous["calls_per_s"] / calls_per_verdict, 3)
            run_info["throughput_from_earlier_run"] = True
            # The hardware note belongs to the run that measured the speed (e.g. the
            # GPU power limit at the time), not to this re-read from the cache.
            for k, v in (previous.get("meta") or {}).items():
                if k in ("gpu_power_limit_w", "vram_mib"):
                    run_info["meta"][k] = v
    summary = compute_summary(rows, cfg["thresholds"], run_info, seed=int(cfg["bootstrap_seed"]))
    if split == "all":
        # The same run scored on each half of the suite: choose a configuration on
        # "dev", report it on "heldout", with no extra judge calls.
        summary["splits"] = {}
        for name in sorted({row["split"] for row in rows}):
            part = compute_summary([r for r in rows if r["split"] == name], cfg["thresholds"],
                                   run_info, seed=int(cfg["bootstrap_seed"]))
            summary["splits"][name] = {k: part[k] for k in ("verdict", "passed", "n_items", "metrics", "checks")}

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "results.jsonl", "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(out_dir / "config.resolved.yaml", "w", encoding="utf-8") as handle:
        yaml.safe_dump(cfg, handle, sort_keys=False)
    write_reports(summary, out_dir)
    log(f"[judgeaudit] verdict: {summary['verdict']}")
    log(f"[judgeaudit] report: {out_dir / 'report.html'}")
    if errors:
        log(f"[judgeaudit] {len(errors)} calls failed; re-run to retry them. First: {next(iter(errors.values()))}")
    return summary
