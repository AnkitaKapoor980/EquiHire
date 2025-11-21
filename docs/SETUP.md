# Setup Guide

## Development Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Docker and Docker Compose (recommended)
- Git

### 2. Clone Repository

```bash
git clone <repository-url>
cd equihire-ai
```

### 3. Environment Setup

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
DATABASE_URL=postgresql://admin:admin123@localhost:5432/equihire
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Database Setup

#### Using Docker Compose

```bash
docker-compose up -d postgres
```

#### Manual Setup

1. Install PostgreSQL with pgvector:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15 postgresql-contrib-15
# Install pgvector extension
```

2. Create database:
```sql
CREATE DATABASE equihire;
CREATE EXTENSION vector;
```

### 5. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 6. Django Setup

```bash
cd backend/django_app
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### 7. Start Services

#### Option 1: Docker Compose (Recommended)

```bash
docker-compose up
```

#### Option 2: Manual

Start each service in separate terminals:

1. Django:
```bash
cd backend/django_app
python manage.py runserver
```

2. Parser Service:
```bash
cd backend/flask_services/parser_service
python app.py
```

3. Matcher Service:
```bash
cd backend/flask_services/matcher_service
python app.py
```

4. Fairness Service:
```bash
cd backend/flask_services/fairness_service
python app.py
```

5. Explainability Service:
```bash
cd backend/flask_services/explainability_service
python app.py
```

### 8. Load Data

Place Kaggle datasets in `data/raw/` directory, then:

```bash
python data/load_data.py
python data/preprocess.py
python data/generate_embeddings.py
```

## Production Setup

### 1. Environment Variables

Set all required environment variables in your deployment platform.

### 2. Database

Use managed PostgreSQL service with pgvector support.

### 3. Object Storage

Use S3, GCS, or Azure Blob Storage instead of MinIO.

### 4. Deploy with Kubernetes

```bash
kubectl apply -f k8s/
```

### 5. Monitoring

Set up Prometheus and Grafana for monitoring.

## Troubleshooting

### Database Connection Issues

- Check PostgreSQL is running
- Verify connection credentials
- Ensure pgvector extension is installed

### Service Communication Issues

- Verify all services are running
- Check service URLs in environment variables
- Review Docker network configuration

### Model Loading Issues

- Download spaCy model: `python -m spacy download en_core_web_sm`
- Check disk space for model downloads
- Verify internet connection for model downloads

