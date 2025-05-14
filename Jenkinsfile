pipeline {
    agent any // Or specify an agent with Docker installed

    environment {
        SONAR_HOST_URL = 'http://localhost:9000' // URL of your SonarQube server
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary" // Your preferred Docker image name
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001      // Port on the Jenkins host machine to map to the container
        APP_PORT_CONTAINER = 5000 // Port your application listens on INSIDE the container (from Dockerfile)
        // !!! IMPORTANT: Replace 'GeminiSonarQube' with the EXACT name of your SonarQube server
        // configuration in Jenkins (Manage Jenkins -> Configure System -> SonarQube servers)
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
                    // Build the Docker image using the Dockerfile in the current directory
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
                        // We will let the scanner create its .scannerwork and .sonar directories
                        // inside the mounted volume /usr/src, controlled by the -u flag for permissions.
                        // We still create .sonartmp for its internal working dir.
                        sh "mkdir -p .sonartmp"
                        sh "chmod -R 777 .sonartmp" // Make it writable

                        // Define the full path for the report task file inside the container
                        def containerReportTaskPath = "/usr/src/${env.SONAR_REPORT_TASK_FILE}"

                        sh """
                        echo "Attempting SonarQube scan..."
                        echo "Workspace (pwd): \$(pwd)"
                        echo "Report task file will be at (container path): ${containerReportTaskPath}"
                        ls -la

                        docker run --rm \\
                            --network="host" \\
                            -u "\$(id -u):\$(id -g)" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "\$(pwd):/usr/src" \\
                            -v "\$(pwd)/.sonartmp:/usr/src/.sonartmp" \\ 
                            sonarsource/sonar-scanner-cli \\
                            -Dsonar.projectBaseDir=/usr/src \\
                            -Dsonar.working.directory=/usr/src/.sonartmp \\
                            -Dsonar.scanner.metadataFilePath=${containerReportTaskPath} 

                        echo "Sonar scan command finished."
                        echo "Checking for report task file at host path: ${env.SONAR_REPORT_TASK_FILE}..."
                        if [ ! -f "${env.SONAR_REPORT_TASK_FILE}" ]; then
                            echo "ERROR: ${env.SONAR_REPORT_TASK_FILE} not found after scan!"
                            echo "Listing workspace contents:"
                            ls -la
                            echo "Listing .sonartmp contents (if any):"
                            ls -la .sonartmp || echo ".sonartmp directory not found or empty"
                            echo "Listing .scannerwork contents (if created by scanner unexpectedly):"
                            ls -la .scannerwork || echo ".scannerwork directory not found or empty"
                            exit 1
                        fi
                        echo "${env.SONAR_REPORT_TASK_FILE} found. Contents:"
                        cat "${env.SONAR_REPORT_TASK_FILE}"
                        """
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        // Use the SONAR_REPORT_TASK_FILE env var
                        def reportTaskFile = env.SONAR_REPORT_TASK_FILE 
                        if (!fileExists(reportTaskFile)) {
                            error "SonarQube report task file not found: ${reportTaskFile}. Cannot check Quality Gate."
                        }
                        def reportTaskContent = readFile(reportTaskFile).trim()
                        echo "Contents of ${reportTaskFile} for Quality Gate: ${reportTaskContent}"

                        def taskIdMatcher = (reportTaskContent =~ /ceTaskUrl=.*id=([^&]+)/)
                        if (!taskIdMatcher.find()) {
                             error "Could not extract task ID from reportTaskContent using regex. Content: ${reportTaskContent}"
                        }
                        def sonarTaskId = taskIdMatcher[0][1]
                        echo "Extracted SonarQube Task ID: ${sonarTaskId}"

                        waitForQualityGate server: env.SONARQUBE_SERVER_CONFIG_NAME, taskId: sonarTaskId, abortPipeline: true
                    }
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
        }
    }
}
