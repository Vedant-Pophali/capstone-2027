<#
.SYNOPSIS
Unified startup script for the Capstone 2027 VSOC system.

.DESCRIPTION
Handles Docker, Spring Boot, and Vite frontend in one command.

.PARAMETER Dev
Run in local development mode (no Docker for backend/frontend).

.PARAMETER TestOnly
Run CRUD smoke tests against a running backend.

.PARAMETER Docker
Run everything via docker-compose (default).

.EXAMPLE
.\start.ps1              # Docker mode (builds and runs everything)
.\start.ps1 -Dev         # Local dev mode (Spring Boot + Vite dev servers)
.\start.ps1 -TestOnly    # Run CRUD tests against a running backend
#>

param(
    [switch]$Dev,
    [switch]$TestOnly,
    [switch]$MLSimulation
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Write-Banner {
    Write-Host ""
    Write-Host "  =================================================" -ForegroundColor DarkCyan
    Write-Host "  |   Capstone 2027: VSOC Fleet Manager           |" -ForegroundColor DarkCyan
    Write-Host "  |   Secure Edge-to-Cloud Vehicle Management     |" -ForegroundColor DarkCyan
    Write-Host "  =================================================" -ForegroundColor DarkCyan
    Write-Host ""
}

function Test-Prerequisites {
    param([bool]$NeedDocker = $true, [bool]$NeedMaven = $false, [bool]$NeedNode = $false)

    if ($NeedDocker) {
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            Write-Host "[ERROR] Docker is not installed or not in PATH." -ForegroundColor Red
            exit 1
        }
        $dockerRunning = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
            exit 1
        }
        Write-Host "  [OK] Docker" -ForegroundColor Green
    }

    if ($NeedMaven) {
        if (-not (Get-Command mvn -ErrorAction SilentlyContinue)) {
            # Try mvnw wrapper
            if (Test-Path "$ProjectRoot\fleet-manager\mvnw.cmd") {
                Write-Host "  [OK] Maven (via wrapper)" -ForegroundColor Green
            } else {
                Write-Host "[ERROR] Maven (mvn) is not installed. Install it or use Docker mode." -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "  [OK] Maven" -ForegroundColor Green
        }
    }

    if ($NeedNode) {
        if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
            Write-Host "[ERROR] Node.js is not installed." -ForegroundColor Red
            exit 1
        }
        Write-Host "  [OK] Node.js $(node --version)" -ForegroundColor Green
    }
}

# ── CRUD Test Mode ──────────────────────────────────────────
function Run-CrudTests {
    Write-Host "`n[TEST] Running CRUD smoke tests against http://localhost:8081" -ForegroundColor Yellow

    $baseUrl = "http://localhost:8081/api"

    # Test 1: POST
    Write-Host "`n  [1/4] Creating vehicle (ID: test-999)..." -ForegroundColor Yellow
    try {
        $body = '{"id":"test-999","owner":"Smoke Test","model":"Test Vehicle"}'
        $vehicle = Invoke-RestMethod -Uri "$baseUrl/vehicles" -Method POST -Body $body -ContentType "application/json"
        Write-Host "  [PASS] Vehicle created" -ForegroundColor Green
        Write-Output ($vehicle | ConvertTo-Json -Depth 3)
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }

    Start-Sleep -Seconds 2

    # Test 2: GET all
    Write-Host "`n  [2/4] Fetching fleet..." -ForegroundColor Yellow
    try {
        $fleet = Invoke-RestMethod -Uri "$baseUrl/vehicles" -Method GET
        Write-Host "  [PASS] Retrieved $($fleet.Count) vehicle(s)" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }

    # Test 3: GET single
    Write-Host "`n  [3/4] Fetching vehicle test-999..." -ForegroundColor Yellow
    try {
        $single = Invoke-RestMethod -Uri "$baseUrl/vehicles/test-999" -Method GET
        Write-Host "  [PASS] Vehicle found: $($single.id)" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }

    Start-Sleep -Seconds 2

    # Test 4: DELETE
    Write-Host "`n  [4/4] Deleting vehicle test-999..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod -Uri "$baseUrl/vehicles/test-999" -Method DELETE
        Write-Host "  [PASS] Vehicle deleted and container destroyed" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "`n[TEST] Smoke tests completed." -ForegroundColor Cyan
}

