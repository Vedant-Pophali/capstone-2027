$ErrorActionPreference = "Continue"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "    Iterative CRUD Testing - Fleet Manager   " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Test 1: POST (Add Vehicle)
Write-Host "`n[1/3] Adding new vehicle (ID: 999)..." -ForegroundColor Yellow
try {
    $vehicle = Invoke-RestMethod -Uri http://localhost:8081/api/vehicles/999 -Method POST
    Write-Host "SUCCESS: Vehicle created!" -ForegroundColor Green
    Write-Output ($vehicle | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "FAILED to create vehicle: $_" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 2: GET (List Vehicles)
Write-Host "`n[2/3] Fetching active fleet status..." -ForegroundColor Yellow
try {
    $allVehicles = Invoke-RestMethod -Uri http://localhost:8081/api/vehicles -Method GET
    Write-Host "SUCCESS: Retrieved fleet." -ForegroundColor Green
    Write-Output ($allVehicles | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "FAILED to fetch fleet: $_" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 3: DELETE (Remove Vehicle)
Write-Host "`n[3/3] Removing vehicle (ID: 999) and terminating container..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri http://localhost:8081/api/vehicles/999 -Method DELETE
    Write-Host "SUCCESS: Vehicle 999 deleted and container destroyed." -ForegroundColor Green
} catch {
    Write-Host "FAILED to delete vehicle: $_" -ForegroundColor Red
}

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "    CRUD Iterative Tests Completed!          " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
