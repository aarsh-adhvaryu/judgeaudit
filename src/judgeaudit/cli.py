from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import load_config
from .judges import JudgeError
from .metrics import compute_summary
from .report import write_reports
from .runner import run_audit


def _cmd_run(args) -> int:
    cfg = load_config(args.config)
    if args.run_name:
        cfg["run_name"] = args.run_name
    if args.cache:
        cfg["cache"] = args.cache
    summary = run_audit(cfg, split=args.split, dry_run=args.dry_run, limit_items=args.limit_items)
    if summary.get("dry_run"):
        return 0
    return 1 if args.gate and not summary["passed"] else 0


def _cmd_report(args) -> int:
    run_dir = Path(args.run_dir)
    old = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    with open(run_dir / "results.jsonl", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    thresholds = load_config(args.config)["thresholds"] if args.config else {
        c["metric"]: {c["op"]: c["limit"]} for c in old["checks"]
    }
    summary = compute_summary(rows, thresholds, old["run"])
    write_reports(summary, run_dir)
    print(f"[judgeaudit] verdict: {summary['verdict']}")
    print(f"[judgeaudit] report: {run_dir / 'report.html'}")
    return 1 if args.gate and not summary["passed"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="judgeaudit",
        description="Audit an LLM-as-judge against known-ground-truth test cases.",
    )
    parser.add_argument("--version", action="version", version=f"judgeaudit {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run an audit and write a reliability card")
    run.add_argument("-c", "--config", required=True)
    run.add_argument("--split", choices=("all", "dev", "heldout"), default="all",
                     help="tune prompts on dev, report on heldout")
    run.add_argument("--dry-run", action="store_true", help="count calls and tokens, call nothing")
    run.add_argument("--limit-items", type=int, help="only the first N base items")
    run.add_argument("--run-name", help="override run_name from the config")
    run.add_argument("--cache", help="override the cache path from the config")
    run.add_argument("--gate", action="store_true", help="exit 1 when a threshold fails (for CI)")
    run.set_defaults(func=_cmd_run)

    report = sub.add_parser("report", help="rebuild the card from a finished run, optionally with new thresholds")
    report.add_argument("run_dir")
    report.add_argument("-c", "--config", help="take thresholds from this config instead")
    report.add_argument("--gate", action="store_true")
    report.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError, JudgeError) as exc:
        print(f"judgeaudit: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
