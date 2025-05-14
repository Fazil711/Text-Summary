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
        SONAR_METADATA_FILENAME = 'sonar-analysis-metadata.txt' // Consistent filename
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
                        sh "mkdir -p .sonartmp"
                        sh "chmod -R 777 .sonartmp"

                        // Define the path for the metadata file *inside the container*
                        def containerMetadataFilePathInDocker = "/usr/src/${env.SONAR_METADATA_FILENAME}"
                        // Define the path for the metadata file *on the host/Jenkins workspace*
                        def hostMetadataFilePath = env.SONAR_METADATA_FILENAME

                        // Construct the full docker command string carefully
                        def dockerScannerCmd = """\
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
                            -Dsonar.scanner.metadataFilePath=${containerMetadataFilePathInDocker}\
                        """ // NO trailing backslash here

                        // This ENTIRE block is now one sh script
                        sh """
                        echo "Attempting SonarQube scan..."
                        echo "Workspace (pwd): \$(pwd)"
                        echo "Report task file will be written to (container path): ${containerMetadataFilePathInDocker}"
                        echo "Report task file expected at (host path): ${hostMetadataFilePath}"
                        echo "Listing workspace contents before scan:"
                        ls -la
                        echo "Full Docker command to be executed:"
                        echo '${dockerScannerCmd}' # Echo the command string (single quotes to prevent shell expansion of its content)

                        ${dockerScannerCmd} # Execute the constructed command

                        echo "Sonar scan command finished."
                        echo "Checking for report task file at host path: ${hostMetadataFilePath}..."
                        if [ ! -f "${hostMetadataFilePath}" ]; then
                            echo "ERROR: ${hostMetadataFilePath} not found after scan!"
                            echo "Listing workspace contents after scan:"
                            ls -la
                            echo "Listing .sonartmp contents (if any):"
                            ls -la .sonartmp || echo ".sonartmp directory not found or empty"
                            exit 1
                        fi
                        echo "${hostMetadataFilePath} found. Contents:"
                        cat "${hostMetadataFilePath}"
                        """
                    }
                }
            }
        }

        stage('Check Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    script {
                        def reportTaskFile = env.SONAR_METADATA_FILENAME // This is correct (host path)
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
