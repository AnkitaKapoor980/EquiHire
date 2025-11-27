pipeline {
    agent any

    environment {
        // Use CI-specific project name to avoid conflicts with development
        COMPOSE_PROJECT_NAME = "equihire-ci-${BUILD_NUMBER}"
        DOCKER_BUILDKIT = "1"
        COMPOSE_DOCKER_CLI_BUILD = "1"
        PYTHONUNBUFFERED = "1"
        
        // Use different ports for CI to avoid conflicts
        CI_POSTGRES_PORT = "5433"
        CI_MINIO_PORT = "9002"
        CI_DJANGO_PORT = "8001"
        CI_PARSER_PORT = "5011"
        CI_MATCHER_PORT = "5012"
        CI_FAIRNESS_PORT = "5013"
        CI_EXPLAINABILITY_PORT = "5014"
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "[INFO] Starting CI pipeline for build #${BUILD_NUMBER}"
                    echo "[INFO] Using isolated environment: ${COMPOSE_PROJECT_NAME}"
                    echo "[INFO] CI will use different ports to avoid conflicts with development"
                    
                    // Clean up any previous CI runs (only CI containers)
                    bat '''
                    @echo off
                    echo [INFO] Cleaning up previous CI containers only...
                    docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "No previous CI containers"
                    
                    :: Clean up any old CI containers from previous builds
                    for /f "tokens=*" %%i in ('docker ps -aq --filter "name=equihire-ci-"') do (
                        echo [INFO] Removing old CI container: %%i
                        docker rm -f %%i 2>nul || echo "Failed to remove: %%i"
                    )
                    
                    echo [INFO] CI preparation complete
                    '''
                }
            }
        }

        stage('Checkout') {
            steps {
                script {
                    retry(2) {
                        checkout scm
                        echo "[INFO] Code checked out successfully"
                    }
                }
            }
        }

        stage('Build Images') {
            steps {
                script {
                    bat '''
                    @echo off
                    echo [INFO] Building Docker images for CI...
                    echo [INFO] Using BuildKit for fast, cached builds...
                    
                    :: Build only what we need for testing
                    docker compose -p %COMPOSE_PROJECT_NAME% build --parallel django_app parser_service matcher_service fairness_service explainability_service
                    
                    if !ERRORLEVEL! NEQ 0 (
                        echo [ERROR] Failed to build images
                        exit /b 1
                    )
                    
                    echo [INFO] Images built successfully
                    '''
                }
            }
        }

        stage('Unit Tests') {
            parallel {
                stage('Django Unit Tests') {
                    steps {
                        script {
                            bat '''
                            @echo off
                            setlocal enabledelayedexpansion
                            
                            echo [INFO] Starting isolated test environment...
                            
                            :: Create CI-specific docker-compose override
                            echo services: > docker-compose.ci.yml
                            echo   postgres: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_POSTGRES_PORT%:5432" >> docker-compose.ci.yml
                            echo   minio: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_MINIO_PORT%:9000" >> docker-compose.ci.yml
                            echo       - "9003:9001" >> docker-compose.ci.yml
                            echo   django_app: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_DJANGO_PORT%:8000" >> docker-compose.ci.yml
                            echo     depends_on: >> docker-compose.ci.yml
                            echo       postgres: >> docker-compose.ci.yml
                            echo         condition: service_healthy >> docker-compose.ci.yml
                            echo       minio: >> docker-compose.ci.yml
                            echo         condition: service_healthy >> docker-compose.ci.yml
                            echo   parser_service: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_PARSER_PORT%:5001" >> docker-compose.ci.yml
                            echo   matcher_service: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_MATCHER_PORT%:5002" >> docker-compose.ci.yml
                            echo   fairness_service: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_FAIRNESS_PORT%:5003" >> docker-compose.ci.yml
                            echo   explainability_service: >> docker-compose.ci.yml
                            echo     ports: >> docker-compose.ci.yml
                            echo       - "%CI_EXPLAINABILITY_PORT%:5004" >> docker-compose.ci.yml
                            
                            echo [INFO] Starting test database and storage...
                            docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml -f docker-compose.ci.yml up -d postgres minio
                            
                            echo [INFO] Waiting for database to be ready...
                            set MAX_RETRIES=20
                            set COUNT=0
                            
                            :wait_db
                            docker compose -p %COMPOSE_PROJECT_NAME% exec -T postgres pg_isready -U admin -h localhost -p 5432 >nul 2>&1
                            if !ERRORLEVEL! EQU 0 (
                                echo [INFO] Database is ready
                                goto db_ready
                            )
                            
                            set /a COUNT+=1
                            if !COUNT! GTR %MAX_RETRIES% (
                                echo [ERROR] Database failed to start
                                exit /b 1
                            )
                            
                            echo [INFO] Waiting for database... (!COUNT!/!MAX_RETRIES!)
                            timeout /t 3 /nobreak >nul
                            goto wait_db
                            
                            :db_ready
                            echo [INFO] Installing pgvector extension...
                            docker compose -p %COMPOSE_PROJECT_NAME% exec -T postgres psql -U admin -d equihire -c "CREATE EXTENSION IF NOT EXISTS vector;" >nul 2>&1
                            
                            echo [INFO] Running Django unit tests in isolated container...
                            docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml -f docker-compose.ci.yml run --rm -v "%CD%/tests:/app/tests" -v "%CD%/test-results:/app/test-results" django_app sh -c "
                                echo 'Installing test dependencies...' &&
                                /opt/venv/bin/pip install pytest pytest-django pytest-cov requests &&
                                echo 'Creating test results directory...' &&
                                mkdir -p /app/test-results &&
                                echo 'Running Django unit tests...' &&
                                cd /app &&
                                /opt/venv/bin/python -m pytest tests/ --junitxml=/app/test-results/junit.xml --cov=. --cov-report=xml:/app/test-results/coverage.xml --cov-report=html:/app/test-results/htmlcov -v --tb=short --disable-warnings
                            "
                            
                            set TEST_RESULT=!ERRORLEVEL!
                            echo [INFO] Django tests completed with exit code: !TEST_RESULT!
                            
                            :: Copy results to host
                            if not exist "test-results" mkdir test-results
                            docker cp %COMPOSE_PROJECT_NAME%-django_app-run-1:/app/test-results/. test-results/ 2>nul || echo "No test results to copy"
                            
                            if !TEST_RESULT! NEQ 0 (
                                echo [ERROR] Django unit tests failed
                                exit /b !TEST_RESULT!
                            )
                            
                            echo [INFO] Django unit tests passed successfully
                            endlocal
                            '''
                        }
                    }
                }

                stage('Service Health Tests') {
                    steps {
                        script {
                            bat '''
                            @echo off
                            setlocal enabledelayedexpansion
                            
                            echo [INFO] Starting microservices for health testing...
                            docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml -f docker-compose.ci.yml up -d parser_service matcher_service fairness_service explainability_service
                            
                            echo [INFO] Waiting for services to start...
                            timeout /t 30 /nobreak >nul
                            
                            echo [INFO] Testing service health endpoints...
                            set ALL_HEALTHY=1
                            
                            for %%s in (parser:5011 matcher:5012 fairness:5013 explainability:5014) do (
                                for /f "tokens=1,2 delims=:" %%a in ("%%s") do (
                                    echo [INFO] Testing %%a service at localhost:%%b...
                                    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%%b/health' -TimeoutSec 10; if ($response.StatusCode -eq 200) { Write-Host '[SUCCESS] %%a service is healthy' } else { Write-Host '[ERROR] %%a service returned HTTP' $response.StatusCode; exit 1 } } catch { Write-Host '[ERROR] %%a service is not responding:' $_.Exception.Message; exit 1 }"
                                    if !ERRORLEVEL! NEQ 0 set ALL_HEALTHY=0
                                )
                            )
                            
                            if !ALL_HEALTHY! EQU 0 (
                                echo [ERROR] Some services failed health checks
                                exit /b 1
                            )
                            
                            echo [INFO] All microservices are healthy
                            endlocal
                            '''
                        }
                    }
                }
            }
        }

        stage('Integration Test') {
            steps {
                script {
                    bat '''
                    @echo off
                    echo [INFO] Running quick integration test...
                    
                    :: Test that Django can reach all microservices
                    docker compose -p %COMPOSE_PROJECT_NAME% -f docker-compose.yaml -f docker-compose.ci.yml up -d django_app
                    
                    echo [INFO] Waiting for Django to start...
                    timeout /t 20 /nobreak >nul
                    
                    echo [INFO] Testing Django application...
                    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:%CI_DJANGO_PORT%' -TimeoutSec 10; if ($response.StatusCode -eq 200) { Write-Host '[SUCCESS] Django application is responding' } else { Write-Host '[ERROR] Django returned HTTP' $response.StatusCode; exit 1 } } catch { Write-Host '[ERROR] Django is not responding:' $_.Exception.Message; exit 1 }"
                    
                    if !ERRORLEVEL! NEQ 0 (
                        echo [ERROR] Integration test failed
                        exit /b 1
                    )
                    
                    echo [INFO] Integration test passed
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                // Publish test results
                if (fileExists('test-results/junit.xml')) {
                    junit 'test-results/junit.xml'
                    echo "[INFO] Test results published"
                } else {
                    echo "[WARNING] No test results found"
                }
                
                // Publish coverage report
                if (fileExists('test-results/coverage.xml')) {
                    publishHTML([
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'test-results/htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                    echo "[INFO] Coverage report published"
                }
                
                // Clean up CI containers only (preserve development environment)
                bat '''
                @echo off
                echo [INFO] Cleaning up CI containers (preserving development environment)...
                docker compose -p %COMPOSE_PROJECT_NAME% down -v --remove-orphans 2>nul || echo "No CI containers to clean"
                
                :: Remove CI-specific compose file
                if exist "docker-compose.ci.yml" del docker-compose.ci.yml
                
                :: Clean up any orphaned CI containers
                for /f "tokens=*" %%i in ('docker ps -aq --filter "name=%COMPOSE_PROJECT_NAME%"') do (
                    echo [INFO] Removing CI container: %%i
                    docker rm -f %%i 2>nul || echo "Failed to remove: %%i"
                )
                
                echo [INFO] CI cleanup complete - development environment preserved
                '''
            }
        }
        
        success {
            echo "✅ Pipeline completed successfully! Development environment is untouched."
        }
        
        failure {
            echo "❌ Pipeline failed. Check logs above. Development environment is preserved."
        }
    }
}