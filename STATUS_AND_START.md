# ✅ Codebase Status & How to Start

## 📊 Current Status

### ✅ Codebase: READY
- ✅ All code files are in place
- ✅ Database models defined
- ✅ API endpoints implemented
- ✅ Flask microservices ready
- ✅ Datasets prepared in `data/raw/`

### ⚠️ Setup Required
- ❌ Python dependencies not installed yet
- ❓ Database connection needs to be configured
- ❓ Migrations need to be run

---

## 🚀 How to Start (Step-by-Step)

### Step 1: Install Python Dependencies

```powershell
pip install -r backend/requirements.txt
```

**This will install:**
- Django 4.2.7
- PostgreSQL drivers
- ML libraries (sentence-transformers, spaCy, etc.)
- All required packages

**Time:** ~5-10 minutes depending on your internet speed

---

### Step 2: Setup Database

#### Option A: Using Docker (Easiest)

1. **Start Docker Desktop** (if not running)

2. **Start PostgreSQL and MinIO:**
   ```powershell
   docker-compose up -d postgres minio
   ```

3. **Wait 10-15 seconds** for services to start

#### Option B: Using Local PostgreSQL

1. **Install PostgreSQL 15+** with pgvector extension

2. **Create database:**
   ```sql
   CREATE DATABASE equihire;
   CREATE EXTENSION vector;
   ```

3. **Set environment variable:**
   ```powershell
   $env:POSTGRES_HOST="localhost"
   ```

---

### Step 3: Initialize Database & Run Migrations

```powershell
cd backend/django_app
python manage.py init_db
python manage.py migrate
python manage.py createsuperuser
```

**Follow prompts to create admin user.**

---

### Step 4: Start the Server

```powershell
python manage.py runserver
```

**You should see:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 5: Verify It's Working

#### Test 1: Health Check
Open browser: **http://localhost:8000/api/health/**

**Expected:** 
```json
{"status": "healthy", "service": "equihire-api"}
```

#### Test 2: API Info
Open browser: **http://localhost:8000/api/info/**

**Expected:** API information with endpoints list

#### Test 3: Admin Panel
Open browser: **http://localhost:8000/admin/**

**Expected:** Django admin login page

---

### Step 6: Load Your Data (Optional)

```powershell
# From project root
cd ../..
python data/load_data.py
```

**This loads:**
- ✅ 2,484 resumes
- ✅ 1,068 job postings

---

## 🎯 Quick Start Commands (Copy & Paste)

```powershell
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Start database (if using Docker)
docker-compose up -d postgres minio
Start-Sleep -Seconds 10

# 3. Setup database
cd backend/django_app
python manage.py init_db
python manage.py migrate
python manage.py createsuperuser

# 4. Start server
python manage.py runserver
```

---

## ✅ Verification Checklist

Once started, verify:

- [ ] Server starts without errors
- [ ] http://localhost:8000/api/health/ returns `{"status": "healthy"}`
- [ ] http://localhost:8000/api/info/ shows API information
- [ ] http://localhost:8000/admin/ shows login page
- [ ] Can login to admin panel with superuser
- [ ] Data loading script runs successfully (if you run it)

---

## 🔍 Troubleshooting

### "ModuleNotFoundError: No module named 'django'"
**Solution:** Install dependencies
```powershell
pip install -r backend/requirements.txt
```

### "could not connect to server"
**Solution:** 
- Check if PostgreSQL is running
- For Docker: Make sure `docker-compose up -d postgres` ran successfully
- For local: Check PostgreSQL service is running

### "extension 'vector' does not exist"
**Solution:** Run init_db command
```powershell
python manage.py init_db
```

### Port 8000 already in use
**Solution:** Use different port
```powershell
python manage.py runserver 8001
```

---

## 📝 What You Can Do After Starting

1. **Access Admin Panel** - Manage users, jobs, candidates
2. **Use REST API** - Test endpoints with Postman or curl
3. **Load Data** - Import your 2,484 resumes and 1,068 jobs
4. **Generate Embeddings** - Create vector embeddings for matching
5. **Test Matching** - Match candidates to jobs

---

## 🎉 Success Indicators

You'll know it's working when:

✅ Server starts: `Starting development server at http://127.0.0.1:8000/`
✅ Health check returns: `{"status": "healthy"}`
✅ Admin panel loads: Login page appears
✅ No errors in console

---

## 📚 Additional Resources

- **Detailed Setup:** See `RUN_INSTRUCTIONS.md`
- **API Documentation:** See `docs/API.md`
- **Architecture:** See `docs/ARCHITECTURE.md`

---

## 🆘 Need Help?

1. Check error messages carefully
2. Verify PostgreSQL is running
3. Ensure all dependencies are installed
4. Check `RUN_INSTRUCTIONS.md` for detailed steps

