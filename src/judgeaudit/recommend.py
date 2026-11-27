"""Pick the cheapest judge set-up that can be trusted, and say what it really scores.

Selection uses only the "dev" half of the suite; the numbers reported for the
chosen set-up come from the "heldout" half, which played no part in choosing it.
So the recommendation is not flattered by having been tuned on its own test.

A set-up is one model (and quantization) with one prompt, one reference policy
and one guard. Its cost is what a deployment pays per verdict: the judge
calls it needs, at the call rate measured for that model on this machine.
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

from .compare import load_runs
from .report import fmt

KEY_METRICS = [
    ("balanced_accuracy", "Balanced accuracy"),
    ("pointwise_accuracy", "Accuracy"),
    ("pair_accuracy", "Pair accuracy"),
    ("flip_to_accept.injection", "Injection accepted"),
    ("flip_to_accept.injection_unseen", "Unseen injection accepted"),
    ("flip_to_accept.injection_fresh", "Fresh injection accepted"),
    ("flip_to_reject.padded", "Padded correct rejected"),
    ("position_inconsistency_cw", "Position flips"),
    ("abstain_rate", "Withheld"),
]
USE_CASES = [
    ("given", "You have a reference answer for each question"),
    ("none", "You have no reference answer"),
]


def _model_speed(runs: list[dict]) -> dict:
    """Judge calls per second for each model, from runs that made enough fresh calls to measure it."""
    rates = defaultdict(list)
    for r in runs:
        run = r["run"]
        model = (run.get("meta") or {}).get("model")
        if model and run.get("calls_per_s") and run.get("new_calls", 0) >= 20 and not run.get("throughput_from_earlier_run"):
            rates[model].append(run["calls_per_s"])
    return {model: statistics.median(values) for model, values in rates.items()}


def candidates(runs_dir: str | Path, include_mock: bool = False) -> list[dict]:
    # Repeated runs are decoding experiments (the same judge asked several times), not set-ups.
    runs = [r for r in load_runs(runs_dir, include_mock)
            if r.get("splits") and {"dev", "heldout"} <= set(r["splits"]) and int(r["run"].get("repeats", 1)) == 1]
    speed = _model_speed(runs)
    out = []
    for r in runs:
        run, meta = r["run"], r["run"].get("meta") or {}
        model = meta.get("model", run["judge"].get("label", "?"))
        dev, held = r["splits"]["dev"], r["splits"]["heldout"]
        calls_per_s = speed.get(model)
        per_verdict = run.get("calls_per_verdict", 1)
        out.append(
            {
                "run": r["dir"],
                "model": model,
                "model_gb": meta.get("model_gb"),
                "vram_mib": meta.get("vram_mib"),
                "prompt": run["prompt_style"],
                "reference": run["reference"],
                "guard": run.get("guard_name", "none"),
                "calls_per_verdict": per_verdict,
                "verdicts_per_s": calls_per_s / per_verdict if calls_per_s else None,
                "dev_failed": [c["metric"] for c in dev["checks"] if c["passed"] is False],
                "dev_unmeasured": [c["metric"] for c in dev["checks"] if c["passed"] is None],
                "dev_passed": dev["passed"],
                # balanced accuracy when the suite has both kinds of answer, else raw accuracy
                "dev_accuracy": (dev["metrics"].get("balanced_accuracy") or dev["metrics"].get("pointwise_accuracy") or {}).get("value"),
                "baselines": r.get("baselines", {}),
                "heldout_passed": held["passed"],
                "heldout_failed": [c["metric"] for c in held["checks"] if c["passed"] is False],
                "heldout": {name: held["metrics"].get(name) for name, _ in KEY_METRICS},
                "heldout_items": held["n_items"],
            }
        )
    return out


def _rank(c: dict) -> tuple:
    # fewest failed checks on dev, then most accurate on dev, then fastest, then smallest
    return (
        len(c["dev_failed"]) + len(c["dev_unmeasured"]),
        -(c["dev_accuracy"] or 0),
        -(c["verdicts_per_s"] or 0),
        c["vram_mib"] or 1e9,
    )


def choose(cands: list[dict]) -> dict:
    """For each use case: the best set-up overall, the cheapest one that passes, and the best per model."""
    result = {}
    for ref, _ in USE_CASES:
        pool = [c for c in cands if c["reference"] == ref]
        if not pool:
            continue
        trusted = [c for c in pool if c["dev_passed"]]
        cheapest = max(trusted, key=lambda c: ((c["verdicts_per_s"] or 0), -(c["vram_mib"] or 1e9))) if trusted else None
        per_model = {}
        for c in sorted(pool, key=_rank):
            per_model.setdefault(c["model"], c)
        # Pareto front on dev: no other set-up is both at least as trustworthy and faster.
        front = []
        for c in pool:
            dominated = any(
                (len(o["dev_failed"]) <= len(c["dev_failed"]) and (o["verdicts_per_s"] or 0) > (c["verdicts_per_s"] or 0))
                or (len(o["dev_failed"]) < len(c["dev_failed"]) and (o["verdicts_per_s"] or 0) >= (c["verdicts_per_s"] or 0))
                for o in pool
            )
            if not dominated:
                front.append(c)
        result[ref] = {
            "best": min(pool, key=_rank),
            "cheapest_trusted": cheapest,
            "per_model": list(per_model.values()),
            "pareto": sorted(front, key=lambda c: -(c["verdicts_per_s"] or 0)),
        }
    return result


def speed(c: dict) -> str:
    return "n/a" if c.get("verdicts_per_s") is None else f"{c['verdicts_per_s']:.1f}"


def _cell(c: dict, name: str) -> str:
    m = c["heldout"].get(name)
    if not m:
        return ""
    return f"{fmt(name, m['value'])} ({fmt(name, m['ci_low'])}-{fmt(name, m['ci_high'])})"


def _setup(c: dict) -> str:
    return f"`{c['model']}` · prompt {c['prompt']} · guard {c['guard']}"


def _value(c: dict | None, name: str) -> float | None:
    m = (c or {}).get("heldout", {}).get(name)
    return None if not m else m["value"]


def _pct(value: float | None) -> str:
    return "" if value is None else f"{100 * value:.1f}%"


def _injection(c: dict | None) -> float | None:
    values = [v for v in (_value(c, n) for n in ("flip_to_accept.injection", "flip_to_accept.injection_unseen",
                                                  "flip_to_accept.injection_fresh")) if v is not None]
    return sum(values) / len(values) if values else None


def baseline_table(cands: list[dict], chosen: dict) -> list[str]:
    """Each model's plain judge (naive prompt, no guard) against its best set-up, held-out."""
    base = next((c["baselines"].get("always_incorrect") for c in cands if c.get("baselines")), None)
    out = ["## Against the baselines", ""]
    if base:
        out += [f"A judge that always answers \"incorrect\" scores {100 * base['pointwise_accuracy']:.1f}% accuracy on this "
                "suite, because most single answers in it are wrong, but only 50% balanced accuracy. The plain judge is "
                "what most teams deploy: the naive prompt and no guard. All numbers are held-out.", ""]
    header = ["Model", "Reference", "Plain judge: balanced accuracy", "Plain judge: injections accepted",
              "Best set-up", "Best: balanced accuracy", "Best: injections accepted", "Checks failed: plain to best"]
    out += ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for ref, _ in USE_CASES:
        for best in (chosen.get(ref) or {}).get("per_model", []):
            plain = next((c for c in cands if c["model"] == best["model"] and c["reference"] == ref
                          and c["prompt"] == "naive" and c["guard"] == "none"), None)
            if plain is None:
                continue
            out.append("| " + " | ".join([
                f"`{best['model']}`", ref,
                _pct(_value(plain, "balanced_accuracy")), _pct(_injection(plain)),
                f"prompt {best['prompt']} · guard {best['guard']}",
                _pct(_value(best, "balanced_accuracy")), _pct(_injection(best)),
                f"{len(plain['heldout_failed'])} to {len(best['heldout_failed'])}",
            ]) + " |")
    out += ["", "Injections accepted is the mean over the three injection sets (tuning, unseen, fresh).", ""]
    return out


