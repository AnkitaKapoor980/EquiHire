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
        }

        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                // Build with cache from previous builds if available
                bat '''
                @echo off
                setlocal enabledelayedexpansion
                
                echo [INFO] Building Docker images with cache...
                docker compose -p %COMPOSE_PROJECT_NAME% build --build-arg BUILDKIT_INLINE_CACHE=1
                
                if !ERRORLEVEL! NEQ 0 (
                    echo [WARNING] Build with cache failed, retrying without cache...
                    docker compose -p %COMPOSE_PROJECT_NAME% build --no-cache
                )
                
                if !ERRORLEVEL! NEQ 0 (
                    echo [ERROR] Failed to build Docker images
                    exit /b 1
                )
                
                endlocal
                '''
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                bat '''
                @echo off
                setlocal enabledelayedexpansion
                
                echo [INFO] Starting database and running migrations...
                
                :: Start PostgreSQL with health check
                docker compose -p %COMPOSE_PROJECT_NAME% up -d --wait postgres
                
                :: Wait for PostgreSQL to be ready with retries
                set MAX_RETRIES=30
                set RETRY_DELAY=5
                set COUNT=0
                
                :check_postgres
                docker compose -p %COMPOSE_PROJECT_NAME% exec -T postgres pg_isready -U admin -h localhost -p 5432 -d equihire
                if !ERRORLEVEL! EQU 0 (
                    echo [INFO] PostgreSQL is ready
                    goto db_ready
                )
                
                set /a COUNT+=1
                echo [INFO] Waiting for PostgreSQL to be ready... (!COUNT! of %MAX_RETRIES%)
                
                if !COUNT! GEQ %MAX_RETRIES% (
                    echo [ERROR] PostgreSQL failed to start in time
                    docker compose -p %COMPOSE_PROJECT_NAME% logs postgres
                    exit /b 1
                )
                
                timeout /t %RETRY_DELAY% >nul
                goto check_postgres
                
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
                @echo off
                setlocal enabledelayedexpansion
                
                echo [INFO] Starting all services...
                docker compose -p %COMPOSE_PROJECT_NAME% up -d --wait
                
                echo [INFO] Waiting for services to be healthy...
                set MAX_RETRIES=30
                set RETRY_DELAY=5
                set COUNT=0
                
                :health_check_loop
                set ALL_HEALTHY=1
                
                :: Check Django health
                curl --max-time 5 --silent --fail http://localhost:8000/api/health/ >nul 2>&1
                if !ERRORLEVEL! NEQ 0 (
                    echo [INFO] Django is not ready yet
                    set ALL_HEALTHY=0
                )
                
                :: Check MinIO health
                curl --max-time 5 --silent --fail http://localhost:9000/minio/health/live >nul 2>&1
                if !ERRORLEVEL! NEQ 0 (
                    echo [INFO] MinIO is not ready yet
                    set ALL_HEALTHY=0
                )
                
                if !ALL_HEALTHY! EQU 1 (
                    echo [INFO] All services are healthy
                    exit /b 0
                )
                
                set /a COUNT+=1
                echo [INFO] Waiting for services to be ready... (!COUNT! of %MAX_RETRIES%)
                
                if !COUNT! GEQ %MAX_RETRIES% (
                    echo [ERROR] Services failed to start in time
                    echo [ERROR] Current status:
                    docker compose -p %COMPOSE_PROJECT_NAME% ps
                    echo [ERROR] Logs:
                    docker compose -p %COMPOSE_PROJECT_NAME% logs --tail=50
                    exit /b 1
                )
                
                timeout /t %RETRY_DELAY% >nul
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
                for /f "tokens=*" %%i in ('docker ps -aq --filter name=^/%COMPOSE_PROJECT_NAME%_') do (
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
