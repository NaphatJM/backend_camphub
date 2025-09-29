pipeline {
    agent any  // ใช้ Jenkins node ที่มี Docker CLI

    environment {
        SONARQUBE = credentials('sonar-token')   // Jenkins Credentials สำหรับ SonarQube token
        SQLDB_URL = credentials('SQLDB_URL')       // Jenkins credentials ID
        SECRET_KEY = credentials('SECRET_KEY')
        JWT_SECRET_KEY = credentials('JWT_SECRET_KEY')
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/kornphongP/backend_camphub.git'
            }
        }

        stage('Install Dependencies & Run Tests') {
            agent {
                docker {
                    image 'python:3.12'
                    args '-u root:root -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
            steps {
                sh 'curl -sSL https://install.python-poetry.org | python3 -'
                sh 'export PATH="$HOME/.local/bin:$PATH" && /root/.local/bin/poetry --version'

                // ตรวจสอบ lock file ถ้า mismatch ให้ regenerate
                sh '''
                set -e
                export PATH="$HOME/.local/bin:$PATH"
                if ! /root/.local/bin/poetry check --lock; then
                    echo "⚠️  pyproject.toml และ poetry.lock ไม่ตรงกัน → regenerate lock file"
                    /root/.local/bin/poetry lock
                fi
                '''

                // ติดตั้ง dependencies
                sh 'export PATH="$HOME/.local/bin:$PATH" && /root/.local/bin/poetry install --no-interaction'

                // รัน tests + coverage
                sh 'export PATH="$HOME/.local/bin:$PATH" && /root/.local/bin/poetry run coverage run -m pytest tests/'
                sh 'export PATH="$HOME/.local/bin:$PATH" && /root/.local/bin/poetry run coverage xml -o coverage.xml'
            }
        }


        stage('SonarQube Analysis') {
            steps {
                script {
                    withSonarQubeEnv('SonarQubeServer') {
                        docker.image('sonarsource/sonar-scanner-cli').inside {
                            sh '''
                                export PATH="$HOME/.local/bin:$PATH"
                                sonar-scanner \
                                    -Dsonar.projectKey=backend_camphub \
                                    -Dsonar.sources=app \
                                    -Dsonar.tests=tests \
                                    -Dsonar.host.url=http://host.docker.internal:9001 \
                                    -Dsonar.login=${SONARQUBE} \
                                    -Dsonar.exclusions=**/tests/**,**/*.md,**/app/core/** \
                                    -Dsonar.python.ignoreHeaderComments=true \
                                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                            '''
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build Docker Image') {
            agent any
            steps {
                sh 'docker build -t backend_camphub:latest .'
            }
        }

        stage('Deploy Container') {
            agent any
            steps {
                sh '''
                docker stop backend_camphub || true
                docker rm backend_camphub || true
                docker run -d \
                        -e SQLDB_URL=$SQLDB_URL \
                        -e SECRET_KEY=$SECRET_KEY \
                        -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
                        --name backend_camphub \
                        -p 8000:8000 \
                        backend_camphub:latest \
                        uvicorn app.main:app --host 0.0.0.0 --port 8000
                '''
            }
        }
    }

    post {
        always {
            echo "✅ Pipeline finished"
        }
    }
}