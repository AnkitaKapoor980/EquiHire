# Database Access Guide for EquiHire AI

## Where Data is Stored

The EquiHire AI application uses **PostgreSQL** as the database. All data is stored in PostgreSQL tables.

### Database Configuration

Based on `settings.py`, the database connection details are:
- **Database Name**: `equihire` (default, can be overridden by `POSTGRES_DB` environment variable)
- **Host**: `postgres` (default, can be overridden by `POSTGRES_HOST` environment variable)
- **Port**: `5432` (default PostgreSQL port)
- **User**: `admin` (default, can be overridden by `POSTGRES_USER` environment variable)
- **Password**: `admin123` (default, can be overridden by `POSTGRES_PASSWORD` environment variable)

## Main Database Tables

The application uses the following main tables:

1. **users** - User accounts (recruiters and candidates)
2. **job_descriptions** - Job postings
3. **applications** - Job applications
4. **resumes** - Resume files and parsed data
5. **candidate_profiles** - Extended candidate profile information

## How to Check Data Manually

### Method 1: Using Django Admin Panel (Easiest)

1. **Start the Django server**:
   ```bash
   cd backend/django_app
   python manage.py runserver
   ```

2. **Access the admin panel**:
   - Open your browser and go to: `http://localhost:8000/admin/`
   - Login with a superuser account (create one if needed)

3. **Create a superuser** (if you don't have one):
   ```bash
   python manage.py createsuperuser
   ```

4. **Browse data**:
   - Navigate through the admin interface to view:
     - Users
     - Job Descriptions
     - Applications
     - Resumes
     - Candidate Profiles

### Method 2: Using Django Shell

1. **Open Django shell**:
   ```bash
   cd backend/django_app
   python manage.py shell
   ```

2. **Query data**:
   ```python
   # Import models
   from accounts.models import User
   from jobs.models import JobDescription, Application
   from candidates.models import Resume, CandidateProfile
   
   # View all users
   users = User.objects.all()
   for user in users:
       print(f"{user.email} - {user.role}")
   
   # View all jobs
   jobs = JobDescription.objects.all()
   for job in jobs:
       print(f"{job.id}: {job.title} - Posted by {job.posted_by.email}")
   
   # View all applications
   applications = Application.objects.all()
   for app in applications:
       print(f"Application {app.id}: {app.resume.candidate.email} -> {app.job.title}")
   
   # View all resumes
   resumes = Resume.objects.all()
   for resume in resumes:
       print(f"{resume.id}: {resume.file_name} - {resume.candidate.email}")
   ```

### Method 3: Using PostgreSQL Command Line (psql)

1. **Connect to PostgreSQL**:
   ```bash
   # If using Docker
   docker exec -it <postgres_container_name> psql -U admin -d equihire
   
   # Or if PostgreSQL is installed locally
   psql -U admin -d equihire -h localhost
   ```

2. **Run SQL queries**:
   ```sql
   -- View all users
   SELECT id, email, username, role, first_name, last_name, created_at 
   FROM users;
   
   -- View all job descriptions
   SELECT id, title, location, employment_type, is_active, created_at 
   FROM job_descriptions;
   
   -- View all applications
   SELECT a.id, a.status, a.score, 
          j.title as job_title,
          u.email as candidate_email
   FROM applications a
   JOIN job_descriptions j ON a.job_id = j.id
   JOIN resumes r ON a.resume_id = r.id
   JOIN users u ON r.candidate_id = u.id;
   
   -- View all resumes
   SELECT r.id, r.file_name, r.file_size, r.is_active,
          u.email as candidate_email
   FROM resumes r
   JOIN users u ON r.candidate_id = u.id;
   
   -- Count records
   SELECT 
       (SELECT COUNT(*) FROM users) as total_users,
       (SELECT COUNT(*) FROM job_descriptions) as total_jobs,
       (SELECT COUNT(*) FROM applications) as total_applications,
       (SELECT COUNT(*) FROM resumes) as total_resumes;
   ```

### Method 4: Using pgAdmin (GUI Tool)

1. **Install pgAdmin** (if not already installed):
   - Download from: https://www.pgadmin.org/download/

2. **Connect to database**:
   - Host: `localhost` (or `postgres` if using Docker)
   - Port: `5432`
   - Database: `equihire`
   - Username: `admin`
   - Password: `admin123`

3. **Browse tables**:
   - Navigate to: Servers → PostgreSQL → Databases → equihire → Schemas → public → Tables
   - Right-click on any table → View/Edit Data → All Rows

### Method 5: Using Python Script

Create a file `check_data.py`:

```python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equihire.settings')
django.setup()

from accounts.models import User
from jobs.models import JobDescription, Application
from candidates.models import Resume

# Print summary
print("=" * 50)
print("DATABASE SUMMARY")
print("=" * 50)

print(f"\nTotal Users: {User.objects.count()}")
print(f"  - Recruiters: {User.objects.filter(role='recruiter').count()}")
print(f"  - Candidates: {User.objects.filter(role='candidate').count()}")

print(f"\nTotal Jobs: {JobDescription.objects.count()}")
print(f"  - Active: {JobDescription.objects.filter(is_active=True).count()}")
print(f"  - Inactive: {JobDescription.objects.filter(is_active=False).count()}")

print(f"\nTotal Applications: {Application.objects.count()}")
print(f"  - Pending: {Application.objects.filter(status='pending').count()}")
print(f"  - Shortlisted: {Application.objects.filter(status='shortlisted').count()}")
print(f"  - Rejected: {Application.objects.filter(status='rejected').count()}")

print(f"\nTotal Resumes: {Resume.objects.count()}")
print(f"  - Active: {Resume.objects.filter(is_active=True).count()}")

# List recent jobs
print("\n" + "=" * 50)
print("RECENT JOBS")
print("=" * 50)
for job in JobDescription.objects.order_by('-created_at')[:5]:
    print(f"{job.id}: {job.title} - {job.posted_by.email}")

# List recent applications
print("\n" + "=" * 50)
print("RECENT APPLICATIONS")
print("=" * 50)
for app in Application.objects.select_related('job', 'resume', 'resume__candidate').order_by('-created_at')[:5]:
    print(f"{app.id}: {app.resume.candidate.email} -> {app.job.title} (Score: {app.score})")
```

Run it:
```bash
cd backend/django_app
python check_data.py
```

## File Storage (Resumes)

Resume files are stored in **MinIO** (S3-compatible object storage), not in the database. The database only stores:
- File metadata (name, size, type, path)
- Parsed data (skills, education, experience)
- Embeddings (vector data)

To check MinIO:
1. Access MinIO console (usually at `http://localhost:9001`)
2. Login with MinIO credentials
3. Browse the `resumes` bucket

## Quick Data Check Commands

```bash
# Using Django management command
cd backend/django_app
python manage.py shell -c "from jobs.models import JobDescription; print(JobDescription.objects.count())"

# Using psql
psql -U admin -d equihire -c "SELECT COUNT(*) FROM job_descriptions;"
```

## Troubleshooting

If you can't connect to the database:
1. Check if PostgreSQL is running: `docker ps` (if using Docker)
2. Verify connection settings in `.env` file
3. Check database logs: `docker logs <postgres_container_name>`

