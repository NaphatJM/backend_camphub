pipeline {
    agent any  // ใช้ Jenkins node ที่มี Docker CLI

    environment {
        SONARQUBE = credentials('sonar-token')   // Jenkins Credentials สำหรับ SonarQube token
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
                // ติดตั้ง Poetry
                sh 'curl -sSL https://install.python-poetry.org | python3 -'
                sh 'export PATH="$HOME/.local/bin:$PATH"'

                // ติดตั้ง dependencies
                sh 'poetry install --no-interaction'

                // รัน unit test และ generate coverage report
                sh 'poetry run coverage run -m pytest tests/'
                sh 'poetry run coverage xml'
            }
        }


        stage('SonarQube Analysis') {
            steps {
                script {
                    docker.image('sonarsource/sonar-scanner-cli').inside {
                        sh '''
                            sonar-scanner \
                                -Dsonar.projectKey=backend_camphub \
                                -Dsonar.sources=app \
                                -Dsonar.host.url=http://host.docker.internal:9001 \
                                -Dsonar.login=${SONARQUBE} \
                        '''
                    }
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t fastapi-app:latest .'
            }
        }

        stage('Deploy Container') {
            steps {
                script {
                    // Set environment variables and port (customizable)
                    def appPort = env.APP_PORT ?: '8000'
                    def appEnv = env.APP_ENV ?: 'production'

                    // Stop & remove old container if exists
                    sh '''
                    if [ $(docker ps -aq -f name=app) ]; then
                        docker stop app
                        docker rm app
                    fi
                    '''

                    // Run new container with env and port mapping
                    sh """
                    docker run -d \
                        --name app \
                        -e APP_ENV=${appEnv} \
                        -p ${appPort}:8000 \
                        fastapi-app:latest \
                        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
                    """
                }
            }
        }
    }

    post {
        always {
            echo "✅ Pipeline finished"
        }
    }
}