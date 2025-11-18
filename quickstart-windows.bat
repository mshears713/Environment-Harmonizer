@echo off
REM Environment Harmonizer - Windows Quick Start Script
REM This script helps you quickly get started with Environment Harmonizer on Windows

echo.
echo ========================================
echo Environment Harmonizer - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop for Windows:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is installed
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running
    echo.
    echo Please start Docker Desktop and try again
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

echo Building Environment Harmonizer image...
echo.
docker build -t environment-harmonizer:latest .
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build complete!
echo.
echo ========================================
echo Quick Start Options:
echo ========================================
echo.
echo 1. Scan current directory:
echo    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest
echo.
echo 2. Scan with verbose output:
echo    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --verbose
echo.
echo 3. Preview fixes:
echo    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --fix --dry-run
echo.
echo 4. Apply fixes:
echo    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --fix
echo.
echo 5. Using docker-compose:
echo    docker-compose run --rm harmonizer
echo.
echo ========================================
echo.

REM Ask user what they want to do
echo What would you like to do?
echo [1] Scan current directory
echo [2] Scan with verbose output
echo [3] Preview fixes (dry-run)
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Scanning current directory...
    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest
) else if "%choice%"=="2" (
    echo.
    echo Scanning with verbose output...
    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --verbose
) else if "%choice%"=="3" (
    echo.
    echo Previewing fixes...
    docker run --rm -v "%cd%":/workspace environment-harmonizer:latest --fix --dry-run
) else if "%choice%"=="4" (
    echo.
    echo Goodbye!
    exit /b 0
) else (
    echo.
    echo Invalid choice. Exiting.
    exit /b 1
)

echo.
echo.
echo Scan complete! For more options, see QUICKSTART.md
echo.
pause
