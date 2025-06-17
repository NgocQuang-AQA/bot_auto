@echo off
REM Build Docker Image for Bot Slack Service
REM This script builds the Docker image for the bot-slack application

echo Building Docker image for Bot Slack Service...
echo.

REM Check if Docker is running
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running!
    echo Please make sure Docker Desktop is installed and running.
    pause
    exit /b 1
)

echo Docker is available. Starting build process...
echo.

REM Build the Docker image
echo Building image: bot-slack:latest
docker build -t bot-slack:latest -f deployment\Dockerfile .

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Docker image built successfully!
    echo Image name: bot-slack:latest
    echo.
    echo You can now run the container with:
    echo docker run -d -p 5000:5000 --name bot-slack-container bot-slack:latest
    echo.
    echo Or use docker-compose:
    echo docker-compose -f deployment\docker-compose.yml up -d
) else (
    echo.
    echo ERROR: Failed to build Docker image!
    echo Please check the error messages above.
)

echo.
echo Available Docker images:
docker images | findstr bot-slack

echo.
pause