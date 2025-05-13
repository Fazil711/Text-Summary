pipeline {
    agent any

    stages {
        stage('Clone') {
            steps {
                git branch: 'docker-deploy', url: 'https://github.com/Fazil711/Text-Summary.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("text-summary-app")
                }
            }
        }

        stage('Run Container') {
            steps {
                script {
                    // Stop any existing container
                    sh "docker rm -f text-summary-container || true"

                    // Run new container
                    sh "docker run -d --name text-summary-container -p 5000:5000 text-summary-app"
                }
            }
        }
    }
}


