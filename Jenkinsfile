pipeline {
    agent any

    environment {
        VENV = "${WORKSPACE}/.venv"
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
                sh 'docker compose build'
            }
        }

        stage('Run Django Unit Tests') {
            steps {
                sh '''
                docker compose run --rm django_app bash -c "
                    python manage.py migrate --noinput &&
                    python manage.py test
                "
                '''
            }
        }

        stage('Start Integration Stack') {
            steps {
                sh 'docker compose up -d'
                sh '''
                echo "Waiting for Django API to become healthy..."
                for i in {1..30}; do
                    if curl -sf http://localhost:8000/api/health/ > /dev/null; then
                        echo "Django API is healthy."
                        exit 0
                    fi
                    sleep 5
                done
                echo "Django API failed to start in time." >&2
                exit 1
                '''
            }
        }

        stage('Selenium Tests') {
            steps {
                sh '''
                python3 -m venv ${VENV}
                . ${VENV}/bin/activate
                pip install --upgrade pip
                pip install -r tests/selenium/requirements.txt
                pytest tests/selenium --base-url=http://localhost:8000 --maxfail=1 --disable-warnings
                '''
            }
        }
    }

    post {
        always {
            sh 'docker compose down -v || true'
            sh 'rm -rf ${VENV} || true'
        }
    }
}

