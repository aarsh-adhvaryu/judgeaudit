import importlib.util
import json
import sys
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / "scripts" / "run_grid.py"
_spec = importlib.util.spec_from_file_location("run_grid", _path)
run_grid = importlib.util.module_from_spec(_spec)
sys.modules["run_grid"] = run_grid
_spec.loader.exec_module(run_grid)


def test_grid_sizes_match_the_published_experiment():
    full, quick = run_grid.grid(False), run_grid.grid(True)
    assert len(full) == 44 and len(set(full)) == 44
    assert len(quick) == 8 and set(quick) <= set(full)
    # plain judges come first, so every guard re-uses their calls
    first_guarded = next(i for i, (_, _, g) in enumerate(full) if g != "plain")
    assert all(g == "plain" for _, _, g in full[:first_guarded])


def test_mock_grid_runs_end_to_end_and_writes_the_dashboard(tmp_path):
    code = run_grid.main(["--mock", "--quick", "--limit-items", "6",
                          "--runs", str(tmp_path / "runs"), "--results", str(tmp_path / "results"),
                          "--cache", str(tmp_path / "cache.sqlite")])
    assert code == 0
    rec = json.loads((tmp_path / "results" / "recommendation.json").read_text(encoding="utf-8"))
    assert len(rec["candidates"]) == 2 * 8
    page = (tmp_path / "results" / "dashboard.html").read_text(encoding="utf-8")
    assert "mock-biased" in page and "mock-careful" in page
