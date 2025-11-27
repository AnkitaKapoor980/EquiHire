pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}\\.venv"
        COMPOSE_PROJECT_NAME = "equihire-${BUILD_NUMBER}"
        DOCKER_BUILDKIT = "1"
        COMPOSE_DOCKER_CLI_BUILD = "1"
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
                    setlocal enabledelayedexpansion
                    
                    echo [INFO] Cleaning up any existing containers and networks...
                    
                    :: Stop and remove containers by project name
                    docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "No containers with project name %COMPOSE_PROJECT_NAME%"
                    
                    :: Also try with default project name (equihire)
                    docker compose -p equihire down -v --remove-orphans 2>nul || echo "No containers with default project name"
                    
                    :: Remove containers by name pattern (equihire_*)
                    echo [INFO] Removing containers with name pattern equihire_*...
                    for /f "tokens=*" %%i in ('docker ps -aq --filter "name=equihire_"') do (
                        echo [INFO] Removing container: %%i
                        docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                    )
                    
                    :: Remove stopped containers with equihire in name
                    for /f "tokens=*" %%i in ('docker ps -aq --filter "name=equihire"') do (
                        echo [INFO] Removing stopped container: %%i
                        docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                    )
                    
                    echo [INFO] Checking for running containers using ports 9000 and 5432...
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=9000"') do (
                        echo [INFO] Stopping container using port 9000: %%i
                        docker stop %%i 2>nul || echo "Failed to stop container: %%i"
                        docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                    )
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5432"') do (
                        echo [INFO] Stopping container using port 5432: %%i
                        docker stop %%i 2>nul || echo "Failed to stop container: %%i"
                        docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                    )
                    
                    :: Add a small delay to ensure ports are released
                    echo [INFO] Waiting for ports to be released...
                    ping -n 3 127.0.0.1 >nul
                    
                    echo [INFO] Removing any dangling networks...
                    for /f "tokens=*" %%i in ('docker network ls -q --filter "name=equihire"') do (
                        echo [INFO] Removing network: %%i
                        docker network rm %%i 2>nul || echo "Failed to remove network: %%i"
                    )
                    
                    :: Clean up old test results
                    if exist "test-results" rmdir /s /q test-results
                    mkdir test-results
                    
                    echo [INFO] Cleanup complete
                    endlocal
                    '''
                }
            }
        }

        stage('Checkout') {
            steps {
                script {
                    retry(3) {
                        cleanWs()
                        checkout scm
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    bat '''
                    @echo off
                    setlocal enabledelayedexpansion
                    
                    echo [INFO] Building Docker images with BuildKit cache...
                    echo [INFO] Docker will automatically use cached layers if available...
                    
                    :: Enable BuildKit for better caching
                    set DOCKER_BUILDKIT=1
                    set COMPOSE_DOCKER_CLI_BUILD=1
                    
                    echo [INFO] Building images (will use cache if available)...
                    echo [INFO] This will be fast if layers are cached, slow only on first build...
                    
                    :: Build with project prefix - Docker will use cache automatically
                    docker compose -p %COMPOSE_PROJECT_NAME% --progress plain build --parallel
                    
                    if !ERRORLEVEL! NEQ 0 (
                        echo [WARNING] Parallel build failed, trying sequential build...
                        docker compose -p %COMPOSE_PROJECT_NAME% --progress plain build
                    )
                    
                    if !ERRORLEVEL! NEQ 0 (
                        echo [ERROR] Failed to build Docker images
                        exit /b 1
                    )
                    
                    echo [INFO] Build completed - images are cached for next build
                    endlocal
                    '''
                }
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                script {
                    try {
                        // Cleanup before starting services
                        bat '''
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        echo [INFO] Final cleanup before starting services...
                        docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "No existing containers"
                        docker compose -p equihire down -v --remove-orphans 2>nul || echo "No default containers"
                        
                        :: Remove any containers using required ports
                        for /f "tokens=*" %%i in ('docker ps -q --filter "publish=9000"') do docker rm -f %%i 2>nul
                        for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5432"') do docker rm -f %%i 2>nul
                        
                        endlocal
                        '''
                        
                        // Start services
                        bat '''
                        @echo off
                        setlocal enabledelayedexpansion
                        
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
                        setlocal enabledelayedexpansion
                        
                        echo [INFO] Running tests in container...
                        echo [INFO] Installing test dependencies...
                        docker compose -p %COMPOSE_PROJECT_NAME% run --rm -v "%CD%:/app" -w /app django_app /opt/venv/bin/pip install pytest pytest-django pytest-cov
                        
                        if !ERRORLEVEL! NEQ 0 (
                            echo [ERROR] Failed to install test dependencies
                            exit /b 1
                        )
                        
                        echo [INFO] Running pytest in container from /app directory...
                        docker compose -p %COMPOSE_PROJECT_NAME% run --rm -v "%CD%:/app" -v "%CD%/test-results:/app/test-results" -w /app -e DJANGO_SETTINGS_MODULE=equihire.settings django_app /opt/venv/bin/python -m pytest tests/ --junitxml=/app/test-results/junit.xml --cov=backend/django_app --cov-report=xml:/app/test-results/coverage.xml --cov-report=html:/app/test-results/htmlcov -v
                        
                        set TEST_EXIT_CODE=!ERRORLEVEL!
                        
                        echo [INFO] Test command exited with code !TEST_EXIT_CODE!
                        
                        if not exist "test-results\\junit.xml" (
                            echo [ERROR] No test results found at test-results/junit.xml
                            if exist "test-results" (
                                echo [INFO] Contents of test-results directory:
                                dir /b test-results
                            ) else (
                                echo [INFO] test-results directory does not exist
                            )
                            if !TEST_EXIT_CODE! EQU 0 (
                                exit /b 1
                            )
                        )
                        
                        echo [INFO] Test execution completed
                        if !TEST_EXIT_CODE! NEQ 0 (
                            exit /b !TEST_EXIT_CODE!
                        )
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
                        setlocal enabledelayedexpansion
                        
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
                    setlocal enabledelayedexpansion
                    
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
                if (fileExists('test-results/junit.xml')) {
                    junit 'test-results/junit.xml'
                } else {
                    echo "No test results found, skipping junit report"
                }
                
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
                docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "Failed to stop containers with project name"
                docker compose -p equihire down -v --remove-orphans 2>nul || echo "Failed to stop default containers"
                
                echo [INFO] Removing any remaining containers...
                for /f "tokens=*" %%i in ('docker ps -aq --filter "name=equihire"') do (
                    echo [INFO] Removing container: %%i
                    docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                )
                
                :: Remove containers using required ports
                for /f "tokens=*" %%i in ('docker ps -q --filter "publish=9000"') do (
                    echo [INFO] Removing container using port 9000: %%i
                    docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
                )
                for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5432"') do (
                    echo [INFO] Removing container using port 5432: %%i
                    docker rm -f %%i 2>nul || echo "Failed to remove container: %%i"
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
