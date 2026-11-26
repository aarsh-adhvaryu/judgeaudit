"""Render the reliability card (Markdown and self-contained HTML) from a summary."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .metrics import LABELS, is_score_metric

SECTIONS = [
    ("Accuracy against ground truth", ("pointwise_accuracy", "pair_accuracy", "acc.")),
    ("Bias: how often a manipulation flips the verdict", ("flip_to_accept.", "flip_to_reject.")),
    ("Bias: score shift on the 1-5 scale", ("score_shift.",)),
    (
        "Position and length preference in pairwise mode",
        ("position_inconsistency", "first_position_rate", "verbosity_preference"),
    ),
    ("Output robustness", ("parse_failure_rate", "repeat_agreement")),
]


def fmt(name: str, value: float | None) -> str:
    if value is None:
        return "n/a"
    if is_score_metric(name):
        return f"{value:+.2f}"
    return f"{100 * value:.1f}%"


def _rows(summary: dict, prefixes: tuple) -> list[tuple]:
    checks = {c["metric"]: c for c in summary["checks"]}
    out = []
    for name, m in summary["metrics"].items():
        if not name.startswith(prefixes):
            continue
        check = checks.get(name)
        if check is None:
            limit, status = "", ""
        else:
            limit = f"{'at least' if check['op'] == 'min' else 'at most'} {fmt(name, check['limit'])}"
            status = {True: "PASS", False: "FAIL", None: "n/a"}[check["passed"]]
        ci = f"{fmt(name, m['ci_low'])} to {fmt(name, m['ci_high'])}"
        out.append((LABELS.get(name, name), name, fmt(name, m["value"]), ci, m["n_items"], limit, status))
    return out


def _failures(summary: dict) -> list[str]:
    lines = []
    for check in summary["checks"]:
        if check["passed"] is False:
            name = check["metric"]
            bound = "at least" if check["op"] == "min" else "at most"
            lines.append(
                f"{LABELS.get(name, name)}: {fmt(name, check['value'])} "
                f"(limit {bound} {fmt(name, check['limit'])})"
            )
    return lines


def _incomplete(summary: dict) -> list[str]:
    lines = []
    if summary.get("failed_calls"):
        lines.append(
            f"{summary['failed_calls']} judge calls failed (server unreachable or erroring). "
            "Re-run to retry them; the numbers below cover only the calls that succeeded."
        )
    for name in summary.get("unevaluated", []):
        lines.append(f"Could not be measured: {LABELS.get(name, name)}")
    return lines


def _perf_lines(summary: dict) -> list[tuple[str, str]]:
    perf, run = summary["perf"], summary["run"]
    lines = [
        ("Judge calls this run", f"{run['new_calls']} new, {run['cached_calls']} from cache, {run['failed_calls']} failed"),
    ]
    if run.get("calls_per_s"):
        lines.append(("Throughput (new calls)", f"{run['calls_per_s']:.2f} verdicts/s at concurrency {run['concurrency']}"))
    if "latency_mean_s" in perf:
        lines.append(
            ("Latency per verdict", f"mean {perf['latency_mean_s'] * 1000:.0f} ms, p50 {perf['latency_p50_s'] * 1000:.0f} ms, p95 {perf['latency_p95_s'] * 1000:.0f} ms")
        )
    if "prompt_tokens_mean" in perf:
        lines.append(
            ("Tokens per verdict", f"{perf['prompt_tokens_mean']:.0f} prompt, {perf.get('completion_tokens_mean', 0):.0f} completion")
        )
    if "server_prompt_per_second_mean" in perf:
        lines.append(("Prefill speed (server)", f"{perf['server_prompt_per_second_mean']:.0f} tokens/s"))
    if "server_predicted_per_second_mean" in perf:
        lines.append(("Decode speed (server)", f"{perf['server_predicted_per_second_mean']:.0f} tokens/s"))
    return lines


def render_markdown(summary: dict) -> str:
    run = summary["run"]
    out = [f"# Judge reliability card: {run['run_name']}", "", f"**{summary['verdict']}**", ""]
    failures = _failures(summary)
    if failures:
        out += ["## Do not trust this judge when", ""] + [f"- {line}" for line in failures] + [""]
    incomplete = _incomplete(summary)
    if incomplete:
        out += ["## Incomplete run", ""] + [f"- {line}" for line in incomplete] + [""]
    out += [
        f"Suite `{run['suite']}` ({run['suite_sha256']}), split `{run['split']}`, "
        f"{summary['n_items']} items, {summary['n_rows']} verdicts, "
        f"prompt `{run['prompt_style']}/{run['prompt_version']}`, reference `{run['reference']}`.",
        "",
    ]
    for title, prefixes in SECTIONS:
        rows = _rows(summary, prefixes)
        if not rows:
            continue
        out += [f"## {title}", "", "| Metric | Value | 95% CI | Items | Limit | Status |", "|---|---|---|---|---|---|"]
        out += [f"| {label} | {value} | {ci} | {n} | {limit} | {status} |" for label, _, value, ci, n, limit, status in rows]
        out.append("")
    out += ["## Cost and speed", ""] + [f"- {k}: {v}" for k, v in _perf_lines(summary)] + [""]
    if summary["fooled_examples"]:
        out += ["## Cases where the judge was fooled", ""]
        for ex in summary["fooled_examples"]:
            answer = ex["answer"].replace("\n", " ")
            out.append(
                f"- `{ex['case_id']}` {ex['question']} Answer: \"{answer}\" "
                f"Expected {ex['expected']}, judge said {ex['judge_said']}."
            )
        out.append("")
    out += ["## Judge", "", "```json", json.dumps(run["judge"], indent=2), "```", ""]
    return "\n".join(out)


_CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#5f6368;--line:#dadce0;--pass:#137333;--fail:#b3261e;--card:#f8f9fa}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--fg:#e8eaed;--muted:#9aa0a6;--line:#3c4043;--pass:#81c995;--fail:#f28b82;--card:#202124}}
body{font:15px/1.5 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--fg);max-width:980px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.5rem;margin-bottom:.25rem}h2{font-size:1.1rem;margin-top:2rem}
.verdict{font-size:1.15rem;font-weight:600;padding:.75rem 1rem;border-radius:8px;background:var(--card);border-left:6px solid var(--line)}
.verdict.pass{border-color:var(--pass)}.verdict.fail{border-color:var(--fail)}
.meta{color:var(--muted);font-size:.9rem}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.4rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:.85rem}td.num{white-space:nowrap;font-variant-numeric:tabular-nums}
.PASS{color:var(--pass);font-weight:600}.FAIL{color:var(--fail);font-weight:600}
.ex{background:var(--card);border-radius:8px;padding:.6rem .9rem;margin:.6rem 0}.ex pre{white-space:pre-wrap;margin:.3rem 0;font:13px/1.4 ui-monospace,Consolas,monospace}
pre.json{background:var(--card);padding:.8rem;border-radius:8px;overflow:auto;font:13px/1.4 ui-monospace,Consolas,monospace}
"""


