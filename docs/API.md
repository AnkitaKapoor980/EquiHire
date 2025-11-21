# EquiHire API Documentation

## Base URL

- Development: `http://localhost:8000/api`
- Production: `https://api.equihire.com/api`

## Authentication

Most endpoints require authentication using token-based authentication.

### Register

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user",
  "password": "password123",
  "password_confirm": "password123",
  "role": "candidate"
}
```

### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "candidate"
  },
  "token": "abc123..."
}
```

Use the token in subsequent requests:
```http
Authorization: Token abc123...
```

## Endpoints

### Accounts

#### Get Profile
```http
GET /api/auth/profile/
Authorization: Token <token>
```

#### Update Profile
```http
PUT /api/auth/profile/update/
Authorization: Token <token>
Content-Type: application/json

{
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Resumes

#### Upload Resume
```http
POST /api/candidates/resumes/
Authorization: Token <token>
Content-Type: multipart/form-data

file: <resume.pdf>
```

#### List Resumes
```http
GET /api/candidates/resumes/
Authorization: Token <token>
```

#### Get Resume
```http
GET /api/candidates/resumes/{id}/
Authorization: Token <token>
```

#### Download Resume
```http
GET /api/candidates/resumes/{id}/download/
Authorization: Token <token>
```

### Jobs

#### List Jobs
```http
GET /api/jobs/jobs/
Authorization: Token <token>
```

Query parameters:
- `employment_type`: Filter by employment type
- `location`: Filter by location
- `search`: Search in title, description, requirements
- `ordering`: Order by field (e.g., `-created_at`)

#### Create Job
```http
POST /api/jobs/jobs/
Authorization: Token <token>
Content-Type: application/json

{
  "title": "Software Engineer",
  "description": "We are looking for...",
  "requirements": "5+ years experience...",
  "employment_type": "full-time",
  "location": "San Francisco, CA",
  "salary_min": 100000,
  "salary_max": 150000,
  "required_skills": ["Python", "Django", "PostgreSQL"]
}
```

#### Get Job
```http
GET /api/jobs/jobs/{id}/
Authorization: Token <token>
```

#### Match Candidates
```http
POST /api/jobs/jobs/{id}/match_candidates/
Authorization: Token <token>
Content-Type: application/json

{
  "top_k": 10
}
```

Response:
```json
{
  "matches": [
    {
      "resume_id": 1,
      "candidate_email": "candidate@example.com",
      "score": 0.85,
      "skills": ["Python", "Django"],
      "education": ["BS Computer Science"],
      "experience_years": 5
    }
  ]
}
```

### Applications

#### List Applications
```http
GET /api/jobs/applications/
Authorization: Token <token>
```

Query parameters:
- `job`: Filter by job ID
- `status`: Filter by status

#### Create Application
```http
POST /api/jobs/applications/
Authorization: Token <token>
Content-Type: application/json

{
  "job": 1,
  "resume": 1,
  "notes": "Optional notes"
}
```

#### Get Application
```http
GET /api/jobs/applications/{id}/
Authorization: Token <token>
```

#### Update Application Status
```http
PATCH /api/jobs/applications/{id}/
Authorization: Token <token>
Content-Type: application/json

{
  "status": "shortlisted",
  "notes": "Strong candidate"
}
```

#### Audit Fairness
```http
POST /api/jobs/applications/{id}/audit_fairness/
Authorization: Token <token>
```

#### Get Explanation
```http
POST /api/jobs/applications/{id}/explain/
Authorization: Token <token>
```

### Dashboard

#### Recruiter Dashboard
```http
GET /api/dashboard/recruiter/
Authorization: Token <token>
```

#### Candidate Dashboard
```http
GET /api/dashboard/candidate/
Authorization: Token <token>
```

#### Analytics
```http
GET /api/dashboard/analytics/
Authorization: Token <token>
```

## Microservices

### Parser Service

#### Health Check
```http
GET http://parser_service:5001/health
```

#### Parse Resume
```http
POST http://parser_service:5001/api/parse
Content-Type: multipart/form-data

file: <resume.pdf>
```

### Matcher Service

#### Generate Embedding
```http
POST http://matcher_service:5002/api/embed
Content-Type: application/json

{
  "text": "Software engineer with Python experience"
}
```

#### Match Resumes
```http
POST http://matcher_service:5002/api/match
Content-Type: application/json

{
  "job_embedding": [0.1, 0.2, ...],
  "job_id": 1,
  "top_k": 10
}
```

### Fairness Service

#### Audit Fairness
```http
POST http://fairness_service:5003/api/audit
Content-Type: application/json

{
  "application_id": 1,
  "job_id": 1,
  "score": 0.75
}
```

### Explainability Service

#### Explain Application
```http
POST http://explainability_service:5004/api/explain
Content-Type: application/json

{
  "application_id": 1,
  "job_id": 1,
  "resume_id": 1,
  "score": 0.75
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "details": {}
}
```

Status codes:
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

