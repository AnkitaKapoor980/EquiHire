# EquiHire AI - Service Status

## ✅ Completed Setup

### 1. Database & Infrastructure
- ✅ PostgreSQL with pgvector extension (Docker) - **RUNNING**
- ✅ MinIO object storage (Docker) - **RUNNING**
- ✅ Database initialized and migrated
- ✅ Django middleware configuration fixed (added allauth middleware)

### 2. Django Application
- ✅ Django server - **RUNNING on http://localhost:8000**
- ✅ Health endpoint accessible: http://localhost:8000/api/health/
- ✅ All migrations applied successfully
- ✅ Test framework configured (pytest.ini created)

### 3. Flask Microservices
- ⚠️ **Flask services launched but need dependencies**
- ✅ Parser Service window opened (port 5001)
- ✅ Matcher Service window opened (port 5002)
- ✅ Fairness Service window opened (port 5003)
- ✅ Explainability Service window opened (port 5004)

## ⚠️ Current Issues

### Flask Services Not Starting
The Flask services require additional Python dependencies that are being installed:
- python-docx (for DOCX parsing)
- PyMuPDF (already installed)
- sentence-transformers (for embeddings)
- scikit-learn (already installed)
- shap (for explainability)
- aif360 (for fairness auditing)
- fairlearn (for fairness)

**Solution**: Dependencies are currently installing. Once complete, restart the Flask services or check the PowerShell windows that opened for any remaining errors.

## 🔧 To Complete Setup

### Option 1: Wait for Dependencies & Restart
1. Wait for pip installation to complete
2. Restart Flask services:
   ```powershell
   powershell -ExecutionPolicy Bypass -File start_services.ps1
   ```

### Option 2: Install All Dependencies First
```powershell
# Install Flask service requirements
cd backend\flask_services\parser_service
pip install -r requirements.txt

cd ..\matcher_service
pip install -r requirements.txt

cd ..\fairness_service
pip install -r requirements.txt

cd ..\explainability_service
pip install -r requirements.txt

# Then restart services
cd ..\..\..
powershell -ExecutionPolicy Bypass -File start_services.ps1
```

### Option 3: Use Docker Compose (All Services)
```powershell
docker-compose up -d
```
This will start all services including Django and Flask services in containers.

## 📊 Service URLs

Once all services are running:
- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Parser Service**: http://localhost:5001
- **Matcher Service**: http://localhost:5002
- **Fairness Service**: http://localhost:5003
- **Explainability Service**: http://localhost:5004
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 🧪 Testing

Run tests after all services are up:
```powershell
cd "F:\Capstone 2\equihire-ai"
$env:POSTGRES_HOST="localhost"
$env:DJANGO_SETTINGS_MODULE="equihire.settings"
python -m pytest tests/ -v
```

## ✅ What's Working

1. ✅ Docker infrastructure (PostgreSQL, MinIO)
2. ✅ Database schema created and migrated
3. ✅ Django application running and accessible
4. ✅ Django health endpoint responding
5. ✅ Test framework configured
6. ✅ All services startup scripts created

## 📝 Next Steps

1. **Check PowerShell windows** that opened for Flask services - look for import errors
2. **Install missing dependencies** if services show import errors
3. **Restart services** once dependencies are installed
4. **Run test suite** to verify all services are working
5. **Load sample data** (optional):
   ```powershell
   python data/load_data.py
   ```

## 🆘 Troubleshooting

If Flask services still don't start:
1. Check the separate PowerShell windows for error messages
2. Verify Python packages: `pip list | Select-String "docx|transformers|shap|aif360"`
3. Check ports aren't in use: `netstat -ano | findstr "5001 5002 5003 5004"`
4. Review service logs in the PowerShell windows

