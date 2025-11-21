# 🚀 START HERE - EquiHire AI Quick Start Guide

## ✅ Codebase Status: READY

Your codebase is complete and ready to run! Here's how to start it and verify it's working.

---

## 📋 Pre-Flight Checklist

Before starting, ensure you have:
- ✅ Python 3.11+ installed
- ✅ PostgreSQL 15+ installed (or Docker for database)
- ✅ All datasets in `data/raw/` (already done ✅)

---

## 🎯 Quick Start (3 Steps)

### Step 1: Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 2: Setup Database & Run Migrations
```powershell
# Option A: Using Docker for database only
docker-compose up -d postgres minio

# Wait 10 seconds, then:
cd backend/django_app
python manage.py init_db
python manage.py migrate
python manage.py createsuperuser

# Option B: Using local PostgreSQL
# Make sure PostgreSQL is running and create database:
# CREATE DATABASE equihire;
# CREATE EXTENSION vector;
# Then set environment variable:
$env:POSTGRES_HOST="localhost"
python manage.py init_db
python manage.py migrate
python manage.py createsuperuser
```

### Step 3: Start the Server
```powershell
python manage.py runserver
```

**🎉 Your app is now running at: http://localhost:8000**

---

## ✅ Verification Steps

### 1. Check Health Endpoint
Open your browser or use PowerShell:
```powershell
curl http://localhost:8000/api/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "equihire-api"
}
```

### 2. Check API Info
```powershell
curl http://localhost:8000/api/info/
```

**Expected Response:**
```json
{
  "name": "EquiHire API",
  "version": "1.0.0",
  "description": "Applicant Tracking System with AI-powered Resume Screening",
  "endpoints": {
    "auth": "/api/auth/",
    "jobs": "/api/jobs/",
    "candidates": "/api/candidates/",
    "dashboard": "/api/dashboard/"
  }
}
```

### 3. Access Admin Panel
- URL: http://localhost:8000/admin/
- Login with the superuser you created

### 4. Load Your Data (Optional but Recommended)
```powershell
cd ../..
python data/load_data.py
```

This loads:
- ✅ 2,484 resumes
- ✅ 1,068 job postings

---

## 🔍 Troubleshooting

### Issue: "Module not found" or Import Error
**Solution:** Install dependencies
```powershell
pip install -r backend/requirements.txt
```

### Issue: Database Connection Error
**Solution:** 
- Check if PostgreSQL is running
- Verify database exists: `CREATE DATABASE equihire;`
- Set environment variable: `$env:POSTGRES_HOST="localhost"`

### Issue: Port 8000 Already in Use
**Solution:** Use a different port
```powershell
python manage.py runserver 8001
```

### Issue: pgvector Extension Error
**Solution:** Run init_db command
```powershell
python manage.py init_db
```

---

## 📊 What's Working

Once started, you can:

1. **Access Admin Panel** - http://localhost:8000/admin/
2. **Use REST API** - http://localhost:8000/api/
3. **View Dashboard** - http://localhost:8000/dashboard/
4. **Health Check** - http://localhost:8000/api/health/
5. **API Info** - http://localhost:8000/api/info/

---

## 🎯 Next Steps After Starting

1. **Load Data:**
   ```powershell
   python data/load_data.py
   ```

2. **Generate Embeddings** (requires matcher service):
   ```powershell
   python data/generate_embeddings.py
   ```

3. **Test API Endpoints:**
   - Register user: `POST /api/auth/register/`
   - Login: `POST /api/auth/login/`
   - View jobs: `GET /api/jobs/jobs/`
   - Upload resume: `POST /api/candidates/resumes/`

---

## 📝 Environment Variables (if needed)

Create a `.env` file in the root directory:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=equihire
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
SECRET_KEY=your-secret-key-here
DEBUG=True
```

---

## 🆘 Need Help?

Check the detailed guide: `RUN_INSTRUCTIONS.md`

