pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://localhost:9000'
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary"
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001
        APP_PORT_CONTAINER = 5000
        SONARQUBE_SERVER_CONFIG_NAME = 'GeminiSonarQube' // Your confirmed server name
    }

    stages {
        // ... Checkout, Build Docker Image, SonarQube Analysis stages ...
        // (These remain the same as the previous good version)
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh 'docker --version'
                    sh "docker build -t ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} ."
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                SONARQUBE_TOKEN_VALUE = credentials('your-sonarqube-token-id') 
            }
            steps {
                withSonarQubeEnv(env.SONARQUBE_SERVER_CONFIG_NAME) {
                    script {
                        sh """
                        echo "Attempting SonarQube scan using server config: ${env.SONARQUBE_SERVER_CONFIG_NAME}"
                        echo "Sonar Host URL from Jenkins SonarQube config: \$SONAR_HOST_URL" 
                        echo "Sonar Token from Jenkins SonarQube config (if set): \$SONAR_AUTH_TOKEN"
                        echo "Workspace (pwd): ${pwd()}"
                        ls -la

                        docker run --rm \\
                            --network="host" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "${pwd()}:/usr/src" \\
                            sonarsource/sonar-scanner-cli
                        
                        echo "Sonar scan command finished."
                        echo "Checking for .scannerwork directory existence after scan:"
                        ls -lad .scannerwork || echo ".scannerwork directory NOT FOUND immediately after scan"
                        """
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    // Corrected: Removed the 'server:' parameter as it's inferred from withSonarQubeEnv
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ... Deploy Application, Post-Deployment Verification stages ...
        // (These remain the same)
        stage('Deploy Application') {
            steps {
                script {
                    sh "docker stop ${env.APP_CONTAINER_NAME} || true"
                    sh "docker rm ${env.APP_CONTAINER_NAME} || true"
                    withCredentials([string(credentialsId: 'gemini-api-key', variable: 'GEMINI_API_KEY_VALUE')]) {
                        sh """
                        docker run -d \\
                            --name ${env.APP_CONTAINER_NAME} \\
                            -p ${env.APP_PORT_HOST}:${env.APP_PORT_CONTAINER} \\
                            -e PORT=${env.APP_PORT_CONTAINER} \\
                            -e GEMINI_API_KEY=${GEMINI_API_KEY_VALUE} \\
                            ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}
                        """
                    }
                    echo "Application container ${env.APP_CONTAINER_NAME} started."
                }
            }
        }

        stage('Post-Deployment Verification') {
            steps {
                echo "Verifying deployment at http://localhost:${env.APP_PORT_HOST}/"
                script {
                    sleep(time: 15, unit: 'SECONDS')
                }
                sh "curl -s -f http://localhost:${env.APP_PORT_HOST}/ || exit 1"
            }
        }
    }
    // ... post block ...
    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo "Application deployed successfully: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
