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
                // !!! IMPORTANT: Replace 'your-sonarqube-token-id' with the EXACT ID of your
                // "Secret text" credential in Jenkins holding the SonarQube token
                SONARQUBE_TOKEN_VALUE = credentials('your-sonarqube-token-id')
            }
            steps {
                // withSonarQubeEnv helps set up context for waitForQualityGate
                withSonarQubeEnv(env.SONARQUBE_SERVER_CONFIG_NAME) {
                    script {
                        sh "mkdir -p .scannerwork"
                        sh "mkdir -p .sonar"
                        sh "mkdir -p .sonartmp"
                        sh "chmod -R 777 .scannerwork .sonar .sonartmp" // Make them writable

                        // Construct the command as a variable first for clarity and debugging
                        def dockerScannerCommand = """\
                        docker run --rm \\
                            --network="host" \\
                            -u "\$(id -u):\$(id -g)" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "${pwd()}:/usr/src" \\
                            -v "${pwd()}/.scannerwork:/usr/src/.scannerwork" \\
                            -v "${pwd()}/.sonar:/usr/src/.sonar" \\
                            -v "${pwd()}/.sonartmp:/usr/src/.sonartmp" \\
                            sonarsource/sonar-scanner-cli \\
                            -Dsonar.projectBaseDir=/usr/src \\
                            -Dsonar.userHome=/usr/src/.sonar \\
                            -Dsonar.working.directory=/usr/src/.sonartmp \
                        """ // Note: No backslash after the last -D argument

                        echo "Attempting SonarQube scan..."
                        echo "Workspace (pwd): ${pwd()}"
                        echo "Listing workspace contents:"
                        ls -la
                        echo "Executing Docker Scanner Command:"
                        echo dockerScannerCommand // This will print the command with escaped newlines, use below for clean print
                        // For a cleaner print of the command as it would look in a shell:
                        // sh "echo '${dockerScannerCommand.replaceAll("\\\\", "\\\\\\\\").replaceAll("'", "\\\\'")}'" // More complex escaping needed

                        sh "${dockerScannerCommand}" // Execute the command

                        echo "Sonar scan command finished."
                        echo "Checking for report-task.txt..."
                        if [ ! -f ".scannerwork/report-task.txt" ]; then
                            echo "ERROR: .scannerwork/report-task.txt not found after scan!"
                            echo "Listing .scannerwork directory contents (if it exists):"
                            ls -la .scannerwork || echo ".scannerwork directory not found or empty"
                            exit 1
                        fi
                        echo ".scannerwork/report-task.txt found. Contents:"
                        cat .scannerwork/report-task.txt
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def reportTaskFile = ".scannerwork/report-task.txt"
                        if (!fileExists(reportTaskFile)) {
                            error "SonarQube report task file not found: ${reportTaskFile}. Cannot check Quality Gate."
                        }
                        def reportTaskContent = readFile(reportTaskFile).trim()
                        echo "Contents of report-task.txt: ${reportTaskContent}"

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
