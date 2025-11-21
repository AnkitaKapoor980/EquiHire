# Architecture Documentation

## System Overview

EquiHire AI is a microservices-based Applicant Tracking System with AI-powered resume screening capabilities. The system is designed for scalability, maintainability, and responsible AI practices.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web Browser / Mobile App / API Clients)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Django)                      │
│  - Authentication & Authorization                           │
│  - Request Routing                                           │
│  - Rate Limiting                                             │
└──────┬──────────┬──────────┬──────────┬────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Parser  │ │ Matcher  │ │ Fairness │ │Explain-  │
│ Service  │ │ Service  │ │ Service  │ │ability   │
│ (Flask)  │ │ (Flask)  │ │ (Flask)  │ │Service   │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │           │            │            │
     └───────────┴────────────┴────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ PostgreSQL   │        │    MinIO     │
│ (with pgvector)       │ (Object Storage)│
└──────────────┘        └──────────────┘
```

## Components

### 1. API Gateway (Django)

**Purpose**: Main entry point, authentication, and orchestration

**Responsibilities**:
- User authentication and authorization
- Request routing to microservices
- Data aggregation
- Business logic

**Technology**: Django 4.2+, Django REST Framework

**Key Apps**:
- `accounts`: User management
- `jobs`: Job posting management
- `candidates`: Resume and candidate management
- `dashboard`: Analytics and dashboards
- `api`: API gateway endpoints

### 2. Parser Service (Flask)

**Purpose**: Extract structured data from resume files

**Responsibilities**:
- PDF/DOCX text extraction
- Entity extraction (skills, education, experience)
- Text cleaning and normalization

**Technology**: Flask 3.0+, PyMuPDF, spaCy

**Endpoints**:
- `POST /api/parse`: Parse resume file

### 3. Matcher Service (Flask)

**Purpose**: Generate embeddings and match resumes to jobs

**Responsibilities**:
- Sentence-BERT embedding generation
- Cosine similarity calculation
- Top-K candidate retrieval

**Technology**: Flask 3.0+, Sentence-Transformers, scikit-learn

**Endpoints**:
- `POST /api/embed`: Generate embedding
- `POST /api/match`: Match resumes to job
- `POST /api/batch_embed`: Batch embedding generation

### 4. Fairness Service (Flask)

**Purpose**: Detect and mitigate bias in hiring decisions

**Responsibilities**:
- Calculate fairness metrics (disparate impact, demographic parity)
- Apply bias mitigation techniques
- Generate fairness reports

**Technology**: Flask 3.0+, AIF360, Fairlearn

**Endpoints**:
- `POST /api/audit`: Audit application for fairness
- `POST /api/mitigate`: Apply bias mitigation

### 5. Explainability Service (Flask)

**Purpose**: Provide explanations for matching decisions

**Responsibilities**:
- SHAP value calculation
- Feature importance extraction
- Explanation generation

**Technology**: Flask 3.0+, SHAP

**Endpoints**:
- `POST /api/explain`: Generate explanation
- `POST /api/batch_explain`: Batch explanation generation

### 6. Database (PostgreSQL)

**Purpose**: Persistent data storage

**Features**:
- pgvector extension for vector similarity search
- JSON fields for flexible data storage
- Proper indexing for performance

**Key Tables**:
- `users`: User accounts
- `job_descriptions`: Job postings with embeddings
- `resumes`: Resumes with parsed data and embeddings
- `applications`: Job applications with scores and explanations

### 7. Object Storage (MinIO)

**Purpose**: Store resume files

**Features**:
- S3-compatible API
- Presigned URLs for secure access
- Scalable storage

## Data Flow

### Resume Upload Flow

1. Client uploads resume file to Django API
2. Django uploads file to MinIO
3. Django calls Parser Service with file
4. Parser Service extracts text and entities
5. Django stores parsed data in PostgreSQL
6. Django calls Matcher Service to generate embedding
7. Embedding stored in PostgreSQL with pgvector

### Job Matching Flow

1. Recruiter creates job posting
2. Django calls Matcher Service to generate job embedding
3. Embedding stored in PostgreSQL
4. Recruiter requests candidate matching
5. Django calls Matcher Service with job embedding
6. Matcher Service queries PostgreSQL for resume embeddings
7. Calculates cosine similarity
8. Returns top-K matches
9. Django calls Fairness Service for bias audit
10. Django calls Explainability Service for explanations
11. Results stored in Application records

## Security

- Token-based authentication (Django REST Framework)
- Role-based access control (Recruiter, Candidate, Admin)
- Secure file storage (MinIO with presigned URLs)
- Environment variable-based configuration
- CORS configuration for API access

## Scalability

- Microservices architecture allows independent scaling
- Horizontal scaling with Kubernetes
- Database connection pooling
- Caching strategies (Redis - optional)
- Load balancing for services

## Monitoring

- Health check endpoints for all services
- Logging with structured formats
- Prometheus metrics (basic setup)
- Error tracking and alerting

## Deployment

### Development
- Docker Compose for local development
- All services in single compose file

### Production
- Kubernetes for orchestration
- Separate deployments for each service
- Managed database (RDS, Cloud SQL, etc.)
- Managed object storage (S3, GCS, Azure Blob)

## Performance Targets

- Resume matching NDCG@10: ≥ 0.70
- Disparate impact ratio: 0.8-1.25
- End-to-end latency: < 2s for 5k resumes
- 100% of candidates have SHAP explanations

## Future Enhancements

- Real-time notifications (WebSockets)
- Advanced ML models (fine-tuned transformers)
- Multi-language support
- Integration with job boards
- Advanced analytics and reporting
- Mobile applications

