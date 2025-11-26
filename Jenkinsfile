pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}\\.venv"
        COMPOSE_PROJECT_NAME = "equihire-${BUILD_NUMBER}"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Cleanup') {
            steps {
                script {
                    // Clean up any existing containers and networks
                    bat '''
                    @echo off
                    setlocal enabledelayedexpansion
                    
                    echo [INFO] Cleaning up any existing containers and networks...
                    docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans || echo "No existing containers to remove"
                    
                    :: Remove any dangling containers and networks
                    for /f "tokens=*" %%i in ('docker ps -aq -f name=equihire_*') do (
                        echo [INFO] Removing container: %%i
                        docker rm -f %%i || echo "Failed to remove container: %%i"
                    )
                    
                    for /f "tokens=*" %%i in ('docker network ls -q -f name=*equihire*') do (
                        echo [INFO] Removing network: %%i
                        docker network rm %%i || echo "Failed to remove network: %%i"
                    )
                    
                    endlocal
                    '''
            }
        }

        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker compose -p %COMPOSE_PROJECT_NAME% build --no-cache'
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                bat '''
                setlocal enabledelayedexpansion
                
                echo [INFO] Starting database and running migrations...
                docker compose -p %COMPOSE_PROJECT_NAME% up -d postgres
                
                :: Wait for PostgreSQL to be ready
                set COUNT=0
                :db_wait_loop
                docker compose -p %COMPOSE_PROJECT_NAME% exec -T postgres pg_isready -U admin
                if !ERRORLEVEL! EQU 0 (
                    echo [INFO] PostgreSQL is ready
                    goto db_ready
                ) else (
                    set /a COUNT+=1
                    if !COUNT! GEQ 30 (
                        echo [ERROR] PostgreSQL failed to start in time
                        exit /b 1
                    )
                    echo [INFO] Waiting for PostgreSQL to be ready...
                    timeout /t 5 >nul
                    goto db_wait_loop
                )
                
                :db_ready
                
                echo [INFO] Running Django tests...
                docker compose -p %COMPOSE_PROJECT_NAME% run --rm django_app bash -c \
                    "python manage.py migrate --noinput && python manage.py test --noinput"
                
                endlocal
                '''
            }
        }

        stage('Start Integration Stack') {
            steps {
                bat '''
                setlocal enabledelayedexpansion
                
                echo [INFO] Starting all services...
                docker compose -p %COMPOSE_PROJECT_NAME% up -d
                
                echo [INFO] Waiting for services to be healthy...
                set COUNT=0
                :health_check_loop
                
                :: Check Django health
                curl --silent --fail http://localhost:8000/api/health/ >nul 2>&1
                set DJANGO_UP=!ERRORLEVEL!
                
                :: Check MinIO health
                curl --silent --fail http://localhost:9000/minio/health/live >nul 2>&1
                set MINIO_UP=!ERRORLEVEL!
                
                if !DJANGO_UP! EQU 0 if !MINIO_UP! EQU 0 (
                    echo [INFO] All services are healthy
                    exit /b 0
                )
                
                set /a COUNT+=1
                if !COUNT! GEQ 30 (
                    echo [ERROR] Services failed to start in time
                    docker compose -p %COMPOSE_PROJECT_NAME% ps
                    docker compose -p %COMPOSE_PROJECT_NAME% logs --tail=50
                    exit /b 1
                )
                
                echo [INFO] Waiting for services to be ready...
                timeout /t 5 >nul
                goto health_check_loop
                
                endlocal
                '''
            }
        }

        stage('Selenium Tests') {
            steps {
                bat """
                @echo off
                setlocal
                
                echo [INFO] Setting up Python virtual environment...
                python -m venv "%VENV%"
                call "%VENV%\\Scripts\\activate"
                
                echo [INFO] Installing test dependencies...
                python -m pip install --upgrade pip
                if not exist "tests\\selenium\\requirements.txt" (
                    echo [ERROR] Selenium requirements file not found
                    exit /b 1
                )
                pip install -r tests\\selenium\\requirements.txt
                
                echo [INFO] Running Selenium tests...
                pytest tests\\selenium --base-url=http://localhost:8000 --maxfail=1 --disable-warnings
                set TEST_RESULT=!ERRORLEVEL!
                
                echo [INFO] Selenium tests completed with exit code !TEST_RESULT!
                exit /b !TEST_RESULT!
                """
            }
        }
    }

    post {
        always {
            script {
                echo 'Cleaning up...'
                bat '''
                @echo off
                setlocal enabledelayedexpansion
                
                echo [INFO] Stopping and removing containers...
                docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans || echo "Failed to stop containers"
                
                echo [INFO] Removing any remaining containers...
                for /f "tokens=*" %%i in ('docker ps -aq -f name=%COMPOSE_PROJECT_NAME%_*') do (
                    echo [INFO] Removing container: %%i
                    docker rm -f %%i || echo "Failed to remove container: %%i"
                )
                
                echo [INFO] Removing virtual environment...
                if exist "%VENV%" rmdir /s /q "%VENV%"
                
                echo [INFO] Cleanup complete
                endlocal
                '''
                
                // Archive test results if they exist
                junit '**/test-results/*.xml'
                
                // Clean workspace
                cleanWs()
            }
        }
    }
}
