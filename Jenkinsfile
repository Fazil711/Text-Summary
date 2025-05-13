pipeline {
    agent any // Or specify an agent with Docker installed: agent { label 'docker-agent' }

    environment {
        // GEMINI_API_KEY will be injected from Jenkins credentials
        // SonarQube server URL and token will also be managed
        SONAR_HOST_URL = 'http://localhost:9000' // If SonarQube is running on the Jenkins host, or use service name if Jenkins runs SonarQube as a service in the pipeline
        DOCKER_IMAGE_NAME = "fazil711/gemini-text-summary" // Your Docker Hub username / image name
        DOCKER_IMAGE_TAG = "build-${BUILD_NUMBER}"
        APP_CONTAINER_NAME = "gemini-app-instance"
        APP_PORT_HOST = 5001 // Port on the host Jenkins machine
        APP_PORT_CONTAINER = 5000 // Port inside the container (matches Dockerfile ENV PORT)
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
                    // Ensure Docker is available
                    sh 'docker --version'
                    // Build the Docker image
                    // docker.build uses the Dockerfile in the current directory
                    def customImage = docker.build("${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}")

                    // (Optional) Push to a Docker registry if you have one configured
                    // docker.withRegistry('https://your-registry.com', 'your-registry-credentials-id') {
                    //    customImage.push()
                    //    customImage.push('latest') // Optionally push a 'latest' tag
                    // }
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                // Get SonarQube token from Jenkins credentials
                SONAR_TOKEN = credentials('your-sonarqube-token-id') // Create this credential in Jenkins
            }
            steps {
                script {
                    // Assuming sonar-project.properties is in your Git repo
                    // Run SonarScanner using its Docker image for simplicity and consistency
                    // Mount project workspace, pass necessary env vars
                    // Make sure the user running docker in Jenkins has permissions for /var/run/docker.sock if needed by scanner
                    // The network_mode: "host" might be needed if SonarScanner docker needs to reach SonarQube on localhost:9000
                    // Or use a defined docker network if both SonarQube and Scanner run in containers managed by Jenkins.
                    // For now, assuming SonarQube is accessible at SONAR_HOST_URL from the Jenkins agent.

                    // Create sonar-project.properties if it doesn't exist or needs dynamic content
                    // For Python, ensure coverage reports are generated if you want coverage in SonarQube
                    // Example: You might run tests and generate coverage.xml in a prior step or within this one.

                    sh """
                    docker run --rm \\
                        -e SONAR_HOST_URL=${env.SONAR_HOST_URL} \\
                        -e SONAR_LOGIN=${SONAR_TOKEN} \\
                        -v "${pwd()}:/usr/src" \\
                        sonarsource/sonar-scanner-cli
                    """
                    // Add -Dsonar.projectKey, -Dsonar.sources etc. if not using sonar-project.properties
                    // or if you want to override them.
                }
            }
        }

        stage('Check Quality Gate') { // Optional
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    // Name configured in Jenkins Manage -> Configure System -> SonarQube servers
                    waitForQualityGate 'YourSonarQubeServerNameInJenkins' 
                }
            }
        }

        stage('Deploy Application') {
            steps {
                script {
                    // Stop and remove any existing container with the same name
                    sh "docker stop ${env.APP_CONTAINER_NAME} || true"
                    sh "docker rm ${env.APP_CONTAINER_NAME} || true"

                    // Run the new Docker container
                    // Inject GEMINI_API_KEY from Jenkins credentials
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
                    sleep(time: 15, unit: 'SECONDS') // Give container time to start fully
                }
                // Curl runs on the Jenkins agent, targeting the port mapped on the agent's host
                sh "curl -s -f http://localhost:${env.APP_PORT_HOST}/ || exit 1"
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished.'
            // Optional: Clean up Docker image if not pushed to a registry and only needed for this build
            // sh "docker rmi ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG} || true"
        }
        success {
            echo "Application deployed successfully: ${env.DOCKER_IMAGE_NAME}:${env.DOCKER_IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline failed.'
            // Optional: Log container logs on failure
            // sh "docker logs ${env.APP_CONTAINER_NAME} || echo 'No logs for ${env.APP_CONTAINER_NAME}'"
        }
    }
}
