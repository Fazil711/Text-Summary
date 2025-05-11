pipeline {
    agent any

    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
        APP_PORT = 5001 // Ensure this is the port you want
        DEPLOY_PATH = "C:/JenkinsDeploy/my-gemini-app"
        // Define a simple health check endpoint in your Flask app if you don't have one
        HEALTH_CHECK_URL = "http://localhost:${APP_PORT}/" // Change to /health or similar if you add one
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
                bat "if not exist \"${env.DEPLOY_PATH}\" mkdir \"${env.DEPLOY_PATH}\""
                bat """
                    robocopy . "${env.DEPLOY_PATH}" /E /XO /XF Jenkinsfile /XD .git venv /NFL /NDL /NJH /NJS
                    if %ERRORLEVEL% GEQ 8 (
                        exit /b %ERRORLEVEL%
                    ) else (
                        exit /b 0
                    )
                """
                dir("${env.DEPLOY_PATH}") {
                    bat '''
                        @echo off
                        echo Checking for old virtual environment...
                        if exist "venv" (
                            echo Removing old virtual environment...
                            rd /s /q venv
                        )
                        echo Creating new virtual environment...
                        python -m venv venv
                        echo Activating virtual environment and installing requirements...
                        call .\\venv\\Scripts\\activate.bat
                        pip install -r requirements.txt
                        call .\\venv\\Scripts\\deactivate.bat
                        echo Setup complete.
                    '''
                }
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Deploying application on port ${env.APP_PORT}..."
                dir("${env.DEPLOY_PATH}") {
                    bat """
                        @echo off
                        echo Current directory: %CD%
                        
                        echo Stopping any old running application on port ${env.APP_PORT}...
                        for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%APP_PORT%" ^| findstr "LISTENING"') do (
                            if "%%a" NEQ "0" (
                                echo Found process with PID %%a on port %APP_PORT%. Terminating...
                                taskkill /F /PID %%a
                            )
                        )

                        echo Starting application...
                        set PORT=${env.APP_PORT}  REM <--- THIS IS THE CRITICAL FIX: SET PORT HERE
                        
                        echo --- Activating venv ---
                        call .\\venv\\Scripts\\activate.bat
                        
                        echo Will attempt to start python main.py on port %PORT%
                        
                        REM Create a temporary batch file to launch python
                        echo @echo off > run_app.bat
                        echo echo Running run_app.bat... >> run_app.bat
                        REM Ensure PORT is explicitly passed to the environment of the script if needed,
                        REM or ensure the python script reads it correctly.
                        REM Here, %PORT% will expand to the value set in the parent script.
                        echo set PORT=%PORT% >> run_app.bat 
                        echo echo PORT set in run_app.bat to: %PORT% >> run_app.bat
                        echo echo GEMINI_API_KEY from run_app.bat: %GEMINI_API_KEY% >> run_app.bat
                        echo echo --- Starting Python Script --- >> run_app.bat
                        echo .\\venv\\Scripts\\python.exe -u main.py >> run_app.bat
                        echo echo --- Python Script Ended or Backgrounded --- >> run_app.bat
                        echo exit /b 0 >> run_app.bat 
                        
                        REM Start the temporary batch file in the background, redirecting its output
                        echo --- Executing: start "GeminiApp" /B cmd /c "run_app.bat > app.log 2>&1" ---
                        start "GeminiApp" /B cmd /c "run_app.bat > app.log 2>&1"
                        
                        call .\\venv\\Scripts\\deactivate.bat
                        
                        echo Application launch command issued. Waiting a few seconds for logs to appear...
                        ping -n 6 127.0.0.1 > NUL 

                        echo --- Checking app.log ---
                        if exist app.log (
                            echo app.log found. Contents:
                            type app.log
                        ) else (
                            echo app.log NOT found.
                        )
                        echo Application deployment script finished.
                    """
                }
            }
        }

        stage('Post-Deployment Verification') {
            steps {
                echo "Verifying deployment at ${env.HEALTH_CHECK_URL}..."
                // Give the app a little more time to be fully up before curling
                script {
                    sleep(time: 10, unit: 'SECONDS')
                }
                bat "curl -s -f ${env.HEALTH_CHECK_URL} || exit 1"
                // -f makes curl fail fast with an error code if HTTP error (4xx, 5xx)
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