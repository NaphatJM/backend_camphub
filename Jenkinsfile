pipeline {
    agent any  // ใช้ Jenkins node ที่มี Docker CLI

    environment {
        SONARQUBE = credentials('sonar-token')   // Jenkins Credentials สำหรับ SonarQube token
        SQLDB_URL = credentials('SQLDB_URL')       // Jenkins credentials ID
        SECRET_KEY = credentials('SECRET_KEY')
        JWT_SECRET_KEY = credentials('JWT_SECRET_KEY')
        POSTGRES_USER = credentials('POSTGRES_USER')
        POSTGRES_PASSWORD = credentials('POSTGRES_PASSWORD')
        POSTGRES_DB = credentials('POSTGRES_DB')
        PGADMIN_EMAIL = credentials('PGADMIN_EMAIL')
        PGADMIN_PASSWORD = credentials('PGADMIN_PASSWORD')
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
                    reuseNode true
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
                              sonar-scanner \
                                  -Dsonar.projectKey=backend_camphub \
                                  -Dsonar.sources=app \
                                  -Dsonar.host.url=http://host.docker.internal:9001 \
                                  -Dsonar.login=${SONARQUBE} \
                                  -Dsonar.exclusions=**/tests/**,**/*.md \
                                  -Dsonar.python.ignoreHeaderComments=true \
                                  -Dsonar.python.coverage.reportPaths=coverage.xml
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
        stage('Deploy with Docker Compose') {
          agent any
          steps {
              sh '''
                # ติดตั้ง docker-compose ถ้ายังไม่มี
                export PATH="$HOME/.local/bin:$PATH"
                mkdir -p $HOME/.local/bin

                if ! command -v docker-compose >/dev/null 2>&1; then
                  curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o $HOME/.local/bin/docker-compose
                  chmod +x $HOME/.local/bin/docker-compose
                fi

                # Start containers (backend, postgres, pgadmin) ตาม docker-compose.yml
                docker-compose down || true
                docker-compose up -d --build

                # รอ DB พร้อม (optional)
                for i in {1..10}; do
                  docker exec camphub_db pg_isready -U $POSTGRES_USER -d $POSTGRES_DB && break
                  sleep 2
                done

                # Init DB (create tables)
                docker exec backend_camphub 
                ls
                python ./scripts/init_db.py
                '''
          }
      }

    //     stage('Build Docker Image') {
    //         agent any
    //         steps {
    //             sh 'docker build -t backend_camphub:latest .'
    //         }
    //     }

    //     stage('Deploy Container') {
    //         agent any
    //         steps {
    //             sh '''
    //             # ติดตั้ง docker-compose ถ้ายังไม่มี (ติดตั้งใน $HOME/.local/bin)
    //             export PATH="$HOME/.local/bin:$PATH"
    //             mkdir -p $HOME/.local/bin
    //             if ! command -v docker-compose >/dev/null 2>&1; then
    //               curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o $HOME/.local/bin/docker-compose
    //               chmod +x $HOME/.local/bin/docker-compose
    //             fi

    //             # Start DB & pgadmin
    //             docker-compose down || true
    //             docker-compose up -d

    //             # รอ DB พร้อม (optional)
    //             for i in {1..10}; do
    //               docker exec camphub_db pg_isready && break
    //               sleep 2
    //             done

    //             docker stop backend_camphub || true
    //             docker rm backend_camphub || true
    //             docker run -d \
    //                     --network camphub_default \
    //                     -e SQLDB_URL=$SQLDB_URL \
    //                     -e SECRET_KEY=$SECRET_KEY \
    //                     -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
    //                     --name backend_camphub \
    //                     -p 8000:8000 \
    //                     backend_camphub:latest \
    //                     uvicorn app.main:app --host 0.0.0.0 --port 8000
    //             '''
    //         }
    //     }
    }

    post {
        always {
            echo "✅ Pipeline finished"
        }
    }
}