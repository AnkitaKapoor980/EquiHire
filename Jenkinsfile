pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}\\.venv"
        COMPOSE_PROJECT_NAME = "equihire-${BUILD_NUMBER}"
        PYTHONUNBUFFERED = "1"
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
                    bat '''
                    @echo off
                    setlocal enabledelayedprogress
                    
                    echo [INFO] Cleaning up any existing containers and networks...
                    docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans || echo "No existing containers to remove"
                    
                    echo [INFO] Removing any dangling containers...
                    for /f "tokens=*" %%i in ('docker ps -aq --filter "name=^%COMPOSE_PROJECT_NAME%_"') do (
                        echo [INFO] Removing container: %%i
                        docker rm -f %%i || echo "Failed to remove container: %%i"
                    )
                    
                    echo [INFO] Checking for running containers using ports 9000 and 5432...
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=9000"') do (
                        echo [INFO] Stopping container using port 9000: %%i
                        docker stop %%i || echo "Failed to stop container: %%i"
                    )
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5432"') do (
                        echo [INFO] Stopping container using port 5432: %%i
                        docker stop %%i || echo "Failed to stop container: %%i"
                    )
                    
                    :: Add a small delay to ensure ports are released
                    ping -n 3 127.0.0.1 >nul
                    
                    echo [INFO] Removing any dangling networks...
                    for /f "tokens=*" %%i in ('docker network ls -q --filter "name=^%COMPOSE_PROJECT_NAME%_"') do (
                        echo [INFO] Removing network: %%i
                        docker network rm %%i || echo "Failed to remove network: %%i"
                    )
                    
                    :: Clean up old test results
                    if exist "test-results" rmdir /s /q test-results
                    mkdir test-results
                    
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
                script {
                    bat '''
                    @echo off
                    setlocal enabledelayedprogress
                    
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
        }

        stage('Run Django Unit Tests') {
            steps {
                script {
                    try {
                        // Start services
                        bat '''
                        @echo off
                        setlocal enabledelayedprogress
                        
                        echo [INFO] Starting database and running migrations...
                        docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml up -d --wait postgres minio
                        
                        echo [INFO] Waiting for PostgreSQL to be ready...
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
                        if !COUNT! GTR %MAX_RETRIES% (
                            echo [ERROR] PostgreSQL failed to start in time
                            docker compose -p %COMPOSE_PROJECT_NAME% logs postgres
                            exit /b 1
                        )
                        
                        echo [INFO] Waiting for PostgreSQL to be ready... (!COUNT! of %MAX_RETRIES%)
                        timeout /t %RETRY_DELAY% /nobreak >nul
                        goto check_postgres
                        
                        :db_ready
                        echo [INFO] Initializing database with pgvector extension...
                        docker compose -p %COMPOSE_PROJECT_NAME% run --rm django_app python manage.py init_db
                        
                        echo [INFO] Running migrations...
                        docker compose -p %COMPOSE_PROJECT_NAME% run --rm django_app python manage.py migrate
                        
                        echo [INFO] Creating test-results directory...
                        if not exist "test-results" mkdir test-results
                        '''
                        
                        // Run tests
                        bat '''
                        @echo off
                        setlocal enabledelayedprogress
                        
                        echo [INFO] Running tests in container...
                        docker compose -p %COMPOSE_PROJECT_NAME% run --rm ^
                            -v "%CD%:/app" ^
                            -v "%CD%/test-results:/app/test-results" ^
                            -w /app/backend/django_app ^
                            django_app ^
                            sh -c "pip install pytest pytest-django pytest-cov && ^
                                  python -m pytest /app/backend/django_app/tests ^
                                    --junitxml=/app/test-results/junit.xml ^
                                    --cov=. ^
                                    --cov-report=xml:/app/test-results/coverage.xml ^
                                    --cov-report=html:/app/test-results/htmlcov"
                        
                        if not exist "test-results\\junit.xml" (
                            echo [ERROR] No test results found at test-results/junit.xml
                            dir /s /b test-results
                            exit /b 1
                        )
                        
                        echo [INFO] Test execution completed successfully
                        '''
                        
                        // Publish test results
                        junit 'test-results/junit.xml'
                        
                    } catch (Exception e) {
                        echo "[ERROR] Test stage failed: ${e.message}"
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        // Cleanup
                        bat '''
                        @echo off
                        echo [INFO] Cleaning up test containers...
                        docker compose -p %COMPOSE_PROJECT_NAME% down -v || echo "Failed to stop test containers"
                        '''
                    }
                }
            }
        }

        stage('Start Integration Stack') {
            steps {
                script {
                    try {
                        bat '''
                        @echo off
                        setlocal enabledelayedprogress
                        
                        echo [INFO] Starting integration stack...
                        docker compose -p %COMPOSE_PROJECT_NAME% up -d
                        
                        echo [INFO] Waiting for services to be ready...
                        timeout /t 30 /nobreak >nul
                        
                        echo [INFO] Current running containers:
                        docker ps --format "table {{.Names}}\t{{.Status}}"
                        
                        endlocal
                        '''
                    } catch (Exception e) {
                        echo "[ERROR] Failed to start integration stack: ${e.message}"
                        currentBuild.result = 'FAILURE'
                        throw e
                    }
                }
            }
        }

        stage('Selenium Tests') {
            steps {
                script {
                    bat '''
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
                    '''
                }
            }
        }
    }

    
    post {
        always {
            script {
                // Publish test results if they exist
                junit 'test-results/junit.xml'
                
                // Publish HTML coverage report if it exists
                if (fileExists('test-results/coverage.xml')) {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'test-results/htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
                
                // Cleanup containers
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
                
                // Clean workspace
                cleanWs()
            }
        }
    }
}
