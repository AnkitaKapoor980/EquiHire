Param(
    [switch]$SkipDocker,
    [switch]$SkipDataLoad,
    [switch]$SkipFlaskServices,
    [int]$DockerWaitSeconds = 12,
    [string]$PythonCmd = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $repoRoot

Write-Host "🚀 EquiHire full-stack launcher" -ForegroundColor Cyan

function Ensure-Tool {
    param (
        [string]$Command,
        [string]$InstallHint
    )

    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "❌ '$Command' was not found. $InstallHint" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Found $Command" -ForegroundColor Green
}

function Start-ServiceWindow {
    param (
        [string]$Name,
        [string]$Path,
        [string]$Command
    )

    $escapedCommand = "Set-Location `"$Path`"; $Command"
    Write-Host "➡️  Launching $Name ..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $escapedCommand | Out-Null
}

Ensure-Tool $PythonCmd "Install Python 3.11+ and ensure it is on PATH."

if (-not $SkipDocker) {
    Ensure-Tool "docker-compose" "Install Docker Desktop and restart PowerShell."
    Write-Host "🐳 Starting core infrastructure containers..." -ForegroundColor Yellow
    docker-compose up -d postgres minio
    Write-Host "⏳ Waiting $DockerWaitSeconds seconds for containers to become healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds $DockerWaitSeconds
} else {
    Write-Host "⚠️  Skipping docker-compose start (assuming Postgres + MinIO are already running)." -ForegroundColor Yellow
}

Push-Location "$repoRoot\backend\django_app"
Write-Host "📦 Applying database migrations..." -ForegroundColor Yellow
& $PythonCmd manage.py init_db
& $PythonCmd manage.py migrate
Pop-Location

if (-not $SkipDataLoad) {
    if (Test-Path "$repoRoot\data\load_data.py") {
        Write-Host "📥 Loading sample datasets (data/load_data.py) ..." -ForegroundColor Yellow
        & $PythonCmd data/load_data.py
    } else {
        Write-Host "⚠️  data/load_data.py not found, skipping sample data load." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Sample data load skipped." -ForegroundColor Yellow
}

Start-ServiceWindow "Django API (http://localhost:8000)" "$repoRoot\backend\django_app" "$PythonCmd manage.py runserver"

if (-not $SkipFlaskServices) {
    $flaskServices = @(
        @{ Name = "Parser Service (http://localhost:5001)"; Path = "$repoRoot\backend\flask_services\parser_service"; Command = "$PythonCmd app.py" },
        @{ Name = "Matcher Service (http://localhost:5002)"; Path = "$repoRoot\backend\flask_services\matcher_service"; Command = "$PythonCmd app.py" },
        @{ Name = "Fairness Service (http://localhost:5003)"; Path = "$repoRoot\backend\flask_services\fairness_service"; Command = "$PythonCmd app.py" },
        @{ Name = "Explainability Service (http://localhost:5004)"; Path = "$repoRoot\backend\flask_services\explainability_service"; Command = "$PythonCmd app.py" }
    )

    foreach ($svc in $flaskServices) {
        if (Test-Path $svc.Path) {
            Start-ServiceWindow $svc.Name $svc.Path $svc.Command
        } else {
            Write-Host "⚠️  Skipping missing service path $($svc.Path)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️  Flask microservices skipped." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ All processes launched in their own PowerShell windows." -ForegroundColor Green
Write-Host "🛑 Use CTRL+C inside each window to stop a service." -ForegroundColor Green
Write-Host "🐳 Run 'docker-compose down' when you want to stop Postgres/MinIO." -ForegroundColor Green

