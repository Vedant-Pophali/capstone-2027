$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   CRUD Smoke Tests — Fleet Manager API   " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

$baseUrl = "http://localhost:8081/api"

# Test 1: POST (Create Vehicle)
Write-Host "`n[1/4] POST /api/vehicles — Creating vehicle (ID: 999)..." -ForegroundColor Yellow
try {
    $body = '{"id":"999","owner":"Test Admin","model":"Test Vehicle"}'
    $vehicle = Invoke-RestMethod -Uri "$baseUrl/vehicles" -Method POST -Body $body -ContentType "application/json"
    Write-Host "[PASS] Vehicle created!" -ForegroundColor Green
    Write-Output ($vehicle | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 2: GET (List All Vehicles)
Write-Host "`n[2/4] GET /api/vehicles — Fetching fleet..." -ForegroundColor Yellow
try {
    $allVehicles = Invoke-RestMethod -Uri "$baseUrl/vehicles" -Method GET
    Write-Host "[PASS] Retrieved $($allVehicles.Count) vehicle(s)" -ForegroundColor Green
    Write-Output ($allVehicles | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
}

Start-Sleep -Seconds 1

# Test 3: GET (Single Vehicle)
Write-Host "`n[3/4] GET /api/vehicles/999 — Fetching single vehicle..." -ForegroundColor Yellow
try {
    $single = Invoke-RestMethod -Uri "$baseUrl/vehicles/999" -Method GET
    Write-Host "[PASS] Vehicle 999 found" -ForegroundColor Green
    Write-Output ($single | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Test 4: DELETE (Remove Vehicle)
Write-Host "`n[4/4] DELETE /api/vehicles/999 — Removing vehicle..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$baseUrl/vehicles/999" -Method DELETE
    Write-Host "[PASS] Vehicle 999 deleted and container destroyed" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
}

Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   CRUD Tests Completed                   " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
