"""One self-contained HTML page for exploring every audit: the demo.

Three views, no server and no dependencies: the recommended set-ups, a
trust-against-cost chart of every set-up, and a case browser that shows exactly
which answers fooled a chosen judge.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from .recommend import KEY_METRICS, USE_CASES, candidates, choose

PALETTE = ["#4269d0", "#efb118", "#ff725c", "#6cc5b0", "#a463f2", "#97bbf5", "#9c6b4e", "#3ca951"]


def _codes(rows: list[dict], order: list[str]) -> tuple[str, str]:
    by_id = {r["case_id"]: r for r in rows if int(r.get("repeat") or 0) == 0}
    verdicts, flags = [], []
    for cid in order:
        r = by_id.get(cid)
        if r is None or r.get("error"):
            verdicts.append("?")
        elif r.get("abstained"):
            verdicts.append("-")
        elif r["mode"] == "pointwise":
            verdicts.append({"correct": "c", "incorrect": "i"}.get(r.get("verdict"), "?"))
        else:
            verdicts.append(r.get("winner") or "?")
        flags.append({True: "1", False: "0"}.get(r.get("flagged") if r else None, "."))
    return "".join(verdicts), "".join(flags)


def _scatter(points: list[dict], models: list[str], title: str) -> str:
    w, h, left, bottom, top, right = 460, 300, 52, 40, 28, 16
    xs = [p["x"] for p in points if p["x"]] or [1]
    x_max = max(xs) * 1.08
    y_min = min([p["y"] for p in points] + [0.6])
    y_min = max(0.0, (int(y_min * 20) / 20))

    def sx(v):
        return left + (w - left - right) * (v / x_max)

    def sy(v):
        return h - bottom - (h - bottom - top) * ((v - y_min) / (1 - y_min))

    parts = [f"<svg viewBox='0 0 {w} {h}' role='img' aria-label='{html.escape(title)}'>",
             f"<text x='{left}' y='16' class='ct'>{html.escape(title)}</text>"]
    for i in range(6):
        y = y_min + (1 - y_min) * i / 5
        parts.append(f"<line x1='{left}' x2='{w - right}' y1='{sy(y):.1f}' y2='{sy(y):.1f}' class='grid'/>"
                     f"<text x='{left - 6}' y='{sy(y) + 4:.1f}' class='tick' text-anchor='end'>{100 * y:.0f}%</text>")
    for i in range(5):
        x = x_max * i / 4
        parts.append(f"<text x='{sx(x):.1f}' y='{h - bottom + 16}' class='tick' text-anchor='middle'>{x:.0f}</text>")
    parts.append(f"<text x='{(w + left) / 2}' y='{h - 6}' class='tick' text-anchor='middle'>verdicts per second (higher is cheaper)</text>")
    for p in points:
        if not p["x"]:
            continue
        color = PALETTE[models.index(p["model"]) % len(PALETTE)]
        fill = color if p["guarded"] else "none"
        label = html.escape(f"{p['model']} · {p['prompt']} · {p['guard']}: {100 * p['y']:.1f}% accurate (held-out), "
                            f"{p['x']:.1f} verdicts/s, {p['failed']} dev checks failed")
        shape = (f"<circle cx='{sx(p['x']):.1f}' cy='{sy(p['y']):.1f}' r='5' fill='{fill}' stroke='{color}' stroke-width='2'>"
                 f"<title>{label}</title></circle>")
        if p["trusted"]:
            shape += f"<circle cx='{sx(p['x']):.1f}' cy='{sy(p['y']):.1f}' r='9' fill='none' class='ring'><title>{label}</title></circle>"
        parts.append(shape)
    parts.append("</svg>")
    return "".join(parts)


_CSS = """
:root{--bg:#ffffff;--fg:#1b1d21;--muted:#5f6368;--line:#e2e4e8;--card:#f6f7f9;--good:#137333;--bad:#b3261e;--goodbg:#e6f4ea;--badbg:#fce8e6;--accent:#4269d0}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--fg:#e8eaed;--muted:#9aa0a6;--line:#33363b;--card:#1d1f22;--good:#81c995;--bad:#f28b82;--goodbg:#1f3326;--badbg:#3a2220;--accent:#8ab4f8}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:36px 0 10px}
.muted{color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
.card{background:var(--card);border-radius:10px;padding:14px 16px;border:1px solid var(--line)}.card h3{margin:0 0 6px;font-size:1rem}
.big{font-size:1.05rem;font-weight:600}.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
svg{width:100%;height:auto;background:var(--card);border-radius:10px;border:1px solid var(--line)}
.ct{font-weight:600;font-size:13px;fill:var(--fg)}.tick{font-size:11px;fill:var(--muted)}.grid{stroke:var(--line)}.ring{stroke:var(--fg);stroke-width:1.2}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:.85rem;margin:8px 0}.legend span{display:inline-flex;align-items:center;gap:6px}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px}table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{position:sticky;top:0;background:var(--card);cursor:pointer;user-select:none}
td.num{font-variant-numeric:tabular-nums;text-align:right}td.g{background:var(--goodbg);color:var(--good)}td.b{background:var(--badbg);color:var(--bad)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:8px 0 12px}select,input{font:inherit;padding:5px 8px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
.case{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0;background:var(--card)}
.case pre{white-space:pre-wrap;margin:6px 0;font:13px/1.45 ui-monospace,Consolas,monospace}.tag{font-size:.78rem;padding:1px 7px;border-radius:99px;border:1px solid var(--line);margin-right:6px}
.tag.bad{color:var(--bad);border-color:var(--bad)}.tag.good{color:var(--good);border-color:var(--good)}
@media (max-width:600px){main{padding:16px 16px 48px}h1{font-size:1.3rem}}
"""

_JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const EXPECT = {correct:'c', incorrect:'i', A:'A', B:'B'};
const SAY = {c:'correct', i:'incorrect', A:'A', B:'B', '-':'withheld', '?':'no answer'};
function el(tag, attrs, text){const e=document.createElement(tag);Object.assign(e,attrs||{});if(text!==undefined)e.textContent=text;return e;}
// set-up table: click a header to sort
document.querySelectorAll('table.sortable').forEach(t=>{
  t.querySelectorAll('th').forEach((th,i)=>th.addEventListener('click',()=>{
    const rows=[...t.tBodies[0].rows]; const dir=th.dataset.dir==='asc'?-1:1; th.dataset.dir=dir===1?'asc':'desc';
    rows.sort((a,b)=>{const x=a.cells[i].dataset.v??a.cells[i].textContent, y=b.cells[i].dataset.v??b.cells[i].textContent;
      const nx=parseFloat(x), ny=parseFloat(y); return (isNaN(nx)||isNaN(ny)? x.localeCompare(y): nx-ny)*dir;});
    rows.forEach(r=>t.tBodies[0].appendChild(r));
  }));
});
const fRef=document.getElementById('fref'), fModel=document.getElementById('fmodel');
function filterTable(){document.querySelectorAll('#setups tbody tr').forEach(r=>{
  r.hidden=(fRef.value&&r.dataset.ref!==fRef.value)||(fModel.value&&r.dataset.model!==fModel.value);});}
fRef.addEventListener('change',filterTable); fModel.addEventListener('change',filterTable);
// case browser
const sRun=document.getElementById('srun'), sVar=document.getElementById('svar'), sOnly=document.getElementById('sonly'), out=document.getElementById('cases'), count=document.getElementById('ccount');
D.runs.forEach(r=>sRun.appendChild(el('option',{value:r.id},r.id)));
[...new Set(D.cases.map(c=>c.variant))].forEach(v=>sVar.appendChild(el('option',{value:v},v.replaceAll('_',' '))));
if(D.default_run) sRun.value=D.default_run;
function show(){
  const run=D.runs.find(r=>r.id===sRun.value); out.innerHTML=''; let shown=0, wrong=0, total=0;
  D.cases.forEach((c,i)=>{
    if(sVar.value&&c.variant!==sVar.value) return;
    const got=run.v[i], exp=EXPECT[c.expected]; const right=exp?got===exp:null; total++;
    if(right===false) wrong++;
    if(sOnly.checked&&right!==false) return;
    if(shown>=150) return; shown++;
    const box=el('div',{className:'case'});
    const head=el('div'); head.appendChild(el('span',{className:'tag'},c.variant.replaceAll('_',' ')));
    head.appendChild(el('span',{className:'tag '+(right===false?'bad':right?'good':'')},`judge: ${SAY[got]||got}`));
    head.appendChild(el('span',{className:'tag'},exp?`expected: ${SAY[exp]}`:'no ground truth'));
    if(run.f[i]==='1') head.appendChild(el('span',{className:'tag bad'},'flagged by screen'));
    head.appendChild(el('span',{className:'muted'},' '+c.id));
    box.appendChild(head); box.appendChild(el('div',{className:'big'},c.q)); box.appendChild(el('pre',{},c.a));
    out.appendChild(box);
  });
  count.textContent=`${wrong} of ${total} verdicts in this view disagree with ground truth`+(shown>=150?' (first 150 shown)':'');
}
[sRun,sVar,sOnly].forEach(x=>x.addEventListener('change',show)); show();
"""


def _pct_class(name: str, value: float | None, thresholds: dict) -> str:
    rule = thresholds.get(name)
    if value is None or not rule:
        return ""
    ok = value >= rule["min"] if "min" in rule else value <= rule["max"]
    return "g" if ok else "b"


def build_dashboard(runs_dir: str | Path, out_path: str | Path, include_mock: bool = False) -> int:
    runs_dir = Path(runs_dir)
    cands = candidates(runs_dir, include_mock)
    if not cands:
        raise ValueError(f"no audits with dev and held-out scores under {runs_dir}")
    chosen = choose(cands)
    models = sorted({c["model"] for c in cands})
    e = html.escape

    # thresholds from any run (they are the same config)
    first = json.loads((runs_dir / cands[0]["run"] / "summary.json").read_text(encoding="utf-8"))
    thresholds = {c["metric"]: {c["op"]: c["limit"]} for c in first["checks"]}

    # case texts once, verdicts per run as compact strings
    def rows_of(run: str) -> list[dict]:
        with open(runs_dir / run / "results.jsonl", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    base_rows = [r for r in rows_of(cands[0]["run"]) if int(r.get("repeat") or 0) == 0]
    order = [r["case_id"] for r in base_rows]
    cases = []
    for r in base_rows:
        text = r["answer"] or f"A: {r['answer_a']}\n\nB: {r['answer_b']}"
        cases.append({"id": r["case_id"], "variant": r["variant"], "q": r["question"],
                      "a": text if len(text) <= 600 else text[:597] + "...", "expected": r["expected"]})
    runs = []
    for c in sorted(cands, key=lambda c: c["run"]):
        v, f = _codes(rows_of(c["run"]), order)
        runs.append({"id": c["run"], "v": v, "f": f})
    default = (chosen.get("none") or chosen.get("given") or {}).get("best", {}).get("run")

    parts = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             f"<title>Judge audit dashboard</title><style>{_CSS}</style></head><body><main>",
             "<h1>Judge audit dashboard</h1>",
             f"<p class='muted'>{len(cands)} judge set-ups ({len(models)} models). Set-ups are chosen on the dev half of the "
             "suite; every number shown is from the held-out half, which played no part in choosing them.</p>",
             "<h2>Which set-up to use</h2><div class='cards'>"]
    for ref, title in USE_CASES:
        if ref not in chosen:
            continue
        pick = chosen[ref]["cheapest_trusted"]
        best = chosen[ref]["best"]
        parts.append(f"<div class='card'><h3>{e(title)}</h3>")
        if pick:
            acc = pick["heldout"].get("pointwise_accuracy") or {}
            parts.append(f"<p class='big'>{e(pick['model'])} · {e(pick['prompt'])} prompt · guard {e(pick['guard'])}</p>"
                         f"<p>{pick['verdicts_per_s']:.1f} verdicts/s, {pick['calls_per_verdict']:g} calls per verdict. "
                         f"Held-out accuracy {100 * (acc.get('value') or 0):.1f}%; "
                         + ("passed every held-out check." if pick["heldout_passed"] else "held-out failures: " + e(", ".join(pick["heldout_failed"])))
                         + "</p>")
        else:
            parts.append(f"<p class='big'>No set-up passed every check.</p><p>Closest: {e(best['model'])} · {e(best['prompt'])} · "
                         f"guard {e(best['guard'])}; failed {e(', '.join(best['dev_failed']))} on dev. Keep a human in the loop.</p>")
        parts.append("</div>")
    parts.append("</div>")

    parts.append("<h2>Trust against cost</h2><div class='legend'>")
    for i, m in enumerate(models):
        parts.append(f"<span><i class='dot' style='background:{PALETTE[i % len(PALETTE)]}'></i>{e(m)}</span>")
    parts.append("<span>hollow = plain judge, filled = guarded, ringed = passed every dev check</span></div><div class='charts'>")
    for ref, title in USE_CASES:
        pts = [{"x": c["verdicts_per_s"], "y": (c["heldout"].get("pointwise_accuracy") or {}).get("value") or 0,
                "model": c["model"], "prompt": c["prompt"], "guard": c["guard"], "guarded": c["guard"] != "none",
                "trusted": c["dev_passed"], "failed": len(c["dev_failed"])} for c in cands if c["reference"] == ref]
        if pts:
            parts.append(_scatter(pts, models, f"{title}: held-out accuracy"))
    parts.append("</div>")

    parts.append("<h2>Every set-up</h2><div class='controls'><label>Reference <select id='fref'><option value=''>all</option>"
                 "<option value='given'>given</option><option value='none'>none</option></select></label>"
                 "<label>Model <select id='fmodel'><option value=''>all</option>"
                 + "".join(f"<option>{e(m)}</option>" for m in models)
                 + "</select></label><span class='muted'>Held-out values; green passes its limit, red fails. Click a header to sort.</span></div>")
    header = ["Model", "Prompt", "Reference", "Guard", "Verdicts/s", "Dev failed"] + [label for _, label in KEY_METRICS]
    parts.append("<div class='wrap'><table id='setups' class='sortable'><thead><tr>" + "".join(f"<th>{e(h)}</th>" for h in header) + "</tr></thead><tbody>")
    for c in sorted(cands, key=lambda c: (c["reference"], c["model"], c["prompt"], c["guard"])):
        vps = c["verdicts_per_s"]
        cells = [f"<td>{e(c['model'])}</td>", f"<td>{e(c['prompt'])}</td>", f"<td>{e(c['reference'])}</td>", f"<td>{e(c['guard'])}</td>",
                 f"<td class='num' data-v='{vps or 0}'>{'' if vps is None else f'{vps:.1f}'}</td>",
                 f"<td class='num' data-v='{len(c['dev_failed'])}'>{len(c['dev_failed'])}</td>"]
        for name, _ in KEY_METRICS:
            m = c["heldout"].get(name)
            value = None if not m else m["value"]
            cells.append(f"<td class='num {_pct_class(name, value, thresholds)}' data-v='{'' if value is None else value}'>"
                         f"{'' if value is None else f'{100 * value:.1f}%'}</td>")
        parts.append(f"<tr data-ref='{e(c['reference'])}' data-model='{e(c['model'])}'>" + "".join(cells) + "</tr>")
    parts.append("</tbody></table></div>")

    parts.append("<h2>Where the judge was fooled</h2><div class='controls'>"
                 "<label>Set-up <select id='srun'></select></label>"
                 "<label>Variant <select id='svar'><option value=''>all</option></select></label>"
                 "<label><input type='checkbox' id='sonly' checked> only wrong verdicts</label></div>"
                 "<p id='ccount' class='muted'></p><div id='cases'></div>")
    payload = json.dumps({"cases": cases, "runs": runs, "default_run": default}, ensure_ascii=False).replace("</", "<\\/")
    parts.append(f"<script type='application/json' id='data'>{payload}</script><script>{_JS}</script></main></body></html>")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return len(cands)
