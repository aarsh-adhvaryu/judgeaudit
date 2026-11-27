"""Run the judgeaudit experiment grid on Linux, Colab or Windows (Python only).

The same experiments as scripts/run_all.ps1, without the Windows-specific parts
(laptop power telemetry, Windows event log). For each model it downloads the
GGUF file if missing, starts llama-server, runs every set-up of the grid, stops
the server, and finally writes results/ (comparison, recommendation, dashboard).

  # the full grid, every model (hours on a laptop or a T4)
  python scripts/run_grid.py --server /path/to/llama-server

  # one model, eight set-ups: the 20-minute version, good for Colab
  python scripts/run_grid.py --server /path/to/llama-server --models llama31-8b-q4 --quick

  # no GPU at all: two mock judges with planted biases, results in results-mock/
  python scripts/run_grid.py --mock

Safe to stop and run again: finished judge calls come from the verdict cache and
partial downloads resume.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from judgeaudit.compare import write_comparison  # noqa: E402
from judgeaudit.config import load_config  # noqa: E402
from judgeaudit.dashboard import build_dashboard  # noqa: E402
from judgeaudit.recommend import write_recommendation  # noqa: E402
from judgeaudit.runner import run_audit  # noqa: E402

HF = "https://huggingface.co"
QWEN_NO_THINKING = "judge.extra_body.chat_template_kwargs.enable_thinking=false"
MODELS = {
    "llama31-8b-q4": ("llama31-8b-instruct-q4_k_m", "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf", []),
    "llama32-3b-q4": ("llama32-3b-instruct-q4_k_m", "bartowski/Llama-3.2-3B-Instruct-GGUF", "Llama-3.2-3B-Instruct-Q4_K_M.gguf", []),
    "llama31-8b-q8": ("llama31-8b-instruct-q8_0", "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF", "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf", []),
    "qwen3-8b-q4": ("qwen3-8b-q4_k_m", "Qwen/Qwen3-8B-GGUF", "Qwen3-8B-Q4_K_M.gguf", [QWEN_NO_THINKING]),
    "qwen3-8b-q8": ("qwen3-8b-q8_0", "Qwen/Qwen3-8B-GGUF", "Qwen3-8B-Q8_0.gguf", [QWEN_NO_THINKING]),
}
GUARDS = {
    "plain": [],
    "swap-regex": ["guard.swap=true", "guard.screen=regex"],
    "swap-llm": ["guard.swap=true", "guard.screen=llm"],
    "swap-both": ["guard.swap=true", "guard.screen=both"],
    "swap-both-abstain": ["guard.swap=true", "guard.screen=both", "guard.on_flag=abstain"],
    "swap-llm2": ["guard.swap=true", "guard.screen=llm", "guard.screen_prompt=v2"],
    "swap-both2": ["guard.swap=true", "guard.screen=both", "guard.screen_prompt=v2"],
}


def grid(quick: bool) -> list[tuple[str, str, str]]:
    """(prompt style, reference, guard) for every set-up, plain judges first so guards re-use their calls."""
    refs = ("none", "given")
    if quick:
        return [(s, r, g) for s, g in (("hardened", "plain"), ("guarded_v2", "plain"),
                                       ("hardened", "swap-regex"), ("hardened", "swap-both2")) for r in refs]
    plain = [(s, r, "plain") for s in ("hardened", "naive", "guarded", "guarded_v2") for r in refs]
    guarded = [(s, r, g) for s in ("hardened", "guarded", "guarded_v2") for r in refs for g in GUARDS if g != "plain"]
    return plain + guarded


def say(text: str) -> None:
    print(f"[run_grid {time.strftime('%H:%M:%S')}] {text}", flush=True)


# --- models and server --------------------------------------------------------


def download(repo: str, filename: str, models_dir: Path) -> Path:
    path = models_dir / filename
    if path.exists():
        return path
    models_dir.mkdir(parents=True, exist_ok=True)
    part = path.with_name(filename + ".part")
    url = f"{HF}/{repo}/resolve/main/{filename}"
    for attempt in range(1, 31):
        have = part.stat().st_size if part.exists() else 0
        request = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(request, timeout=60) as response, open(part, "ab" if have else "wb") as out:
                total = have + int(response.headers.get("Content-Length", 0))
                say(f"downloading {filename}: {have / 1e9:.2f} of {total / 1e9:.2f} GB")
                last = time.time()
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    if time.time() - last > 30:
                        last = time.time()
                        say(f"  {part.stat().st_size / 1e9:.2f} GB")
            os.replace(part, path)
            return path
        except urllib.error.HTTPError as exc:
            if exc.code == 416 and part.exists():  # already complete
                os.replace(part, path)
                return path
            if exc.code in (401, 403, 404):
                raise SystemExit(f"download refused ({exc.code}): {url}")
            say(f"download interrupted ({exc}), resuming, attempt {attempt} of 30")
        except OSError as exc:
            say(f"download interrupted ({exc}), resuming, attempt {attempt} of 30")
        time.sleep(5)
    raise SystemExit(f"could not download {url}")


def healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as response:
            return json.loads(response.read()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def gpu_memory_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return int(out.split()[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


class Server:
    def __init__(self, binary: str, model: Path, port: int, parallel: int, ctx_per_slot: int, log_dir: Path):
        self.binary, self.model, self.port = binary, model, port
        self.parallel, self.ctx_per_slot, self.log_dir = parallel, ctx_per_slot, log_dir
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        self.stop()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log = open(self.log_dir / f"server-{self.model.stem}-p{self.parallel}-{time.strftime('%H%M%S')}.log", "w")
        cmd = [self.binary, "-m", str(self.model), "-ngl", "99", "-c", str(self.ctx_per_slot * self.parallel),
               "--parallel", str(self.parallel), "--port", str(self.port)]
        self.proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(300):
            time.sleep(1)
            if self.proc.poll() is not None:
                raise SystemExit(f"llama-server exited at start (code {self.proc.returncode}); see {log.name} in {self.log_dir}")
            if healthy(self.port):
                text = (self.log_dir / log.name).read_text(errors="replace")
                if "failed to initialize CUDA" in text or "no usable GPU" in text:
                    self.stop()
                    raise SystemExit("llama-server could not use the GPU; build it with -DGGML_CUDA=ON")
                return
        raise SystemExit("llama-server did not become ready within 5 minutes")

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None


# --- audits -------------------------------------------------------------------


def audit(sets: list[str], run_name: str, args, server: Server | None, use_cache: bool = True, mock_judge: dict | None = None) -> dict:
    base = [f"out_dir={args.runs}", f"cache={args.cache}"]
    if not mock_judge:
        base.append(f"judge.base_url=http://127.0.0.1:{args.port}/v1")
    cfg = load_config(ROOT / "configs" / "local_llamacpp.yaml", base + sets)
    if mock_judge:
        cfg["judge"] = dict(mock_judge)  # same suite, thresholds and guards; only the judge differs
    cfg["run_name"] = run_name
    if not Path(cfg["suite"]).is_absolute():
        cfg["suite"] = str(ROOT / cfg["suite"])
    for attempt in range(1, 4):
        say(f"audit {run_name}")
        summary = run_audit(cfg, limit_items=args.limit_items, use_cache=use_cache)
        if not summary["run"].get("aborted") or server is None:
            return summary
        say(f"llama-server stopped answering during {run_name}; restarting and resuming (attempt {attempt} of 3)")
        server.start()
    return summary


def run_model(name: str, args) -> None:
    label, repo, filename, extra = MODELS[name]
    path = download(repo, filename, Path(args.models_dir))
    server = Server(args.server, path, args.port, args.parallel, args.ctx_per_slot, Path(args.logs))
    say(f"===== {name}: starting llama-server")
    server.start()
    try:
        meta = [f"meta.model={name}", f"meta.model_gb={path.stat().st_size / 1e9:.2f}",
                f"meta.vram_mib={gpu_memory_mib() or 0}", f"meta.parallel={args.parallel}",
                f"judge.label={label}", f"concurrency={args.parallel}"] + extra
        for style, ref, guard in grid(args.quick):
            audit(meta + [f"prompt_style={style}", f"reference={ref}"] + GUARDS[guard],
                  f"{name}--{style}-{ref}--{guard}", args, server)
        if args.bench:
            for on in (True, False):
                audit(meta + [f"judge.extra_body.cache_prompt={str(on).lower()}"],
                      f"bench-prefix-cache-{'on' if on else 'off'}", args, server, use_cache=False)
            for p in (1, 2, 4, 8):
                server.parallel = p
                server.start()
                audit(meta + [f"concurrency={p}", f"meta.parallel={p}", f"meta.vram_mib={gpu_memory_mib() or 0}"],
                      f"bench-parallel-{p}", args, server, use_cache=False)
    finally:
        server.stop()


MOCK_JUDGES = {
    # a judge with the failure modes found on real models, and a careful one
    "mock-biased": {"kind": "mock", "knowledge": 0.95, "noise": 0.02, "verbosity_bias": -0.45,
                    "injection_susceptibility": 1.0, "position_bias": 0.15, "screen_recall": 0.6},
    "mock-careful": {"kind": "mock", "knowledge": 0.98, "noise": 0.01, "verbosity_bias": -0.05,
                     "injection_susceptibility": 0.3, "position_bias": 0.05, "screen_recall": 0.9},
}


def run_mock(args) -> None:
    for name, judge in MOCK_JUDGES.items():
        for style, ref, guard in grid(args.quick):
            audit([f"meta.model={name}", f"prompt_style={style}", f"reference={ref}"] + GUARDS[guard],
                  f"{name}--{style}-{ref}--{guard}", args, None, mock_judge=judge)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--server", help="path to llama-server (default: llama-server on PATH)")
    parser.add_argument("--models", default=",".join(MODELS), help=f"comma-separated, from: {', '.join(MODELS)}")
    parser.add_argument("--quick", action="store_true", help="eight set-ups per model instead of 44")
    parser.add_argument("--bench", action="store_true", help="also run the prefix-cache and batching measurements")
    parser.add_argument("--limit-items", type=int, help="only the first N questions (they alternate dev and held-out)")
    parser.add_argument("--mock", action="store_true", help="no GPU: run the grid against two mock judges")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--parallel", type=int, default=4, help="llama-server slots and client concurrency")
    parser.add_argument("--ctx-per-slot", type=int, default=1024)
    parser.add_argument("--models-dir", default=str(ROOT / "models"))
    parser.add_argument("--runs", help="where run folders go (default runs/, or runs-mock/ with --mock)")
    parser.add_argument("--results", help="where tables and the dashboard go (default results/, or results-mock/)")
    parser.add_argument("--cache", help="verdict cache file (default .cache/verdicts.sqlite)")
    parser.add_argument("--logs", default=str(ROOT / "logs"))
    args = parser.parse_args(argv)
    suffix = "-mock" if args.mock else ""
    args.runs = args.runs or str(ROOT / f"runs{suffix}")
    args.results = args.results or str(ROOT / f"results{suffix}")
    args.cache = args.cache or str(ROOT / ".cache" / f"verdicts{suffix}.sqlite")

    started = time.time()
    if args.mock:
        run_mock(args)
    else:
        args.server = args.server or shutil.which("llama-server")
        if not args.server or not Path(args.server).exists():
            parser.error("llama-server not found: pass --server /path/to/llama-server (see README)")
        for name in [m.strip() for m in args.models.split(",") if m.strip()]:
            if name not in MODELS:
                parser.error(f"unknown model {name!r}; choose from {', '.join(MODELS)}")
            run_model(name, args)

    write_comparison(args.runs, args.results, include_mock=args.mock)
    write_recommendation(args.runs, args.results, include_mock=args.mock)
    build_dashboard(args.runs, Path(args.results) / "dashboard.html", include_mock=args.mock)
    say(f"finished in {(time.time() - started) / 60:.1f} minutes")
    say(f"open {Path(args.results) / 'dashboard.html'} and read {Path(args.results) / 'recommendation.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
