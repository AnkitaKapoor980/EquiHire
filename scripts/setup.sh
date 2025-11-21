#!/bin/bash

# EquiHire AI Setup Script

set -e

echo "🚀 Setting up EquiHire AI..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "⚠️  .env.example not found, creating basic .env"
    cat > .env << EOF
DATABASE_URL=postgresql://admin:admin123@postgres:5432/equihire
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
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
EOF
    echo "✅ .env file created"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres minio

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Build and start all services
echo "🔨 Building and starting all services..."
docker-compose up -d --build

# Wait for Django to be ready
echo "⏳ Waiting for Django to be ready..."
sleep 15

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T django_app python manage.py init_db || echo "⚠️  init_db command may not exist, continuing..."

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec -T django_app python manage.py migrate

# Create superuser (optional)
echo "👤 To create a superuser, run:"
echo "   docker-compose exec django_app python manage.py createsuperuser"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application at:"
echo "   - Django Admin: http://localhost:8000/admin"
echo "   - API: http://localhost:8000/api/"
echo "   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "📚 Next steps:"
echo "   1. Create a superuser (see command above)"
echo "   2. Place Kaggle datasets in data/raw/"
echo "   3. Run: python data/load_data.py"
echo "   4. Run: python data/generate_embeddings.py"
echo ""

