# Environment Harmonizer - Windows PowerShell Quick Start Script
# This script helps you quickly get started with Environment Harmonizer on Windows

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment Harmonizer - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>$null
    Write-Host "[OK] Docker is installed: $dockerVersion" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Docker Desktop for Windows:"
    Write-Host "https://www.docker.com/products/docker-desktop"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Docker is running
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Host "[OK] Docker is running" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] Docker is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Docker Desktop and try again"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Build the Docker image
Write-Host "Building Environment Harmonizer image..." -ForegroundColor Yellow
Write-Host ""

try {
    docker build -t environment-harmonizer:latest .
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }
    Write-Host ""
    Write-Host "[SUCCESS] Build complete!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to build Docker image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Start Options:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Scan current directory:"
Write-Host "   docker run --rm -v `"`${PWD}:/workspace`" environment-harmonizer:latest" -ForegroundColor Blue
Write-Host ""
Write-Host "2. Scan with verbose output:"
Write-Host "   docker run --rm -v `"`${PWD}:/workspace`" environment-harmonizer:latest --verbose" -ForegroundColor Blue
Write-Host ""
Write-Host "3. Preview fixes:"
Write-Host "   docker run --rm -v `"`${PWD}:/workspace`" environment-harmonizer:latest --fix --dry-run" -ForegroundColor Blue
Write-Host ""
Write-Host "4. Apply fixes:"
Write-Host "   docker run --rm -v `"`${PWD}:/workspace`" environment-harmonizer:latest --fix" -ForegroundColor Blue
Write-Host ""
Write-Host "5. Using docker-compose:"
Write-Host "   docker-compose run --rm harmonizer" -ForegroundColor Blue
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Interactive menu
Write-Host "What would you like to do?"
Write-Host "[1] Scan current directory"
Write-Host "[2] Scan with verbose output"
Write-Host "[3] Preview fixes (dry-run)"
Write-Host "[4] Exit"
Write-Host ""
$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Scanning current directory..." -ForegroundColor Yellow
        docker run --rm -v "${PWD}:/workspace" environment-harmonizer:latest
    }
    "2" {
        Write-Host ""
        Write-Host "Scanning with verbose output..." -ForegroundColor Yellow
        docker run --rm -v "${PWD}:/workspace" environment-harmonizer:latest --verbose
    }
    "3" {
        Write-Host ""
        Write-Host "Previewing fixes..." -ForegroundColor Yellow
        docker run --rm -v "${PWD}:/workspace" environment-harmonizer:latest --fix --dry-run
    }
    "4" {
        Write-Host ""
        Write-Host "Goodbye!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host ""
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host ""
Write-Host "Scan complete! For more options, see QUICKSTART.md" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
