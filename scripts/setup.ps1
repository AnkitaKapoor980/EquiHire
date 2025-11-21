# EquiHire AI Setup Script for Windows PowerShell

Write-Host "🚀 Setting up EquiHire AI..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
    } else {
        @"
DATABASE_URL=postgresql://admin:admin123@postgres:5432/equihire
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=resumes
MINIO_SECURE=False
PARSER_SERVICE_URL=http://parser_service:5001
MATCHER_SERVICE_URL=http://matcher_service:5002
FAIRNESS_SERVICE_URL=http://fairness_service:5003
EXPLAINABILITY_SERVICE_URL=http://explainability_service:5004
"@ | Out-File -FilePath .env -Encoding utf8
    }
    Write-Host "✅ .env file created" -ForegroundColor Green
}

# Start services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d postgres minio

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Build and start all services
Write-Host "🔨 Building and starting all services..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for Django to be ready
Write-Host "⏳ Waiting for Django to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Initialize database
Write-Host "🗄️  Initializing database..." -ForegroundColor Yellow
docker-compose exec -T django_app python manage.py init_db 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  init_db command may not exist, continuing..." -ForegroundColor Yellow
}

# Run migrations
Write-Host "📦 Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T django_app python manage.py migrate

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application at:" -ForegroundColor Cyan
Write-Host "   - Django Admin: http://localhost:8000/admin" -ForegroundColor White
Write-Host "   - API: http://localhost:8000/api/" -ForegroundColor White
Write-Host "   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor White
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Create a superuser: docker-compose exec django_app python manage.py createsuperuser" -ForegroundColor White
Write-Host "   2. Place Kaggle datasets in data/raw/" -ForegroundColor White
Write-Host "   3. Run: python data/load_data.py" -ForegroundColor White
Write-Host "   4. Run: python data/generate_embeddings.py" -ForegroundColor White
Write-Host ""

