<#
.SYNOPSIS
Sequential startup script for the Capstone 2027 Edge-to-Cloud Federated Learning Pipeline.
#>

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Capstone 2027: Secure Edge-to-Cloud Federated Learning   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Tearing down any previous containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "`n[2/5] Building and launching Cloud/Backend infrastructure..." -ForegroundColor Yellow
Write-Host "This builds the Admin UI, Audit Logger, and the base Docker Image for our vehicles."
docker-compose up -d --build

Write-Host "`n[3/5] Waiting for backend services to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n[4/5] Activating local Python environment and running Edge Node Handshake Simulation..." -ForegroundColor Yellow
Write-Host "Pillar 1 Demo: Demonstrating Secure PUF Handshake for Vehicle ID: 77" -ForegroundColor Green

# Use virtual environment if available
$pythonPath = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonPath = ".\.venv\Scripts\python.exe"
    Write-Host "Using virtual environment Python..." -ForegroundColor DarkGray
} else {
    Write-Host "No .venv found, using system Python..." -ForegroundColor DarkGray
}

# Install requirements quietly
& $pythonPath -m pip install -r .\edge-vehicles\requirements.txt -q

# Run the PUF Handshake simulation with a flexible ID
$env:VEHICLE_ID = "77"
& $pythonPath .\edge-vehicles\main.py

Write-Host "`n[5/5] Running SNN Zero-Day Pipeline Simulation..." -ForegroundColor Yellow
Write-Host "Pillar 1 Demo (cont.): Demonstrating Local SNN/CNN retraining on zero-day attack." -ForegroundColor Green
& $pythonPath .\src\ml\orchestrator\zero_day_pipeline.py

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "System is now fully operational!" -ForegroundColor Green
Write-Host "Pillar 2 Demo: You can now access the VSOC Admin Dashboard."
Write-Host "-> Dashboard URL: http://localhost:5173" -ForegroundColor Cyan
Write-Host "-> API Server URL: http://localhost:3001" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nPress Ctrl+C at any time to exit and safely spin down the infrastructure." -ForegroundColor DarkGray

try {
    # Keep the script running to hold the terminal open
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nShutting down infrastructure..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "Done!" -ForegroundColor Green
}
