<#
Runs the whole experiment set unattended, one model after another:
  1. downloads the model if it is missing (an interrupted download resumes)
  2. starts llama-server, waits until it is ready, records GPU memory in use
  3. runs the audit for every prompt style and reference setting
  4. on the benchmark model only: decoding, prefix-cache and batching experiments
  5. stops the server and refreshes results\comparison.md

If llama-server dies in the middle of an audit, the script records the evidence in
logs\crashes.log, restarts the server and resumes: finished judge calls come from
the cache. Safe to stop with Ctrl+C and run again.

  powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
  powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -Only llama31-8b-q4
#>
param(
    [string]$LlamaServer = "D:\llama.cpp\llama-server.exe",
    [int]$Port = 8080,
    [string[]]$Only = @(),
    [switch]$SkipBench
)

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$ModelsDir = Join-Path $Root "models"
$LogDir = Join-Path $Root "logs"
$CrashLog = Join-Path $LogDir "crashes.log"
$Config = "configs\local_llamacpp.yaml"
$env:PYTHONUNBUFFERED = "1"
$Only = @($Only | ForEach-Object { $_ -split "," } | Where-Object { $_ })
$script:Crashes = 0

if (-not (Test-Path $Py)) { Write-Host "[run_all] .venv not found. Run: python -m venv .venv; .venv\Scripts\pip install -e .[dev]"; exit 1 }
if (-not (Test-Path $LlamaServer)) { Write-Host "[run_all] llama-server not found at $LlamaServer (pass -LlamaServer <path>)"; exit 1 }
New-Item -ItemType Directory -Force $ModelsDir, $LogDir, (Join-Path $Root "results") | Out-Null

