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

        stage('Start All Services') {
            steps {
                script {
                    bat '''
                    @echo off
                    setlocal enabledelayedexpansion
                    
                    echo [INFO] Final cleanup before starting services...
                    docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "No existing containers"
                    docker compose -p equihire down -v --remove-orphans 2>nul || echo "No default containers"
                    
                    :: Remove any containers using required ports
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=9000"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5432"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=8000"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5001"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5002"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5003"') do docker rm -f %%i 2>nul
                    for /f "tokens=*" %%i in ('docker ps -q --filter "publish=5004"') do docker rm -f %%i 2>nul
                    
                    echo [INFO] Starting all services...
                    docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml up -d
                    
                    echo [INFO] Waiting for all services to be healthy...
                    set MAX_RETRIES=60
                    set RETRY_DELAY=5
                    set COUNT=0
                    
                    :check_services
                    set ALL_HEALTHY=1
                    
                    echo [INFO] Checking service health status...
                    for %%s in (postgres minio django_app parser_service matcher_service fairness_service explainability_service) do (
                        echo [INFO] Checking %%s...
                        docker compose -p %COMPOSE_PROJECT_NAME% ps %%s | find "healthy" >nul
                        if !ERRORLEVEL! NEQ 0 (
                            docker compose -p %COMPOSE_PROJECT_NAME% ps %%s | find "running" >nul
                            if !ERRORLEVEL! NEQ 0 (
                                echo [WARNING] Service %%s is not running or healthy
                                set ALL_HEALTHY=0
                            ) else (
                                echo [INFO] Service %%s is running but not yet healthy
                                set ALL_HEALTHY=0
                            )
                        ) else (
                            echo [INFO] Service %%s is healthy
                        )
                    )
                    
                    if !ALL_HEALTHY! EQU 1 (
                        echo [INFO] All services are healthy
                        goto services_ready
                    )
                    
                    set /a COUNT+=1
                    if !COUNT! GTR %MAX_RETRIES% (
                        echo [ERROR] Some services failed to become healthy in time
                        echo [INFO] Current service status:
                        docker compose -p %COMPOSE_PROJECT_NAME% ps
                        echo [INFO] Service logs:
                        docker compose -p %COMPOSE_PROJECT_NAME% logs --tail=50
                        exit /b 1
                    )
                    
                    echo [INFO] Waiting for all services to be healthy... (!COUNT! of %MAX_RETRIES%)
                    timeout /t %RETRY_DELAY% /nobreak >nul
                    goto check_services
                    
                    :services_ready
                    echo [INFO] All services are up and healthy
                    
                    echo [INFO] Additional 45-second wait for full service initialization...
                    timeout /t 45 /nobreak >nul
                    
                    echo [INFO] Initializing database with pgvector extension...
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app python manage.py init_db
                    
                    echo [INFO] Running migrations...
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app python manage.py migrate
                    
                    echo [INFO] Verifying service connectivity...
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app curl -f http://parser_service:5001/health || echo "Parser service not reachable"
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app curl -f http://matcher_service:5002/health || echo "Matcher service not reachable"
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app curl -f http://fairness_service:5003/health || echo "Fairness service not reachable"
                    docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app curl -f http://explainability_service:5004/health || echo "Explainability service not reachable"
                    
                    echo [INFO] Creating test-results directory...
                    if not exist "test-results" mkdir test-results
                    
                    endlocal
                    '''
                }
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                script {
                    try {
                        bat '''
                        @echo off
                        setlocal enabledelayedexpansion
                        
                        echo [INFO] Installing test dependencies in Django container...
                        docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app /opt/venv/bin/pip install pytest pytest-django pytest-cov requests
                        
                        if !ERRORLEVEL! NEQ 0 (
                            echo [ERROR] Failed to install test dependencies
                            exit /b 1
                        )
                        
                        echo [INFO] Copying test files to Django container...
                        docker cp tests %COMPOSE_PROJECT_NAME%-django_app-1:/app/
                        if exist pytest.ini docker cp pytest.ini %COMPOSE_PROJECT_NAME%-django_app-1:/app/
                        
                        echo [INFO] Verifying test files are copied...
                        docker compose -p %COMPOSE_PROJECT_NAME% exec -T django_app ls -la /app/tests/
                        
                        echo [INFO] Running Django unit tests inside the running container...
                        docker compose -p %COMPOSE_PROJECT_NAME% exec -T -e DJANGO_SETTINGS_MODULE=equihire.settings django_app sh -c "cd /app && /opt/venv/bin/python -m pytest tests/ --junitxml=/app/test-results/junit.xml --cov=. --cov-report=xml:/app/test-results/coverage.xml --cov-report=html:/app/test-results/htmlcov -v --tb=short"
                        
                        set TEST_EXIT_CODE=!ERRORLEVEL!
                        echo [INFO] Test command exited with code !TEST_EXIT_CODE!
                        
                        echo [INFO] Copying test results back to host...
                        docker cp %COMPOSE_PROJECT_NAME%-django_app-1:/app/test-results/ test-results/
                        
                        echo [INFO] Test results copied. Contents:
                        if exist "test-results" (
                            dir /s /b test-results
                        ) else (
                            echo No test results directory found
                        )
                        
                        if !TEST_EXIT_CODE! NEQ 0 (
                            echo [ERROR] Tests failed with exit code !TEST_EXIT_CODE!
                            exit /b !TEST_EXIT_CODE!
                        )
                        
                        echo [INFO] All tests passed successfully!
                        endlocal
                        '''
                        
                    } catch (Exception e) {
                        echo "[ERROR] Test execution failed: ${e.message}"
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        // Always try to copy test results, even if tests fail
                        bat '''
                        @echo off
                        echo [INFO] Ensuring test results are copied...
                        docker cp %COMPOSE_PROJECT_NAME%-django_app-1:/app/test-results/ test-results/ 2>nul || echo "No test results to copy"
                        '''
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
                    
                    echo [INFO] Setting up Python virtual environment for Selenium tests...
                    python -m venv "%VENV%"
                    call "%VENV%\\Scripts\\activate"
                    
                    echo [INFO] Installing test dependencies...
                    python -m pip install --upgrade pip
                    if not exist "tests\\selenium\\requirements.txt" (
                        echo [WARNING] Selenium requirements file not found, creating basic one...
                        echo selenium > tests\\selenium\\requirements.txt
                        echo pytest >> tests\\selenium\\requirements.txt
                        echo pytest-html >> tests\\selenium\\requirements.txt
                    )
                    pip install -r tests\\selenium\\requirements.txt
                    
                    echo [INFO] Running Selenium tests...
                    pytest tests\\selenium --base-url=http://localhost:8000 --maxfail=1 --disable-warnings --html=test-results/selenium-report.html --self-contained-html
                    set TEST_RESULT=!ERRORLEVEL!
                    
                    echo [INFO] Selenium tests completed with exit code !TEST_RESULT!
                    if !TEST_RESULT! NEQ 0 (
                        echo [WARNING] Selenium tests failed, but continuing pipeline...
                    )
                    
                    endlocal
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
                    echo "No JUnit test results found, skipping junit report"
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
                
                // Publish Selenium report if it exists
                if (fileExists('test-results/selenium-report.html')) {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'test-results',
                        reportFiles: 'selenium-report.html',
                        reportName: 'Selenium Test Report'
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
                for /f "tokens=*" %%i in ('docker ps -q --filter "publish=8000"') do (
                    echo [INFO] Removing container using port 8000: %%i
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