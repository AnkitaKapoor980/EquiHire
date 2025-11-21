# EquiHire AI Startup Script
# This script helps you start the application

Write-Host "🚀 EquiHire AI Startup Script" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "backend/django_app/manage.py")) {
    Write-Host "❌ Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import django; print('Django:', django.get_version())" 2>&1 | Out-Null
    Write-Host "✅ Dependencies appear to be installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Dependencies may not be installed. Run: pip install -r backend/requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Setup Options:" -ForegroundColor Cyan
Write-Host "1. Start database with Docker (recommended)" -ForegroundColor White
Write-Host "2. Use existing PostgreSQL database" -ForegroundColor White
Write-Host "3. Just run migrations and start server" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
        docker-compose up -d postgres minio
        
        Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        Write-Host "📦 Running database migrations..." -ForegroundColor Yellow
        cd backend/django_app
        python manage.py init_db
        python manage.py migrate
        
        Write-Host ""
        Write-Host "👤 Create a superuser (optional):" -ForegroundColor Cyan
        Write-Host "   python manage.py createsuperuser" -ForegroundColor White
        
        Write-Host ""
        Write-Host "🚀 Starting Django server..." -ForegroundColor Yellow
        Write-Host "   Access at: http://localhost:8000" -ForegroundColor Green
        Write-Host ""
        python manage.py runserver
    }
    "2" {
        Write-Host ""
        $dbHost = Read-Host "Enter PostgreSQL host (default: localhost)"
        if ([string]::IsNullOrWhiteSpace($dbHost)) { $dbHost = "localhost" }
        
        $env:POSTGRES_HOST = $dbHost
        Write-Host "📦 Running database migrations..." -ForegroundColor Yellow
        cd backend/django_app
        python manage.py init_db
        python manage.py migrate
        
        Write-Host ""
        Write-Host "👤 Create a superuser (optional):" -ForegroundColor Cyan
        Write-Host "   python manage.py createsuperuser" -ForegroundColor White
        
        Write-Host ""
        Write-Host "🚀 Starting Django server..." -ForegroundColor Yellow
        Write-Host "   Access at: http://localhost:8000" -ForegroundColor Green
        Write-Host ""
        python manage.py runserver
    }
    "3" {
        Write-Host ""
        Write-Host "📦 Running database migrations..." -ForegroundColor Yellow
        cd backend/django_app
        python manage.py init_db
        python manage.py migrate
        
        Write-Host ""
        Write-Host "🚀 Starting Django server..." -ForegroundColor Yellow
        Write-Host "   Access at: http://localhost:8000" -ForegroundColor Green
        Write-Host ""
        python manage.py runserver
    }
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

