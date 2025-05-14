pipeline {
    agent any // Or specify an agent with Docker installed: agent { label 'docker-agent' }

    environment {
        // GEMINI_API_KEY will be injected from Jenkins credentials
        SONAR_HOST_URL = 'http://localhost:9000' // Correct for --network="host" on scanner
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary"
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001
        APP_PORT_CONTAINER = 5000
    }

    stages {
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
                    // Using sh for docker build as docker.build() might have different credential handling needs
                    // or if you prefer direct shell commands.
                    sh "docker build -t ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} ."
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                // Use a distinct variable name for the credential's value
                // Ensure 'your-sonarqube-token-id' is the EXACT ID of your "Secret text" credential in Jenkins
                SONAR_LOGIN_TOKEN_FROM_CREDENTIALS = credentials('your-sonarqube-token-id')
            }
            steps {
                script {
                    // Assuming sonar-project.properties is in your Git repo root (the current workspace)
                    // The sonar-scanner-cli container will run using the host's network.
                    // SONAR_HOST_URL is http://localhost:9000 (from global environment)
                    // SONAR_LOGIN_TOKEN_FROM_CREDENTIALS holds the token value.
                    sh """
                    echo "Attempting SonarQube scan..."
                    echo "Sonar Host URL: ${env.SONAR_HOST_URL}"
                    echo "Workspace (pwd): ${pwd()}"
                    ls -la # List files in workspace to ensure sonar-project.properties is there

                    docker run --rm \\
                        --network="host" \\
                        -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                        -e SONAR_TOKEN="${SONAR_LOGIN_TOKEN_FROM_CREDENTIALS}" \\
                        -v "${pwd()}:/usr/src" \\
                        sonarsource/sonar-scanner-cli
                    """
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    // Ensure 'YourSonarQubeServerNameInJenkins' matches the Name field in
                    // Manage Jenkins -> Configure System -> SonarQube servers
                    waitForQualityGate 'YourSonarQubeServerNameInJenkins'
                }
            }
        }

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
                    echo "Access at http://<jenkins-agent-ip>:${env.APP_PORT_HOST}"
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

    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo "Application deployed successfully: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline failed.'
            // sh "docker logs ${env.APP_CONTAINER_NAME} || echo 'No logs for ${env.APP_CONTAINER_NAME}'"
        }
    }
}
