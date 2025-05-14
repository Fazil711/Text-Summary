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
                        // These sh steps are fine as they are individual commands
                        sh "mkdir -p .scannerwork"
                        sh "mkdir -p .sonar"
                        sh "mkdir -p .sonartmp"
                        sh "chmod -R 777 .scannerwork .sonar .sonartmp"

                        // The entire sequence of docker run and subsequent checks must be in ONE sh block
                        sh """
                        echo "Attempting SonarQube scan..."
                        echo "Workspace (pwd): \$(pwd)"  # Use \$(pwd) for shell's pwd
                        echo "Listing workspace contents:"
                        ls -la

                        # Construct and execute Docker Scanner Command
                        # Using single quotes for the main body to prevent premature Groovy interpolation
                        # and using shell variables for dynamic parts.
                        # SONARQUBE_TOKEN_VALUE_SHELL is set by withCredentials and available here.
                        # env.SONAR_HOST_URL is available from Jenkins environment.
                        
                        # Backslashes for line continuation must be the VERY LAST character on the line.
                        docker run --rm \\
                            --network="host" \\
                            -u "\$(id -u):\$(id -g)" \\
                            -e SONAR_HOST_URL="${env.SONAR_HOST_URL}" \\
                            -e SONAR_TOKEN="${SONARQUBE_TOKEN_VALUE}" \\
                            -v "\$(pwd):/usr/src" \\
                            -v "\$(pwd)/.scannerwork:/usr/src/.scannerwork" \\
                            -v "\$(pwd)/.sonar:/usr/src/.sonar" \\
                            -v "\$(pwd)/.sonartmp:/usr/src/.sonartmp" \\
                            sonarsource/sonar-scanner-cli \\
                            -Dsonar.projectBaseDir=/usr/src \\
                            -Dsonar.userHome=/usr/src/.sonar \\
                            -Dsonar.working.directory=/usr/src/.sonartmp

                        echo "Sonar scan command finished."
                        echo "Checking for report-task.txt..."
                        if [ ! -f ".scannerwork/report-task.txt" ]; then
                            echo "ERROR: .scannerwork/report-task.txt not found after scan!"
                            echo "Listing .scannerwork directory contents (if it exists):"
                            ls -la .scannerwork || echo ".scannerwork directory not found or empty"
                            exit 1 # Make the sh step fail if report-task.txt is not found
                        fi
                        echo ".scannerwork/report-task.txt found. Contents:"
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
                        def reportTaskFile = ".scannerwork/report-task.txt" // Relative to workspace root
                        // This check is now redundant if the sh step above exits on failure, but good for safety.
                        if (!fileExists(reportTaskFile)) {
                            error "SonarQube report task file not found: ${reportTaskFile}. Cannot check Quality Gate."
                        }
                        def reportTaskContent = readFile(reportTaskFile).trim()
                        echo "Contents of report-task.txt for Quality Gate: ${reportTaskContent}"

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