def render(cands: list[dict], chosen: dict) -> str:
    out = [
        "# Which judge set-up to use",
        "",
        "Chosen on the dev half of the suite; every number below is measured on the held-out half, "
        "which played no part in the choice. Ranges are 95% bootstrap intervals over items.",
        "",
    ]
    for ref, title in USE_CASES:
        if ref not in chosen:
            continue
        c = chosen[ref]
        best, cheap = c["best"], c["cheapest_trusted"]
        out += [f"## {title}", ""]
        if cheap:
            out.append(f"**Use {_setup(cheap)}.** It is the fastest set-up that passed every check on dev "
                       f"({speed(cheap)} verdicts/s, {cheap['calls_per_verdict']:g} judge calls per verdict, "
                       f"{cheap['vram_mib']} MiB VRAM in use).")
            held = "passed every check" if cheap["heldout_passed"] else "failed " + ", ".join(cheap["heldout_failed"])
            out.append(f"On held-out items it {held}.")
        else:
            out.append(f"**No set-up passed every check on dev.** The closest is {_setup(best)}, which failed "
                       + ", ".join(best["dev_failed"]) + ". Do not use an LLM judge unattended for this case.")
        out.append("")
        header = ["Set-up", "Verdicts/s", "Calls/verdict", "Dev checks failed"] + [label for _, label in KEY_METRICS]
        out += ["Best set-up for each model (held-out numbers):", "",
                "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        for m in c["per_model"]:
            vps = f"{m['verdicts_per_s']:.1f}" if m["verdicts_per_s"] else ""
            failed = ", ".join(x.replace("flip_to_", "").replace("position_inconsistency_cw", "position") for x in m["dev_failed"]) or "none"
            out.append("| " + " | ".join([_setup(m), vps, f"{m['calls_per_verdict']:g}", failed]
                                         + [_cell(m, n) for n, _ in KEY_METRICS]) + " |")
        out += ["", "Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):", ""]
        for p in c["pareto"]:
            vps = f"{p['verdicts_per_s']:.1f}" if p["verdicts_per_s"] else "?"
            out.append(f"- {_setup(p)}: {len(p['dev_failed'])} dev checks failed, {vps} verdicts/s")
        out.append("")
    out += baseline_table(cands, chosen)
    out += [f"{len(cands)} set-ups compared. Full numbers: `comparison.csv`; per-run cards: `runs/<run>/report.html`.", ""]
    return "\n".join(out)


def write_recommendation(runs_dir: str | Path, out_dir: str | Path, include_mock: bool = False) -> dict:
    cands = candidates(runs_dir, include_mock)
    chosen = choose(cands)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "recommendation.md").write_text(render(cands, chosen), encoding="utf-8")
    (out_dir / "recommendation.json").write_text(json.dumps({"candidates": cands, "chosen": chosen}, indent=2), encoding="utf-8")
    return {"candidates": cands, "chosen": chosen}
