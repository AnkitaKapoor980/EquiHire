# Start all Flask microservices for EquiHire
$ErrorActionPreference = "Continue"
$repoRoot = $PSScriptRoot
if (-not $repoRoot) {
    $repoRoot = Get-Location
}
Set-Location $repoRoot

Write-Host "Starting EquiHire Flask Microservices..." -ForegroundColor Cyan

# Environment variables for database connection
$envVars = @{
    POSTGRES_HOST = "localhost"
    POSTGRES_PORT = "5432"
    POSTGRES_DB = "equihire"
    POSTGRES_USER = "admin"
    POSTGRES_PASSWORD = "admin123"
}

# Build environment variable string for PowerShell
$envCmd = ""
foreach ($key in $envVars.Keys) {
    $envCmd += "`$env:$key='$($envVars[$key])'; "
}

# Flask services configuration
$flaskServices = @(
    @{ 
        Name = "Parser Service"; 
        Port = 5001; 
        Path = "$repoRoot\backend\flask_services\parser_service"; 
        Command = "python app.py"
    },
    @{ 
        Name = "Matcher Service"; 
        Port = 5002; 
        Path = "$repoRoot\backend\flask_services\matcher_service"; 
        Command = "python app.py"
    },
    @{ 
        Name = "Fairness Service"; 
        Port = 5003; 
        Path = "$repoRoot\backend\flask_services\fairness_service"; 
        Command = "python app.py"
    },
    @{ 
        Name = "Explainability Service"; 
        Port = 5004; 
        Path = "$repoRoot\backend\flask_services\explainability_service"; 
        Command = "python app.py"
    }
)

# Start each Flask service in a separate window
foreach ($svc in $flaskServices) {
    if (Test-Path $svc.Path) {
        Write-Host "Starting $($svc.Name) on port $($svc.Port)..." -ForegroundColor Yellow
        
        $fullCommand = "Set-Location `"$($svc.Path)`"; $envCmd $($svc.Command)"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $fullCommand | Out-Null
        
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Skipping $($svc.Name) - path not found: $($svc.Path)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "All Flask services launched in separate PowerShell windows!" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "   Parser Service:        http://localhost:5001" -ForegroundColor White
Write-Host "   Matcher Service:       http://localhost:5002" -ForegroundColor White
Write-Host "   Fairness Service:      http://localhost:5003" -ForegroundColor White
Write-Host "   Explainability Service: http://localhost:5004" -ForegroundColor White
Write-Host ""
Write-Host "Waiting 15 seconds for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Test all services
Write-Host ""
Write-Host "Testing Flask services..." -ForegroundColor Cyan

$healthUrls = @(
    @{ Name = "Parser"; Url = "http://localhost:5001/health" },
    @{ Name = "Matcher"; Url = "http://localhost:5002/health" },
    @{ Name = "Fairness"; Url = "http://localhost:5003/health" },
    @{ Name = "Explainability"; Url = "http://localhost:5004/health" }
)

$allHealthy = $true
foreach ($test in $healthUrls) {
    try {
        $response = Invoke-WebRequest -Uri $test.Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "$($test.Name) Service: Running (Status: $($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "$($test.Name) Service: Not responding - $($_.Exception.Message)" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
if ($allHealthy) {
    Write-Host "All Flask services are healthy and running!" -ForegroundColor Green
} else {
    Write-Host "Some services may still be starting. Check the PowerShell windows for errors." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To stop services, close each PowerShell window or press CTRL+C in each window." -ForegroundColor Yellow

