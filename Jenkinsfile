pipeline {
    agent any 

    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
        APP_PORT = 5001
        DEPLOY_PATH = "/opt/my-gemini-app" 
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }

        stage('Setup Environment & Install Dependencies') {
            steps {
                echo 'Setting up Python virtual environment and installing dependencies...'
                sh "mkdir -p ${env.DEPLOY_PATH}"
                sh "rsync -av --exclude='.git' --exclude='venv/' ./ ${env.DEPLOY_PATH}/"

                dir("${env.DEPLOY_PATH}") { 
                    sh '''
                        # Remove old venv if it exists, to ensure a clean environment
                        if [ -d "venv" ]; then
                            echo "Removing old virtual environment..."
                            rm -rf venv
                        fi
                        echo "Creating new virtual environment..."
                        python3 -m venv venv
                        echo "Activating virtual environment and installing requirements..."
                        source venv/bin/activate
                        pip install -r requirements.txt
                        deactivate
                    '''
                }
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying application on port ${env.APP_PORT}..."
                dir("${env.DEPLOY_PATH}") {
                    sh """
                        echo 'Stopping any old running application on port ${env.APP_PORT}...'
                        # Try to kill process using the port. '|| true' prevents failure if nothing is running.
                        fuser -k ${env.APP_PORT}/tcp || true

                        echo 'Starting application...'
                        # Activate venv and run the app in the background
                        # Redirect output to a log file
                        # GEMINI_API_KEY is already in the environment from Jenkins
                        # PORT environment variable will be used by main.py
                        export PORT=${env.APP_PORT}
                        source venv/bin/activate
                        nohup python main.py > app.log 2>&1 &
                        deactivate
                        echo "Application started. Check app.log in ${env.DEPLOY_PATH} for logs."
                        echo "Access at: http://<your-jenkins-server-ip>:${env.APP_PORT}"
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo 'Application deployed successfully!'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}