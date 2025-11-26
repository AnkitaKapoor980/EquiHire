# Comprehensive verification script for EquiHire application
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EquiHire Application - Complete Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker containers
Write-Host "1. Checking Docker Containers..." -ForegroundColor Yellow
$containers = docker-compose ps --format json | ConvertFrom-Json
$runningContainers = $containers | Where-Object { $_.State -eq "running" }
Write-Host "   Running containers: $($runningContainers.Count)/$($containers.Count)" -ForegroundColor $(if ($runningContainers.Count -eq $containers.Count) { "Green" } else { "Yellow" })

foreach ($container in $containers) {
    $statusColor = switch ($container.Health) {
        "healthy" { "Green" }
        "unhealthy" { "Red" }
        default { "Yellow" }
    }
    Write-Host "   - $($container.Service): $($container.State) ($($container.Health))" -ForegroundColor $statusColor
}

Write-Host ""

# Check service health endpoints
Write-Host "2. Checking Service Health Endpoints..." -ForegroundColor Yellow
$services = @(
    @{ Name = "Django API"; Url = "http://localhost:8000/api/health/"; ExpectedStatus = 200 },
    @{ Name = "Parser Service"; Url = "http://localhost:5001/health"; ExpectedStatus = 200 },
    @{ Name = "Matcher Service"; Url = "http://localhost:5002/health"; ExpectedStatus = 200 },
    @{ Name = "Fairness Service"; Url = "http://localhost:5003/health"; ExpectedStatus = 200 },
    @{ Name = "Explainability Service"; Url = "http://localhost:5004/health"; ExpectedStatus = 200 }
)

$allHealthy = $true
foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq $service.ExpectedStatus) {
            Write-Host "   - $($service.Name): [HEALTHY]" -ForegroundColor Green
        } else {
            Write-Host "   - $($service.Name): [WARNING: Status $($response.StatusCode)]" -ForegroundColor Yellow
            $allHealthy = $false
        }
    } catch {
        Write-Host "   - $($service.Name): [NOT RESPONDING]" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""

# Check database connection
Write-Host "3. Checking Database Connection..." -ForegroundColor Yellow
try {
    $dbCheck = docker-compose exec -T postgres psql -U admin -d equihire -c "SELECT version();" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   - PostgreSQL: [CONNECTED]" -ForegroundColor Green
        $pgvectorCheck = docker-compose exec -T postgres psql -U admin -d equihire -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" 2>&1
        if ($pgvectorCheck -match "vector") {
            Write-Host "   - pgvector extension: [INSTALLED]" -ForegroundColor Green
        } else {
            Write-Host "   - pgvector extension: [NOT FOUND]" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   - PostgreSQL: [CONNECTION FAILED]" -ForegroundColor Red
    }
} catch {
    Write-Host "   - Database check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check data files
Write-Host "4. Checking Data Files..." -ForegroundColor Yellow
$dataDir = "data/raw"
if (Test-Path $dataDir) {
    $csvFiles = Get-ChildItem -Path $dataDir -Filter "*.csv" -ErrorAction SilentlyContinue
    if ($csvFiles) {
        Write-Host "   - Found $($csvFiles.Count) CSV file(s):" -ForegroundColor Green
        foreach ($file in $csvFiles) {
            Write-Host "     * $($file.Name)" -ForegroundColor White
        }
    } else {
        Write-Host "   - No CSV files found in data/raw/" -ForegroundColor Yellow
        Write-Host "     (This is OK - data loading will be skipped)" -ForegroundColor Gray
    }
} else {
    Write-Host "   - Data directory not found: $dataDir" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allHealthy -and $runningContainers.Count -eq $containers.Count) {
    Write-Host "SUCCESS: All services are running and healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access your application at:" -ForegroundColor Cyan
    Write-Host "  - Django API:        http://localhost:8000" -ForegroundColor White
    Write-Host "  - Django Admin:      http://localhost:8000/admin" -ForegroundColor White
    Write-Host "  - Parser Service:    http://localhost:5001" -ForegroundColor White
    Write-Host "  - Matcher Service:   http://localhost:5002" -ForegroundColor White
    Write-Host "  - Fairness Service:  http://localhost:5003" -ForegroundColor White
    Write-Host "  - Explainability:   http://localhost:5004" -ForegroundColor White
    Write-Host "  - MinIO Console:     http://localhost:9001" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Add CSV files to data/raw/ to load sample data" -ForegroundColor White
    Write-Host "  2. Run: docker-compose exec django_app python data/load_data.py" -ForegroundColor White
    Write-Host "  3. Access the admin panel and create users/jobs" -ForegroundColor White
    exit 0
} else {
    Write-Host "WARNING: Some services may not be fully operational." -ForegroundColor Yellow
    Write-Host "Check container logs with: docker-compose logs [service_name]" -ForegroundColor Gray
    exit 1
}

