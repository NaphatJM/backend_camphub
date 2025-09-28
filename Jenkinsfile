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
                sh 'pip install --upgrade pip'
                sh 'pip install coverage pytest'
                // ติดตั้ง Poetry
                // sh 'curl -sSL https://install.python-poetry.org | python3 -'
                // sh 'export PATH="$HOME/.local/bin:$PATH"'

                // ติดตั้ง dependencies
                // sh '/root/.local/bin/poetry install --no-interaction'
                // sh '/root/.local/bin/poetry run coverage run -m pytest tests/'
                // sh '/root/.local/bin/poetry run coverage xml'
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
                                -Dsonar.exclusions=**/tests/**,**/*.md \
                                -Dsonar.python.ignoreHeaderComments=true
                        '''
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
    }

    post {
        always {
            echo "✅ Pipeline finished"
        }
    }
}