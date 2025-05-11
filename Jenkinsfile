pipeline {
    agent any // Runs on any available Jenkins agent (which is Windows in your case)

    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
        APP_PORT = 5001
        // Windows-friendly path
        DEPLOY_PATH = "C:/JenkinsDeploy/my-gemini-app" // Or C:\\JenkinsDeploy\\my-gemini-app
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                // The initial checkout is handled by Jenkins SCM configuration.
                // This explicit checkout here is usually redundant if "Pipeline script from SCM" is used.
                // If you want to ensure a clean workspace or specific branch beyond what SCM config does:
                // cleanWs() // Optional: clean workspace before checkout
                checkout scm
            }
        }

        stage('Setup Environment & Install Dependencies') {
            steps {
                echo 'Setting up Python virtual environment and installing dependencies...'
                // Create the deployment directory if it doesn't exist
                bat "if not exist \"${env.DEPLOY_PATH}\" mkdir \"${env.DEPLOY_PATH}\""

                // Copy application files to the deployment path
                // Using robocopy for more robust copying than xcopy
                // /E :: copy subdirectories, including Empty ones.
                // /XO :: eXclude Older files.
                // /XF Jenkinsfile :: eXclude specific Files
                // /XD .git venv :: eXclude specific Directories
                // /NFL :: No File List - don't log file names.
                // /NDL :: No Directory List - don't log directory names.
                // /NJH :: No Job Header.
                // /NJS :: No Job Summary.
                // The exit code of robocopy can be tricky (0-7 are success).
                // We wrap it to ensure Jenkins doesn't fail on "successful" copies with warnings.
                bat """
                    robocopy . "${env.DEPLOY_PATH}" /E /XO /XF Jenkinsfile /XD .git venv /NFL /NDL /NJH /NJS
                    if %ERRORLEVEL% GEQ 8 (
                        exit /b %ERRORLEVEL%
                    ) else (
                        exit /b 0
                    )
                """

                dir("${env.DEPLOY_PATH}") { // Change directory for the following commands
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
                        echo --- Listing files in current directory ---
                        dir /b
                        echo --- Checking for main.py ---
                        if exist main.py (
                            echo main.py found.
                        ) else (
                            echo ERROR: main.py NOT FOUND in %CD%
                            exit /b 1
                        )

                        echo --- Checking for venv python.exe ---
                        if exist .\\venv\\Scripts\\python.exe (
                            echo venv python.exe found.
                        ) else (
                            echo ERROR: .\\venv\\Scripts\\python.exe NOT FOUND
                            exit /b 1
                        )

                        echo Stopping any old running application on port ${env.APP_PORT}...
                        for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%APP_PORT%" ^| findstr "LISTENING"') do (
                            if "%%a" NEQ "0" (
                                echo Found process with PID %%a on port %APP_PORT%. Terminating...
                                taskkill /F /PID %%a
                            )
                        )

                        echo Starting application...
                        set PORT=${env.APP_PORT}
                        
                        echo --- Activating venv and checking python version ---
                        call .\\venv\\Scripts\\activate.bat
                        echo Python version from venv:
                        python --version
                        echo Which python:
                        where python
                        
                        echo Starting python main.py on port %PORT%
                        REM Start in background, redirect output. Try specifying full path to venv python
                        echo Attempting to start: .\\venv\\Scripts\\python.exe main.py
                        start "GeminiApp" /B .\\venv\\Scripts\\python.exe main.py > app.log 2>&1
                        
                        call .\\venv\\Scripts\\deactivate.bat
                        
                        REM Add a small delay to see if app.log gets created
                        timeout /t 5 /nobreak > NUL

                        echo --- Checking app.log ---
                        if exist app.log (
                            echo app.log found. Contents:
                            type app.log
                        ) else (
                            echo app.log NOT found. The application might not have started correctly.
                        )
                        echo Application deployment script finished.
                    """
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