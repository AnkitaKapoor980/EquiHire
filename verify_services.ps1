# Script to verify all EquiHire services are running and accessible
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying EquiHire Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Service endpoints to check
$services = @(
    @{ Name = "Django API"; Url = "http://localhost:8000/api/health/"; ExpectedStatus = 200 },
    @{ Name = "Parser Service"; Url = "http://localhost:5001/health"; ExpectedStatus = 200 },
    @{ Name = "Matcher Service"; Url = "http://localhost:5002/health"; ExpectedStatus = 200 },
    @{ Name = "Fairness Service"; Url = "http://localhost:5003/health"; ExpectedStatus = 200 },
    @{ Name = "Explainability Service"; Url = "http://localhost:5004/health"; ExpectedStatus = 200 }
)

$allHealthy = $true
$results = @()

foreach ($service in $services) {
    Write-Host "Checking $($service.Name)..." -ForegroundColor Yellow -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq $service.ExpectedStatus) {
            Write-Host " [HEALTHY]" -ForegroundColor Green
            $results += @{ Name = $service.Name; Status = "HEALTHY"; Details = "Status: $($response.StatusCode)" }
        } else {
            Write-Host " [WARNING: Status $($response.StatusCode)]" -ForegroundColor Yellow
            $results += @{ Name = $service.Name; Status = "WARNING"; Details = "Status: $($response.StatusCode)" }
            $allHealthy = $false
        }
    } catch {
        Write-Host " [NOT RESPONDING]" -ForegroundColor Red
        $results += @{ Name = $service.Name; Status = "FAILED"; Details = $_.Exception.Message }
        $allHealthy = $false
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service Status Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $results) {
    $statusColor = switch ($result.Status) {
        "HEALTHY" { "Green" }
        "WARNING" { "Yellow" }
        default { "Red" }
    }
    Write-Host "$($result.Name): " -NoNewline
    Write-Host $result.Status -ForegroundColor $statusColor
    Write-Host "  $($result.Details)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Django API:        http://localhost:8000" -ForegroundColor White
Write-Host "Django Admin:      http://localhost:8000/admin" -ForegroundColor White
Write-Host "Parser Service:    http://localhost:5001" -ForegroundColor White
Write-Host "Matcher Service:   http://localhost:5002" -ForegroundColor White
Write-Host "Fairness Service:  http://localhost:5003" -ForegroundColor White
Write-Host "Explainability:    http://localhost:5004" -ForegroundColor White
Write-Host "MinIO Console:     http://localhost:9001" -ForegroundColor White

if ($allHealthy) {
    Write-Host ""
    Write-Host "SUCCESS: All services are healthy and accessible!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "WARNING: Some services are not responding. Check container logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs service_name" -ForegroundColor Gray
    exit 1
}