$HF = "https://huggingface.co"
$Models = @(
    @{ Name = "llama31-8b-q4"; Label = "llama31-8b-instruct-q4_k_m"; Repo = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"; File = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"; Bench = $true; Sets = @() },
    @{ Name = "llama32-3b-q4"; Label = "llama32-3b-instruct-q4_k_m"; Repo = "bartowski/Llama-3.2-3B-Instruct-GGUF"; File = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"; Bench = $false; Sets = @() },
    @{ Name = "llama31-8b-q8"; Label = "llama31-8b-instruct-q8_0"; Repo = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"; File = "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"; Bench = $false; Sets = @() },
    @{ Name = "qwen3-8b-q4"; Label = "qwen3-8b-q4_k_m"; Repo = "Qwen/Qwen3-8B-GGUF"; File = "Qwen3-8B-Q4_K_M.gguf"; Bench = $false; Sets = @("judge.extra_body.chat_template_kwargs.enable_thinking=false") },
    @{ Name = "qwen3-8b-q8"; Label = "qwen3-8b-q8_0"; Repo = "Qwen/Qwen3-8B-GGUF"; File = "Qwen3-8B-Q8_0.gguf"; Bench = $false; Sets = @("judge.extra_body.chat_template_kwargs.enable_thinking=false") }
)

function Say([string]$text) {
    Write-Host ("[run_all {0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $text)
}

function Stop-Server {
    $running = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
    if ($running) {
        $running | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
}

function Test-Server {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 3
        return ($health.status -eq "ok")
    } catch {
        return $false
    }
}

function Get-Vram {
    try {
        $line = & nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | Select-Object -First 1
        return [int]("$line".Trim())
    } catch {
        return 0
    }
}

function Get-GpuLine {
    try {
        $line = & nvidia-smi --query-gpu=temperature.gpu,power.draw,memory.used,utilization.gpu --format=csv,noheader | Select-Object -First 1
        return ("$line".Trim() -replace ", ", " / ")
    } catch {
        return "n/a"
    }
}

function Save-Evidence([string]$what, [int]$minutes) {
    # Writes what happened, the GPU state and any graphics-driver or hardware events
    # Windows logged in the last few minutes. Returns the number of such events.
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $CrashLog -Value "$stamp  $what  | GPU temp/power/memory/util: $(Get-GpuLine)"
    $count = 0
    try {
        $events = Get-WinEvent -FilterHashtable @{ LogName = "System"; StartTime = (Get-Date).AddMinutes(-$minutes) } -ErrorAction Stop |
            Where-Object { $_.ProviderName -match "nvlddmkm|Display|WHEA|Kernel-Power|Kernel-Processor-Power" }
        foreach ($e in $events) {
            $first = ("" + $e.Message -split "`n")[0].Trim()
            Add-Content -Path $CrashLog -Value ("    windows event {0}  {1}  id {2}  {3}" -f $e.TimeCreated.ToString("HH:mm:ss"), $e.ProviderName, $e.Id, $first)
            $count++
        }
    } catch { }
    return $count
}

function Get-Model($m) {
    $path = Join-Path $ModelsDir $m.File
    if (Test-Path $path) { return $path }
    $part = "$path.part"
    $url = "$HF/$($m.Repo)/resolve/main/$($m.File)"
    Say "downloading $($m.File)"
    for ($try = 1; $try -le 30; $try++) {
        & curl.exe -L -f -C - -o $part $url | Out-Host
        $code = $LASTEXITCODE
        if ($code -eq 0) {
            Rename-Item -Path $part -NewName $m.File
            return $path
        }
        if ($code -eq 22) {
            Say "download refused by the server (wrong file name or no access): $url"
            return $null
        }
        Say "download interrupted (curl exit $code), resuming, attempt $try of 30"
        Start-Sleep -Seconds 5
    }
    return $null
}

function Start-Server([string]$path, [int]$parallel, [string]$tag) {
    Stop-Server
    $ctx = 1024 * $parallel
    $log = Join-Path $LogDir ("server-{0}-{1}.log" -f $tag, (Get-Date -Format "HHmmss"))
    $argList = @("-m", "`"$path`"", "-ngl", "99", "-c", "$ctx", "--parallel", "$parallel", "--port", "$Port")
    $proc = Start-Process -FilePath $LlamaServer -ArgumentList $argList -PassThru -NoNewWindow -RedirectStandardOutput "$log.stdout" -RedirectStandardError $log
    for ($i = 0; $i -lt 150; $i++) {
        Start-Sleep -Seconds 2
        if ($proc.HasExited) { break }
        if (Test-Server) { return $true }
    }
    Say "llama-server did not become ready. Last lines of $log :"
    if (Test-Path $log) { Get-Content $log -Tail 15 | Out-Host }
    Stop-Server
    return $false
}

function Invoke-Audit([string]$runName, [string[]]$sets, [string[]]$more, [string]$path, [int]$parallel, [string]$tag) {
    $cmd = @("-m", "judgeaudit", "run", "-c", $Config, "--run-name", $runName)
    foreach ($s in $sets) { if ($s) { $cmd += @("--set", $s) } }
    if ($more) { $cmd += $more }
    for ($attempt = 1; $attempt -le 4; $attempt++) {
        if (-not (Test-Server)) {
            if (-not (Start-Server $path $parallel $tag)) { Say "cannot start the server, skipping $runName"; return }
        }
        Say "audit $runName  | GPU temp/power/memory/util: $(Get-GpuLine)"
        & $Py @cmd | Out-Host
        if ($LASTEXITCODE -ne 3) { return }
        # Exit code 3: the judge server stopped answering in the middle of the run.
        $script:Crashes++
        $n = Save-Evidence "llama-server died during $runName (attempt $attempt)" 3
        Say "llama-server died during $runName ($n related Windows events logged). Restarting and resuming, attempt $attempt of 4."
        Stop-Server
        Start-Sleep -Seconds 15
    }
    Say "giving up on $runName after 4 attempts"
}

function Update-Results {
    & $Py -m judgeaudit compare runs --out results | Out-Host
    $cards = Join-Path $Root "results\cards"
    New-Item -ItemType Directory -Force $cards | Out-Null
    Get-ChildItem (Join-Path $Root "runs") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $src = Join-Path $_.FullName "report.md"
        if ((Test-Path $src) -and ($_.Name -ne "smoke") -and ($_.Name -ne "_archive")) {
            Copy-Item $src (Join-Path $cards "$($_.Name).md") -Force
        }
    }
}

# The first hand-made run is the same experiment as llama31-8b-q4--hardened-none; keep it out of the tables.
$old = Join-Path $Root "runs\llama31-8b-q4"
if (Test-Path $old) {
    $archive = Join-Path $Root "runs\_archive"
    New-Item -ItemType Directory -Force $archive | Out-Null
    if (-not (Test-Path (Join-Path $archive "llama31-8b-q4"))) { Move-Item $old $archive }
}

$drive = (Split-Path -Qualifier $Root).TrimEnd(":")
$freeGb = [math]::Round((Get-PSDrive -Name $drive).Free / 1GB, 1)
Say "free space on ${drive}: $freeGb GB (the four extra models need about 25 GB)"
$history = Save-Evidence "run_all started (looking back 4 hours for graphics-driver events)" 240
Say "Windows logged $history graphics-driver or hardware events in the last 4 hours (details in logs\crashes.log)"
if (Get-Process -Name "llama-server" -ErrorAction SilentlyContinue) { Say "stopping the llama-server that is already running" }
Stop-Server
$started = Get-Date

try {
    foreach ($m in $Models) {
        if ($Only.Count -gt 0 -and ($Only -notcontains $m.Name)) { continue }
        Say "===== $($m.Name) ====="
        $path = Get-Model $m
        if (-not $path) { Say "skipping $($m.Name): model file not available"; continue }
        $sizeGb = [math]::Round((Get-Item $path).Length / 1e9, 2)

        if (-not (Start-Server $path 4 $m.Name)) { Say "skipping $($m.Name): server failed to start"; continue }
        $vram = Get-Vram
        Say "server ready, GPU memory in use: $vram MiB"
        $base = @("judge.label=$($m.Label)", "concurrency=4", "meta.model=$($m.Name)", "meta.model_gb=$sizeGb", "meta.vram_mib=$vram", "meta.parallel=4") + @($m.Sets)

        foreach ($style in @("hardened", "naive")) {
            foreach ($ref in @("none", "given")) {
                Invoke-Audit "$($m.Name)--$style-$ref" ($base + @("prompt_style=$style", "reference=$ref")) @() $path 4 $m.Name
            }
        }

        if ($m.Bench -and -not $SkipBench) {
            # Decoding strategy: the same audit three times, greedy and sampled.
            Invoke-Audit "$($m.Name)--greedy-x3" ($base + @("repeats=3")) @() $path 4 $m.Name
            Invoke-Audit "$($m.Name)--temp07-x3" ($base + @("repeats=3", "judge.temperature=0.7")) @() $path 4 $m.Name

            # Prefix (KV) caching on and off. --no-cache makes every call really run.
            Invoke-Audit "bench-prefix-cache-on" ($base + @("judge.extra_body.cache_prompt=true")) @("--no-cache") $path 4 $m.Name
            Invoke-Audit "bench-prefix-cache-off" ($base + @("judge.extra_body.cache_prompt=false")) @("--no-cache") $path 4 $m.Name

            # Batching: server slots and client concurrency swept together.
            foreach ($p in @(1, 2, 4, 8)) {
                $tag = "$($m.Name)-p$p"
                if (-not (Start-Server $path $p $tag)) { continue }
                $v = Get-Vram
                Invoke-Audit "bench-parallel-$p" ($base + @("concurrency=$p", "meta.parallel=$p", "meta.vram_mib=$v")) @("--no-cache") $path $p $tag
            }
        }

        Stop-Server
        Update-Results
    }
} finally {
    Stop-Server
}

Update-Results
$minutes = [math]::Round(((Get-Date) - $started).TotalMinutes, 1)
Say "finished in $minutes minutes; llama-server died and was restarted $($script:Crashes) times"
Say "open results\comparison.md, then commit: git add -A; git commit -m `"Experiment results`"; git push"
