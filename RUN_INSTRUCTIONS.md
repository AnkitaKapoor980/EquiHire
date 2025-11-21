# How to Run EquiHire AI

## One-Command Startup (Hybrid Recommended)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_full_stack.ps1
```

This script:
- Starts Postgres + MinIO in Docker
- Runs `init_db` + `migrate` (and data loader)
- Launches Django + all Flask services in separate terminals

Use switches if needed: `...run_full_stack.ps1 -SkipDataLoad`, `-SkipFlaskServices`, or `-SkipDocker`.

---

## Quick Start (Docker - Recommended)

### Step 1: Start Database and Services
```powershell
docker-compose up -d postgres minio
```

Wait 10-15 seconds for services to be ready.

### Step 2: Initialize Database and Run Migrations
```powershell
cd backend/django_app
python manage.py init_db
python manage.py migrate
```

**Note:** If running outside Docker, set environment variable:
```powershell
$env:POSTGRES_HOST="localhost"
```

### Step 3: Create Superuser (Optional)
```powershell
python manage.py createsuperuser
```

### Step 4: Load Your Datasets
```powershell
cd ../..
python data/load_data.py
```

This will load:
- 2,484 resumes from `data/raw/resume_data.csv`
- 1,068 jobs from `data/raw/job_data.csv`

### Step 5: Start Django Server
```powershell
cd backend/django_app
python manage.py runserver
```

The application will be available at: **http://localhost:8000**

---

## Option 2: Full Docker Setup (All Services)

### Step 1: Start All Services
```powershell
docker-compose up -d
```

### Step 2: Initialize Database
```powershell
docker-compose exec django_app python manage.py init_db
docker-compose exec django_app python manage.py migrate
docker-compose exec django_app python manage.py createsuperuser
```

### Step 3: Load Data
```powershell
python data/load_data.py
```

**Note:** For Docker, you may need to set:
```powershell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="5432"
```

### Step 4: Access Application
- **Django Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/
- **Dashboard:** http://localhost:8000/dashboard/
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

---

## Option 3: Local Development (Without Docker)

### Prerequisites
- PostgreSQL 15+ with pgvector extension installed
- Python 3.11+
- All dependencies installed: `pip install -r backend/requirements.txt`

### Step 1: Create .env File
Create a `.env` file in the root directory:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=resumes
MINIO_SECURE=False
PARSER_SERVICE_URL=http://localhost:5001
MATCHER_SERVICE_URL=http://localhost:5002
FAIRNESS_SERVICE_URL=http://localhost:5003
EXPLAINABILITY_SERVICE_URL=http://localhost:5004
```

### Step 2: Create PostgreSQL Database
```sql
CREATE DATABASE equihire;
CREATE EXTENSION vector;
```

### Step 3: Initialize and Migrate
```powershell
cd backend/django_app
python manage.py init_db
python manage.py migrate
python manage.py createsuperuser
```

### Step 4: Load Data
```powershell
cd ../..
python data/load_data.py
```

### Step 5: Start Django Server
```powershell
cd backend/django_app
python manage.py runserver
```

### Step 6: Start Flask Services (Separate Terminals)
```powershell
# Terminal 2: Parser Service
cd backend/flask_services/parser_service
python app.py

# Terminal 3: Matcher Service
cd backend/flask_services/matcher_service
python app.py

# Terminal 4: Fairness Service
cd backend/flask_services/fairness_service
python app.py

# Terminal 5: Explainability Service
cd backend/flask_services/explainability_service
python app.py
```

---

## Available Endpoints

Once running, you can access:

- **Home/Dashboard:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **API Health:** http://localhost:8000/api/health/
- **Jobs API:** http://localhost:8000/api/jobs/
- **Candidates API:** http://localhost:8000/api/candidates/
- **Authentication:** http://localhost:8000/api/auth/

---

## Troubleshooting

### Database Connection Error
- Check if PostgreSQL is running
- Verify database credentials in `.env` or environment variables
- For Docker: Use `postgres` as hostname
- For Local: Use `localhost` as hostname

### Port Already in Use
- Change port: `python manage.py runserver 8001`
- Or stop the service using port 8000

### pgvector Extension Error
- Make sure PostgreSQL has pgvector extension installed
- Run: `python manage.py init_db` to create the extension

### Data Loading Issues
- Ensure CSV files are in `data/raw/` directory
- Check database connection settings
- Verify file names match: `*resume*.csv` and `*job*.csv`

---

## Next Steps After Running

1. **Generate Embeddings** (requires matcher service running):
   ```powershell
   python data/generate_embeddings.py
   ```

2. **Access Admin Panel** to manage users, jobs, and candidates

3. **Test API Endpoints** using tools like Postman or curl

4. **Upload Resumes** via the candidates interface

5. **Create Job Postings** via the jobs interface

6. **Match Candidates** to jobs using the matching API


