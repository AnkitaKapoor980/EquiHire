pipeline {
    agent any

environment {
    VENV = "${WORKSPACE}\\.venv"
}

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker compose build'
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                bat '''
docker compose run --rm django_app bash -c "python manage.py migrate --noinput && python manage.py test"
'''
            }
        }

        stage('Start Integration Stack') {
            steps {
                bat '''
docker compose up -d
SETLOCAL EnableDelayedExpansion
SET /A COUNT=0
:wait_loop
IF !COUNT! GEQ 30 (
    echo Django API failed to start in time.
    EXIT /B 1
)
curl --silent --fail http://localhost:8000/api/health/ >NUL 2>&1
IF !ERRORLEVEL! EQU 0 (
    echo Django API is healthy.
    EXIT /B 0
)
SET /A COUNT+=1
timeout /t 5 >NUL
GOTO wait_loop
'''
            }
        }

        stage('Selenium Tests') {
            steps {
                bat """
python -m venv "%VENV%"
call "%VENV%\\Scripts\\activate"
python -m pip install --upgrade pip
pip install -r tests\\selenium\\requirements.txt
pytest tests\\selenium --base-url=http://localhost:8000 --maxfail=1 --disable-warnings
"""
            }
        }
    }

    post {
        always {
            bat '''
docker compose down -v
IF EXIST "%VENV%" rmdir /s /q "%VENV%"
'''
        }
    }
}

