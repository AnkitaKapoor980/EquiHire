@echo off
echo Setting up EquiHire development environment...

:: Navigate to Django project directory
cd /d %~dp0backend\django_app

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Run the setup script
python setup_dev.py

:: Start the Django development server
echo.
echo Starting Django development server...
start cmd /k "cd /d %~dp0backend\django_app && venv\Scripts\activate && python manage.py runserver"

:: Open the application in browser
start http://localhost:8000

:: Open MinIO console
start http://localhost:9001

echo.
echo Development environment is ready!
pause