# ── ML Simulation Mode ──────────────────────────────────────
function Run-MLSimulation {
    Write-Host "`n[ML SIMULATION] Activating local Python environment and running Edge Node Handshake Simulation..." -ForegroundColor Yellow
    Write-Host "Pillar 1 Demo: Demonstrating Secure PUF Handshake for Vehicle ID: 77" -ForegroundColor Green

    $pythonPath = "python"
    if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
        $pythonPath = "$ProjectRoot\.venv\Scripts\python.exe"
        Write-Host "Using virtual environment Python..." -ForegroundColor DarkGray
    } else {
        Write-Host "No .venv found, using system Python..." -ForegroundColor DarkGray
    }

    & $pythonPath -m pip install -r "$ProjectRoot\edge-vehicles\requirements.txt" -q

    $env:VEHICLE_ID = "77"
    & $pythonPath "$ProjectRoot\edge-vehicles\main.py"

    Write-Host "`n[ML SIMULATION] Running SNN Zero-Day Pipeline Simulation..." -ForegroundColor Yellow
    Write-Host "Pillar 1 Demo (cont.): Demonstrating Local SNN/CNN retraining on zero-day attack." -ForegroundColor Green
    & $pythonPath "$ProjectRoot\src\ml\orchestrator\zero_day_pipeline.py"
    
    Write-Host "`n[ML SIMULATION] Completed." -ForegroundColor Cyan
}

# ── Docker Mode ─────────────────────────────────────────────
function Start-DockerMode {
    Write-Host "[1/4] Pre-flight checks..." -ForegroundColor Yellow
    Test-Prerequisites -NeedDocker $true

    Write-Host "`n[2/4] Tearing down previous containers..." -ForegroundColor Yellow
    docker-compose -f "$ProjectRoot\docker-compose.yml" down 2>$null

    Write-Host "`n[3/4] Building and launching all services..." -ForegroundColor Yellow
    Write-Host "  This builds: fleet-manager (Spring Boot), dashboard-client (Vite/React), edge-vehicle-base" -ForegroundColor DarkGray
    docker-compose -f "$ProjectRoot\docker-compose.yml" up -d --build

    Write-Host "`n[4/4] Waiting for services to initialize (15 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    Write-Host ""
    Write-Host "  System is running!" -ForegroundColor Green
    Write-Host "  Dashboard:  http://localhost:5173" -ForegroundColor Cyan
    Write-Host "  API:        http://localhost:8081/api/vehicles" -ForegroundColor Cyan
    Write-Host "  WebSocket:  http://localhost:8081/ws" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Press Ctrl+C to shut down." -ForegroundColor DarkGray

    try {
        while ($true) { Start-Sleep -Seconds 1 }
    } finally {
        Write-Host "`n  Shutting down..." -ForegroundColor Yellow
        docker-compose -f "$ProjectRoot\docker-compose.yml" down
        Write-Host "  Done!" -ForegroundColor Green
    }
}

# ── Dev Mode ────────────────────────────────────────────────
function Start-DevMode {
    Write-Host "[1/4] Pre-flight checks..." -ForegroundColor Yellow
    Test-Prerequisites -NeedDocker $true -NeedMaven $true -NeedNode $true

    Write-Host "`n[2/4] Building edge-vehicle Docker image..." -ForegroundColor Yellow
    docker build -t capstone-2027-edge-vehicle-base "$ProjectRoot\edge-vehicles"

    Write-Host "`n[3/4] Starting Spring Boot backend..." -ForegroundColor Yellow
    # Create local data directory
    New-Item -ItemType Directory -Force -Path "$ProjectRoot\data\fleet-manager" | Out-Null

    $backendJob = Start-Job -ScriptBlock {
        param($root)
        Set-Location "$root\fleet-manager"
        $env:SPRING_DATASOURCE_URL = "jdbc:sqlite:$root/data/fleet-manager/fleet.db"
        mvn spring-boot:run -q
    } -ArgumentList $ProjectRoot

    Write-Host "  Backend starting (port 8081)..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 10

    Write-Host "`n[4/4] Starting Vite frontend dev server..." -ForegroundColor Yellow
    $frontendJob = Start-Job -ScriptBlock {
        param($root)
        Set-Location "$root\vsoc-dashboard\client"
        npm install --silent 2>$null
        npx vite --host
    } -ArgumentList $ProjectRoot

    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "  Dev servers running!" -ForegroundColor Green
    Write-Host "  Dashboard:  http://localhost:5173" -ForegroundColor Cyan
    Write-Host "  API:        http://localhost:8081/api/vehicles" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop all servers." -ForegroundColor DarkGray

    try {
        while ($true) {
            # Stream backend logs
            Receive-Job $backendJob -ErrorAction SilentlyContinue
            Receive-Job $frontendJob -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
    } finally {
        Write-Host "`n  Stopping dev servers..." -ForegroundColor Yellow
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
        Write-Host "  Done!" -ForegroundColor Green
    }
}

# ── Main ────────────────────────────────────────────────────
Write-Banner

if ($TestOnly) {
    Run-CrudTests
} elseif ($MLSimulation) {
    Run-MLSimulation
} elseif ($Dev) {
    Start-DevMode
} else {
    Start-DockerMode
}
