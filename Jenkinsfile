pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://localhost:9000'
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary"
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001
        APP_PORT_CONTAINER = 5000
        SONARQUBE_SERVER_CONFIG_NAME = 'GeminiSonarQube' 
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
                        // Pre-create .scannerwork for the report-task.txt
                        // Pre-create .sonartmp for scanner's internal working files
                        // Pre-create .sonar for persistent cache
                        sh "mkdir -p .scannerwork .sonar .sonartmp"
                        sh "chmod -R 777 .scannerwork .sonar .sonartmp"

                        // Define the path for the metadata file *inside the container* TO THE DEFAULT LOCATION
                        def containerMetadataFilePathInDocker = "/usr/src/.scannerwork/report-task.txt"

                        sh """
                        echo "Attempting SonarQube scan..."
                        echo "Workspace (pwd): \$(pwd)"
                        echo "Report task file will be at (container path): ${containerMetadataFilePathInDocker}"
                        ls -la

                        docker run --rm \\
                            --network="host" \\
                            -u "\$(id -u):\$(id -g)" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "\$(pwd):/usr/src" \\
                            -v "\$(pwd)/.sonartmp:/usr/src/.sonartmp" \\
                            -v "\$(pwd)/.sonar:/usr/src/.sonar" \\
                            # We also need to mount .scannerwork if we specify it for metadata
                            -v "\$(pwd)/.scannerwork:/usr/src/.scannerwork" \\
                            sonarsource/sonar-scanner-cli \\
                            -Dsonar.projectBaseDir=/usr/src \\
                            -Dsonar.working.directory=/usr/src/.sonartmp \\
                            -Dsonar.userHome=/usr/src/.sonar \\
                            -Dsonar.scanner.metadataFilePath=${containerMetadataFilePathInDocker}

                        echo "Sonar scan command finished."
                        echo "Checking for ${containerMetadataFilePathInDocker} (on host: .scannerwork/report-task.txt)..."
                        if [ ! -f ".scannerwork/report-task.txt" ]; then
                            echo "ERROR: .scannerwork/report-task.txt not found after scan!"
                            exit 1
                        fi
                        echo ".scannerwork/report-task.txt found. Contents:"
                        cat ".scannerwork/report-task.txt"
                        """
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    // Let waitForQualityGate try to find the task automatically from the default location
                    // It should use the server from withSonarQubeEnv context.
                    waitForQualityGate abortPipeline: true
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
        }
    }
}