def render_html(summary: dict) -> str:
    e = html.escape
    run = summary["run"]
    state = "pass" if summary["passed"] else ("fail" if summary["checks"] else "")
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Judge reliability card: {e(run['run_name'])}</title><style>{_CSS}</style></head><body>",
        f"<h1>Judge reliability card: {e(run['run_name'])}</h1>",
        f"<p class='meta'>Suite {e(run['suite'])} ({e(run['suite_sha256'])}) · split {e(run['split'])} · "
        f"{summary['n_items']} items · {summary['n_rows']} verdicts · prompt {e(run['prompt_style'])}/{e(run['prompt_version'])} · "
        f"reference {e(run['reference'])}</p>",
        f"<p class='verdict {state}'>{e(summary['verdict'])}</p>",
    ]
    failures = _failures(summary)
    if failures:
        parts.append("<h2>Do not trust this judge when</h2><ul>")
        parts += [f"<li>{e(line)}</li>" for line in failures]
        parts.append("</ul>")
    incomplete = _incomplete(summary)
    if incomplete:
        parts.append("<h2>Incomplete run</h2><ul>")
        parts += [f"<li>{e(line)}</li>" for line in incomplete]
        parts.append("</ul>")
    for title, prefixes in SECTIONS:
        rows = _rows(summary, prefixes)
        if not rows:
            continue
        parts.append(
            f"<h2>{e(title)}</h2><table><tr><th>Metric</th><th>Value</th><th>95% CI</th>"
            "<th>Items</th><th>Limit</th><th>Status</th></tr>"
        )
        for label, name, value, ci, n, limit, status in rows:
            parts.append(
                f"<tr><td title='{e(name)}'>{e(label)}</td><td class='num'>{e(value)}</td>"
                f"<td class='num'>{e(ci)}</td><td class='num'>{n}</td><td class='num'>{e(limit)}</td>"
                f"<td class='{e(status)}'>{e(status)}</td></tr>"
            )
        parts.append("</table>")
    parts.append("<h2>Cost and speed</h2><table>")
    parts += [f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in _perf_lines(summary)]
    parts.append("</table>")
    if summary["fooled_examples"]:
        parts.append("<h2>Cases where the judge was fooled</h2>")
        for ex in summary["fooled_examples"]:
            parts.append(
                f"<div class='ex'><strong>{e(ex['question'])}</strong> <span class='meta'>{e(ex['case_id'])}</span>"
                f"<pre>{e(ex['answer'])}</pre>"
                f"<span class='meta'>Expected {e(ex['expected'])}, judge said {e(str(ex['judge_said']))}</span></div>"
            )
    parts.append(f"<h2>Judge</h2><pre class='json'>{e(json.dumps(run['judge'], indent=2))}</pre>")
    parts.append("</body></html>")
    return "\n".join(parts)


def write_reports(summary: dict, out_dir: str | Path) -> None:
    out_dir = Path(out_dir)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(render_markdown(summary), encoding="utf-8")
    (out_dir / "report.html").write_text(render_html(summary), encoding="utf-8")
