<#
.SYNOPSIS
Compiles and runs the 32-bit Parallel Arbiter PUF fleet simulation using Icarus Verilog.

.DESCRIPTION
Automates the full simulation workflow:
  1. Checks for Icarus Verilog (iverilog + vvp) in PATH.
  2. Compiles all design sources (including parallel_puf.v) and testbench.
  3. Runs the simulation, producing VCD waveform and CSV CRP data.
  4. Provides guidance for GTKWave / EPWave viewing.

.EXAMPLE
cd hardware-simulation
.\scripts\run_simulation.ps1
#>

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$SimRoot = (Resolve-Path "$ScriptDir\..").Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path

Write-Host ""
Write-Host "  ===============================================" -ForegroundColor Cyan
Write-Host "  |  32-bit Parallel Arbiter PUF Fleet Sim     |" -ForegroundColor Cyan
Write-Host "  |  5 Cars x 32 Lanes x 128 Stages           |" -ForegroundColor Cyan
Write-Host "  ===============================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 0: Prerequisite Check ─────────────────────────────────────────
$hasIverilog = Get-Command iverilog -ErrorAction SilentlyContinue
$hasVvp = Get-Command vvp     -ErrorAction SilentlyContinue

if (-not $hasIverilog -or -not $hasVvp) {
    Write-Host "[ERROR] Icarus Verilog (iverilog / vvp) is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Installation options for Windows:" -ForegroundColor Yellow
    Write-Host "    1. Direct download : https://bleyer.org/icarus/"       -ForegroundColor DarkGray
    Write-Host "    2. Chocolatey      : choco install iverilog"            -ForegroundColor DarkGray
    Write-Host "    3. Scoop           : scoop install iverilog"            -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  After installing, ensure iverilog and vvp are in your PATH." -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  ── Alternative: EDA Playground (no install needed) ──" -ForegroundColor Yellow
    Write-Host "    1. Go to https://www.edaplayground.com"               -ForegroundColor DarkGray
    Write-Host "    2. Select 'Icarus Verilog 12.0' as the simulator"     -ForegroundColor DarkGray
    Write-Host "    3. Paste all src/*.v files into the 'Design' panel"   -ForegroundColor DarkGray
    Write-Host "    4. Paste tb/puf_fleet_tb.v into the 'Testbench' panel" -ForegroundColor DarkGray
    Write-Host "    5. Check 'Open EPWave after run'"                      -ForegroundColor DarkGray
    Write-Host "    6. Click 'Run' to see waveforms"                       -ForegroundColor DarkGray
    Write-Host ""
    exit 1
}

Write-Host "  [OK] iverilog found: $($hasIverilog.Source)" -ForegroundColor Green
Write-Host "  [OK] vvp found:      $($hasVvp.Source)" -ForegroundColor Green
Write-Host ""

# ── Step 1: Ensure data/ directory exists for CSV export ───────────────
$dataDir = "$ProjectRoot\data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "  [OK] Created data/ directory at project root." -ForegroundColor Green
}

# ── Step 2: Compile Verilog Sources ────────────────────────────────────
Write-Host "[1/3] Compiling Verilog design + testbench..." -ForegroundColor Yellow
Write-Host "       Architecture: 128-bit challenge, 32-bit parallel response" -ForegroundColor DarkGray

$srcFiles = @(
    "$SimRoot\src\mux2to1_gate.v",
    "$SimRoot\src\d_flip_flop_arbiter.v",
    "$SimRoot\src\puf_switch_stage.v",
    "$SimRoot\src\arbiter_puf.v",
    "$SimRoot\src\parallel_puf.v",
    "$SimRoot\src\vehicle_fleet_puf.v"
)
$tbFile = "$SimRoot\tb\puf_fleet_tb.v"
$outFile = "$SimRoot\puf_sim.out"

$allFiles = $srcFiles + $tbFile

& iverilog -o $outFile $allFiles
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Verilog compilation failed. Check syntax errors above." -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Compiled to $outFile" -ForegroundColor Green

# ── Step 3: Run Simulation ─────────────────────────────────────────────
Write-Host ""
Write-Host "[2/3] Running PUF fleet simulation..." -ForegroundColor Yellow
Write-Host "   (5 cars x 32 lanes x 128 stages - this may take a moment)" -ForegroundColor DarkGray
Write-Host ""

# Must run vvp from hardware-simulation/ so relative paths in testbench resolve correctly
Push-Location $SimRoot
try {
    & vvp puf_sim.out
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Simulation execution failed." -ForegroundColor Red
        exit 1
    }
}
finally {
    Pop-Location
}

# ── Step 4: Report Output Files ────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Output files:" -ForegroundColor Yellow

$vcdPath = "$SimRoot\puf_fleet_waveform.vcd"
$csvPath = "$ProjectRoot\data\puf_crp_export.csv"

if (Test-Path $vcdPath) {
    $vcdSize = (Get-Item $vcdPath).Length / 1KB
    Write-Host "  [VCD] $vcdPath" -ForegroundColor Cyan
    Write-Host "        Size: $([math]::Round($vcdSize, 1)) KB" -ForegroundColor DarkGray
}
else {
    Write-Host "  [WARN] VCD file not found at: $vcdPath" -ForegroundColor DarkYellow
}

if (Test-Path $csvPath) {
    $csvLines = (Get-Content $csvPath).Count
    Write-Host "  [CSV] $csvPath" -ForegroundColor Cyan
    Write-Host "        Rows: $($csvLines - 1) CRPs (plus header)" -ForegroundColor DarkGray
}
else {
    Write-Host "  [WARN] CSV file not found at: $csvPath" -ForegroundColor DarkYellow
}

# ── Viewing Instructions ──────────────────────────────────────────────
Write-Host ""
Write-Host "  ── How to View Waveforms ──" -ForegroundColor Yellow
Write-Host ""
Write-Host "  GTKWave (local):" -ForegroundColor Cyan
Write-Host "    gtkwave `"$vcdPath`"" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  EPWave (online - no install):" -ForegroundColor Cyan
Write-Host "    Upload the VCD file to https://www.edaplayground.com" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Key signals to inspect:" -ForegroundColor DarkGray
Write-Host "    - car1_lane0_upper vs car1_lane0_lower  (Car 1 lane 0 race)" -ForegroundColor DarkGray
Write-Host "    - car2_lane0_upper vs car2_lane0_lower  (Car 2 lane 0 race)" -ForegroundColor DarkGray
Write-Host "    - car*_response[31:0]                    (32-bit CRP vectors)" -ForegroundColor DarkGray
Write-Host "    - Zoom into rising edges to see ps-level timing gaps" -ForegroundColor DarkGray
Write-Host ""