# EquiHire AI - Applicant Tracking System

A production-ready ATS (Applicant Tracking System) with AI-powered resume screening, fairness auditing, and explainability features.

## Features

- **Resume Parsing**: Extract structured data from PDF/DOCX resumes using PyMuPDF and spaCy
- **Intelligent Matching**: Sentence-BERT embeddings with cosine similarity for resume-job matching
- **Fairness Auditing**: AIF360 and Fairlearn integration for bias detection and mitigation
- **Explainability**: SHAP-based explanations for matching decisions
- **Role-Based Access**: Separate dashboards for recruiters and candidates
- **Scalable Architecture**: Microservices with Docker and Kubernetes support

## Technology Stack

- **Backend**: Django 4.2+ (API Gateway), Flask 3.0+ (Microservices)
- **Database**: PostgreSQL 15+ with pgvector extension
- **Object Storage**: MinIO
- **ML/NLP**: Sentence-BERT, spaCy, scikit-learn
- **Responsible AI**: AIF360, Fairlearn, SHAP
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ with pgvector (if running without Docker)

### Running with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd equihire-ai
```

2. Start all services:
```bash
docker-compose up -d
```

3. Run database migrations:
```bash
docker-compose exec django_app python manage.py migrate
```

4. Create a superuser:
```bash
docker-compose exec django_app python manage.py createsuperuser
```

5. Access the application:
- Django Admin: http://localhost:8000/admin
- API: http://localhost:8000/api/
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Local Development

1. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start PostgreSQL and MinIO (or use Docker):
```bash
docker-compose up -d postgres minio
```

4. Run migrations:
```bash
cd backend/django_app
python manage.py migrate
```

5. Start Django development server:
```bash
python manage.py runserver
```

6. Start Flask services (in separate terminals):
```bash
# Parser service
cd backend/flask_services/parser_service
python app.py

# Matcher service
cd backend/flask_services/matcher_service
python app.py

# Fairness service
cd backend/flask_services/fairness_service
python app.py

# Explainability service
cd backend/flask_services/explainability_service
python app.py
```

## Project Structure

```
equihire-ai/
├── backend/
│   ├── django_app/          # Django main application
│   │   ├── accounts/        # User authentication
│   │   ├── jobs/           # Job postings
│   │   ├── candidates/     # Candidate management
│   │   ├── dashboard/      # Dashboard views
│   │   └── api/            # API gateway
│   └── flask_services/     # Microservices
│       ├── parser_service/
│       ├── matcher_service/
│       ├── fairness_service/
│       └── explainability_service/
├── data/                   # Data loading scripts
├── docker/                  # Dockerfiles
├── k8s/                    # Kubernetes manifests
├── tests/                  # Test files
└── docs/                   # Documentation
```

## API Documentation

### Authentication

Register a new user:
```bash
POST /api/auth/register/
{
  "email": "user@example.com",
  "username": "user",
  "password": "password123",
  "password_confirm": "password123",
  "role": "candidate"
}
```

Login:
```bash
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Resume Upload

```bash
POST /api/candidates/resumes/
Content-Type: multipart/form-data
file: <resume.pdf>
```

### Job Posting

```bash
POST /api/jobs/jobs/
{
  "title": "Software Engineer",
  "description": "Job description...",
  "requirements": "Requirements...",
  "employment_type": "full-time"
}
```

### Match Candidates

```bash
POST /api/jobs/jobs/{job_id}/match_candidates/
{
  "top_k": 10
}
```

## Data Loading

Load Kaggle datasets:
```bash
python data/load_data.py
```

Preprocess data:
```bash
python data/preprocess.py
```

Generate embeddings:
```bash
python data/generate_embeddings.py
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=backend --cov-report=html
```

## Deployment

### Kubernetes

1. Apply secrets:
```bash
kubectl create secret generic postgres-secret \
  --from-literal=password=your-password

kubectl create secret generic django-secret \
  --from-literal=secret-key=your-secret-key \
  --from-literal=database-url=postgresql://...
```

2. Deploy services:
```bash
kubectl apply -f k8s/
```

### Production Considerations

- Use environment variables for all secrets
- Enable HTTPS/TLS
- Set up proper monitoring (Prometheus/Grafana)
- Configure backup strategies for PostgreSQL
- Use managed object storage (S3, GCS) instead of MinIO in production
- Set up proper logging and error tracking

## Performance Metrics

- Resume matching NDCG@10: ≥ 0.70
- Disparate impact ratio: 0.8-1.25
- End-to-end latency: < 2s for 5k resumes
- 100% of candidates have SHAP explanations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.

