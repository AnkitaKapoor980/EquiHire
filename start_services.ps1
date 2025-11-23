# Start all EquiHire services
$ErrorActionPreference = "Continue"
$repoRoot = "F:\Capstone 2\equihire-ai"
Set-Location $repoRoot

# Environment variables
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "equihire"
$env:POSTGRES_USER = "admin"
$env:POSTGRES_PASSWORD = "admin123"
$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin"
$env:MINIO_BUCKET_NAME = "resumes"
$env:MINIO_SECURE = "False"
$env:PARSER_SERVICE_URL = "http://localhost:5001"
$env:MATCHER_SERVICE_URL = "http://localhost:5002"
$env:FAIRNESS_SERVICE_URL = "http://localhost:5003"
$env:EXPLAINABILITY_SERVICE_URL = "http://localhost:5004"

Write-Host "Starting EquiHire Services..." -ForegroundColor Cyan

# Start Django
Write-Host "Starting Django (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$repoRoot\backend\django_app'; `$env:POSTGRES_HOST='localhost'; `$env:MINIO_ENDPOINT='localhost:9000'; python manage.py runserver"

Start-Sleep -Seconds 3

# Start Flask Services
$services = @(
    @{ Name = "Parser Service"; Port = 5001; Path = "$repoRoot\backend\flask_services\parser_service" },
    @{ Name = "Matcher Service"; Port = 5002; Path = "$repoRoot\backend\flask_services\matcher_service" },
    @{ Name = "Fairness Service"; Port = 5003; Path = "$repoRoot\backend\flask_services\fairness_service" },
    @{ Name = "Explainability Service"; Port = 5004; Path = "$repoRoot\backend\flask_services\explainability_service" }
)

foreach ($svc in $services) {
    Write-Host "Starting $($svc.Name) (port $($svc.Port))..." -ForegroundColor Yellow
    $envCmd = "`$env:POSTGRES_HOST='localhost'; `$env:POSTGRES_PORT='5432'; `$env:POSTGRES_DB='equihire'; `$env:POSTGRES_USER='admin'; `$env:POSTGRES_PASSWORD='admin123'"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$($svc.Path)'; $envCmd; python app.py"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "All services launched in separate windows!" -ForegroundColor Green
Write-Host "Waiting 20 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Test all services
Write-Host ""
Write-Host "Testing services..." -ForegroundColor Cyan

$urls = @(
    @{ Name = "Django"; Url = "http://localhost:8000/api/health/" },
    @{ Name = "Parser"; Url = "http://localhost:5001/health" },
    @{ Name = "Matcher"; Url = "http://localhost:5002/health" },
    @{ Name = "Fairness"; Url = "http://localhost:5003/health" },
    @{ Name = "Explainability"; Url = "http://localhost:5004/health" }
)

foreach ($test in $urls) {
    try {
        $response = Invoke-WebRequest -Uri $test.Url -UseBasicParsing -TimeoutSec 5
        Write-Host "OK $($test.Name): Running (Status: $($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "FAILED $($test.Name): Not responding" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "   Django: http://localhost:8000" -ForegroundColor White
Write-Host "   Parser: http://localhost:5001" -ForegroundColor White
Write-Host "   Matcher: http://localhost:5002" -ForegroundColor White
Write-Host "   Fairness: http://localhost:5003" -ForegroundColor White
Write-Host "   Explainability: http://localhost:5004" -ForegroundColor White
