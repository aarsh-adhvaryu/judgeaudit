"""Put finished runs side by side: reliability in one table, cost in another."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .report import fmt

RELIABILITY = [
    ("balanced_accuracy", "Balanced accuracy"),
    ("pointwise_accuracy", "Accuracy"),
    ("pair_accuracy", "Pair accuracy"),
    ("flip_to_accept.injection", "Injection accepted"),
    ("flip_to_accept.injection_unseen", "Unseen injection accepted"),
    ("flip_to_accept.injection_fresh", "Fresh injection accepted"),
    ("flip_to_accept.authority", "Authority accepted"),
    ("flip_to_accept.fluent", "Fluent accepted"),
    ("flip_to_accept.padded", "Padded wrong accepted"),
    ("flip_to_reject.padded", "Padded correct rejected"),
    ("position_inconsistency_cw", "Position flips"),
    ("abstain_rate", "Withheld"),
    ("screen.flag_rate_correct", "Screen false alarms"),
    ("parse_failure_rate", "Parse failures"),
    ("repeat_agreement", "Repeat agreement"),
]


def verdicts_per_s(run: dict) -> float | None:
    if run.get("verdicts_per_s"):
        return run["verdicts_per_s"]
    if run.get("calls_per_s"):
        return run["calls_per_s"] / run.get("calls_per_verdict", 1)
    return None


def load_runs(runs_dir: str | Path, include_mock: bool = False) -> list[dict]:
    runs = []
    for path in sorted(Path(runs_dir).glob("*/summary.json")):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not include_mock and summary["run"]["judge"].get("kind") == "mock":
            continue
        summary["dir"] = path.parent.name
        runs.append(summary)
    return runs


def _num(value, pattern: str) -> str:
    return "" if value is None else pattern.format(value)


def _status(summary: dict) -> str:
    if summary.get("failed_calls") or summary.get("unevaluated"):
        return "INCOMPLETE"
    checks = summary["checks"]
    failed = sum(1 for c in checks if c["passed"] is False)
    return f"{failed}/{len(checks)} failed" if checks else ""


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return lines + ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]


def render_comparison(runs: list[dict]) -> str:
    out = ["# Run comparison", "", f"{len(runs)} runs. Rates are per base item; see each run's card for intervals.", ""]
    base = next((r.get("baselines", {}).get("always_incorrect") for r in runs if r.get("baselines")), None)
    if base:
        out += [f"Baseline: a judge that always answers \"incorrect\" scores {100 * base['pointwise_accuracy']:.1f}% "
                "accuracy on this suite but 50% balanced accuracy. Compare judges on balanced accuracy.", ""]
    names = [name for name, _ in RELIABILITY if any(name in r["metrics"] for r in runs)]
    labels = dict(RELIABILITY)
    rows = []
    for r in runs:
        run = r["run"]
        rows.append(
            [f"`{r['dir']}`", run["prompt_style"], run["reference"], run.get("guard_name", "none"), r["n_items"], _status(r)]
            + [fmt(n, r["metrics"][n]["value"]) if n in r["metrics"] else "" for n in names]
        )
    out += ["## Reliability", ""]
    out += _table(["Run", "Prompt", "Reference", "Guard", "Items", "Checks"] + [labels[n] for n in names], rows)

    rows = []
    for r in runs:
        run, perf, meta = r["run"], r["perf"], r["run"].get("meta") or {}
        rows.append(
            [
                f"`{r['dir']}`",
                _num(meta.get("model_gb"), "{:.2f}"),
                _num(meta.get("vram_mib"), "{:.0f}"),
                _num(meta.get("gpu_power_limit_w"), "{:.0f}"),
                run["concurrency"],
                "no" if run.get("use_cache") is False else "yes",
                _num(run.get("calls_per_verdict", 1), "{:g}"),
                _num(verdicts_per_s(run), "{:.2f}"),
                _num(perf.get("latency_p50_s") and perf["latency_p50_s"] * 1000, "{:.0f}"),
                _num(perf.get("latency_p95_s") and perf["latency_p95_s"] * 1000, "{:.0f}"),
                _num(perf.get("prompt_tokens_mean"), "{:.0f}"),
                _num(perf.get("server_prompt_per_second_mean"), "{:.0f}"),
                _num(perf.get("server_predicted_per_second_mean"), "{:.0f}"),
            ]
        )
    out += ["", "## Cost and speed", ""]
    out += _table(
        ["Run", "Model GB", "VRAM used MiB", "GPU W", "Concurrency", "Verdict cache", "Calls/verdict", "Verdicts/s",
         "p50 ms", "p95 ms", "Prompt tokens", "Prefill tok/s", "Decode tok/s"],
        rows,
    )
    out += [
        "",
        "Verdicts/s is measured on calls that really ran, divided by the judge calls each verdict "
        "needs. GPU W is the power limit the laptop allowed while it was measured. VRAM is the "
        "whole GPU's used memory after the model loaded, so it includes other applications.",
        "",
    ]
    return "\n".join(out)


def write_comparison(runs_dir: str | Path, out_dir: str | Path, include_mock: bool = False) -> int:
    runs = load_runs(runs_dir, include_mock)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "comparison.md").write_text(render_comparison(runs), encoding="utf-8")

    metric_names = sorted({name for r in runs for name in r["metrics"]})
    perf_names = sorted({name for r in runs for name in r["perf"]})
    meta_names = sorted({name for r in runs for name in (r["run"].get("meta") or {})})
    with open(out_dir / "comparison.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        header = ["run", "label", "prompt_style", "reference", "guard", "split", "repeats", "concurrency",
                  "n_items", "status", "calls_per_s", "calls_per_verdict", "verdicts_per_s", "use_cache"]
        header += [f"meta.{n}" for n in meta_names] + [f"perf.{n}" for n in perf_names]
        for name in metric_names:
            header += [name, f"{name}.ci_low", f"{name}.ci_high"]
        writer.writerow(header)
        for r in runs:
            run, meta = r["run"], r["run"].get("meta") or {}
            row = [r["dir"], run["judge"].get("label", ""), run["prompt_style"], run["reference"],
                   run.get("guard_name", "none"), run["split"], run["repeats"], run["concurrency"], r["n_items"],
                   _status(r), run.get("calls_per_s"), run.get("calls_per_verdict", 1), verdicts_per_s(run),
                   run.get("use_cache", True)]
            row += [meta.get(n, "") for n in meta_names] + [r["perf"].get(n, "") for n in perf_names]
            for name in metric_names:
                m = r["metrics"].get(name)
                row += [m["value"], m["ci_low"], m["ci_high"]] if m else ["", "", ""]
            writer.writerow(row)
    return len(runs)
