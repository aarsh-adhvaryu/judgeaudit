"""Run an audit: build cases, ask the judge (through the cache), write results."""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import yaml

from . import __version__
from .cache import VerdictCache, make_key
from .judges import JudgeError, JudgeRequest, JudgeUnreachable, build_judge
from .metrics import compute_summary
from .parsing import parse_verdict
from .prompts import PROMPT_VERSION, build_messages, schema_for
from .report import write_reports
from .tasks import load_cases


def _file_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def _previous_run(out_dir: Path) -> dict:
    try:
        return json.loads((out_dir / "summary.json").read_text(encoding="utf-8")).get("run", {})
    except (OSError, ValueError):
        return {}


def _row(case, repeat: int, payload: dict | None, cached: bool, error: str | None) -> dict:
    row = asdict(case)
    row.update(repeat=repeat, cached=cached, error=error)
    if payload is None:
        row.update(raw=None, parsed_ok=False, verdict=None, score=None, winner=None)
        return row
    parsed = parse_verdict(payload["text"], case.mode) or {}
    row.update(
        raw=payload["text"],
        parsed_ok=bool(parsed),
        verdict=parsed.get("verdict"),
        score=parsed.get("score"),
        winner=parsed.get("winner"),
        latency_s=payload.get("latency_s"),
        prompt_tokens=payload.get("prompt_tokens"),
        completion_tokens=payload.get("completion_tokens"),
        timings=payload.get("timings"),
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
    # use_cache=False is for speed measurements: every call really hits the judge.
    cache = VerdictCache(cfg["cache"]) if use_cache else None

    jobs = []
    for case in cases:
        messages = build_messages(case, style)
        schema = schema_for(case.mode)
        for repeat in range(int(cfg["repeats"])):
            key = make_key(fingerprint, messages, schema, repeat)
            jobs.append((key, case, repeat, messages, schema))

    payloads = {key: (cache.get(key) if cache is not None else None) for key, *_ in jobs}
    pending = [job for job in jobs if payloads[job[0]] is None]
    n_items = len({case.item_id for case in cases})
    prompt_chars = sum(len(m["content"]) for _, _, _, msgs, _ in pending for m in msgs)
    log(
        f"[judgeaudit] {n_items} items, {len(jobs)} judge calls: "
        f"{len(jobs) - len(pending)} cached, {len(pending)} to run "
        f"(~{prompt_chars // 4:,} prompt tokens)"
    )
    if dry_run:
        if cache is not None:
            cache.close()
        return {"dry_run": True, "n_calls": len(jobs), "n_pending": len(pending)}

    errors: dict[str, str] = {}
    fresh: set[str] = set()
    aborted = False
    started = time.perf_counter()
    if pending:
        concurrency = int(cfg["concurrency"])
        # Circuit breaker: this many unreachable calls in a row means the server is gone.
        breaker = max(4, 2 * concurrency)
        unreachable_streak = 0
        pool = ThreadPoolExecutor(max_workers=concurrency)
        futures = {
            pool.submit(
                judge.judge,
                JudgeRequest(messages=msgs, mode=case.mode, schema=schema, repeat=rep, case=case),
            ): key
            for key, case, rep, msgs, schema in pending
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
    if cache is not None:
        cache.close()

    rows = [
        _row(case, repeat, payloads[key], cached=key not in fresh, error=errors.get(key))
        for key, case, repeat, _, _ in jobs
    ]
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
        "repeats": int(cfg["repeats"]),
        "concurrency": int(cfg["concurrency"]),
        "judge": fingerprint,
        "new_calls": len(fresh),
        "cached_calls": len(jobs) - len(pending),
        "failed_calls": len(errors),
        "wall_s": round(wall_s, 3),
        "calls_per_s": round(len(fresh) / wall_s, 3) if fresh and wall_s > 0 else None,
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
            run_info["throughput_from_earlier_run"] = True
    summary = compute_summary(rows, cfg["thresholds"], run_info, seed=int(cfg["bootstrap_seed"]))

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
