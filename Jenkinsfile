pipeline {
    agent any

    environment {
        SONAR_HOST_URL = 'http://localhost:9000'
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary"
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001
        APP_PORT_CONTAINER = 5000
        SONARQUBE_SERVER_CONFIG_NAME = 'GeminiSonarQube' // !!! CHANGE THIS to your actual server name in Jenkins
    }

    stages {
        // ... (Checkout, Build Docker Image stages remain the same) ...
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
                // Still use withSonarQubeEnv for server configuration context
                withSonarQubeEnv(env.SONARQUBE_SERVER_CONFIG_NAME) {
                    script {
                        // The .scannerwork directory will be created in the workspace
                        // We need to ensure the Docker container writes to a place in the mounted volume
                        // that corresponds to the Jenkins workspace.
                        // The scanner by default creates .scannerwork in its current execution directory.
                        // Inside the container, the work dir is /usr/src (our mounted workspace)
                        // So, .scannerwork should appear in the Jenkins workspace root.

                        sh """
                        echo "Attempting SonarQube scan using server config: ${env.SONARQUBE_SERVER_CONFIG_NAME}"
                        echo "Sonar Host URL: ${env.SONAR_HOST_URL}"
                        echo "Workspace (pwd): ${pwd()}"
                        ls -la

                        # Run the scanner. It will create .scannerwork/report-task.txt in /usr/src
                        docker run --rm \\
                            --network="host" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "${pwd()}:/usr/src" \\
                            sonarsource/sonar-scanner-cli

                        echo "Scan command finished. Checking for report-task.txt..."
                        # Check if the report-task.txt was created
                        if [ ! -f ".scannerwork/report-task.txt" ]; then
                            echo "ERROR: .scannerwork/report-task.txt not found after scan!"
                            ls -la .scannerwork || echo ".scannerwork directory not found or empty"
                            exit 1
                        fi
                        echo ".scannerwork/report-task.txt found."
                        cat .scannerwork/report-task.txt
                        """
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        // Read the report-task.txt file from the workspace
                        // This file is created by the sonar-scanner
                        def reportTaskFile = ".scannerwork/report-task.txt"
                        if (!fileExists(reportTaskFile)) {
                            error "SonarQube report task file not found: ${reportTaskFile}. Cannot check Quality Gate."
                        }
                        def reportTaskContent = readFile(reportTaskFile).trim()
                        echo "Contents of report-task.txt: ${reportTaskContent}"

                        // Extract task ID. Example content: ceTaskUrl=http://localhost:9000/api/ce/task?id=AYpQh....
                        // We need the value of the 'id' parameter.
                        def taskUrl = Eigenschaften.parse(reportTaskContent).getProperty('ceTaskUrl')
                        if (!taskUrl) {
                             error "Could not parse ceTaskUrl from ${reportTaskFile}. Content: ${reportTaskContent}"
                        }
                        def taskIdMatcher = (taskUrl =~ /id=([^&]+)/)
                        if (!taskIdMatcher.find()) {
                            error "Could not extract task ID from ceTaskUrl: ${taskUrl}"
                        }
                        def sonarTaskId = taskIdMatcher[0][1]
                        echo "Extracted SonarQube Task ID: ${sonarTaskId}"

                        // Use the extracted task ID with waitForQualityGate
                        // Ensure the server name matches your Jenkins SonarQube server configuration
                        waitForQualityGate server: env.SONARQUBE_SERVER_CONFIG_NAME, taskId: sonarTaskId, abortPipeline: true
                    }
                }
            }
        }
        // ... (Deploy Application, Post-Deployment Verification stages remain the same) ...
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
    // ... (post block)
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

// Helper class for parsing properties file format (like report-task.txt)
// This needs to be outside the pipeline block, or you can use a shared library.
// For simplicity here, putting it at the end. Jenkins CPS sandbox might need approval for Properties.
// If Properties class is not allowed/problematic, a simpler regex for ceTaskUrl might be needed.
// @NonCPS // This annotation might be needed if used within pipeline script directly for complex methods
class Eigenschaften {
    static java.util.Properties parse(String content) {
        def props = new java.util.Properties()
        new StringReader(content).withReader { reader ->
            props.load(reader)
        }
        return props
    }
}
