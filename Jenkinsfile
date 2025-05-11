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

                        echo Stopping any old running application on port ${env.APP_PORT}...
                        for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%APP_PORT%" ^| findstr "LISTENING"') do (
                            if "%%a" NEQ "0" (
                                echo Found process with PID %%a on port %APP_PORT%. Terminating...
                                taskkill /F /PID %%a
                            )
                        )

                        echo Starting application...
                        
                        echo --- Activating venv (for context of run_app.bat creation if needed, though PORT is set in run_app.bat now) ---
                        call .\\venv\\Scripts\\activate.bat
                        
                        echo Starting python main.py on port %PORT%
                        
                        REM Create a temporary batch file to launch python
                        echo @echo off > run_app.bat
                        echo echo Running run_app.bat... >> run_app.bat
                        echo echo PORT from run_app.bat: %PORT% >> run_app.bat
                        echo echo GEMINI_API_KEY from run_app.bat: %GEMINI_API_KEY% >> run_app.bat
                        echo echo --- Starting Python Script --- >> run_app.bat
                        REM Use python -u for unbuffered output
                        echo .\\venv\\Scripts\\python.exe -u main.py >> run_app.bat
                        REM Add a small pause within run_app.bat AFTER python starts, if it's a quick crash, this might let logs flush
                        REM echo ping -n 3 127.0.0.1 ^> NUL >> run_app.bat
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
                echo 'Verifying deployment...'
                // Here you can add any verification steps, like checking if the application is running
                // For example, using curl or a simple HTTP request to check if the app is responding
                bat "curl -s http://localhost:${env.APP_PORT}/health || exit 1"
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