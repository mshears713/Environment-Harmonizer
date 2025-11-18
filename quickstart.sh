#!/bin/bash
# Environment Harmonizer - Quick Start Script for Linux/WSL/macOS
# This script helps you quickly get started with Environment Harmonizer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "Environment Harmonizer - Quick Start"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed or not in PATH"
    echo ""
    echo "Please install Docker:"
    echo "  - Ubuntu/Debian: https://docs.docker.com/engine/install/ubuntu/"
    echo "  - WSL: https://docs.docker.com/desktop/windows/wsl/"
    echo "  - macOS: https://docs.docker.com/desktop/mac/install/"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker is installed"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not running"
    echo ""
    echo "Please start Docker and try again"
    echo "  - Linux/WSL: sudo systemctl start docker"
    echo "  - macOS: Start Docker Desktop"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker is running"
echo ""

# Build the Docker image
echo "Building Environment Harmonizer image..."
echo ""
if docker build -t environment-harmonizer:latest .; then
    echo ""
    echo -e "${GREEN}[SUCCESS]${NC} Build complete!"
else
    echo ""
    echo -e "${RED}[ERROR]${NC} Failed to build Docker image"
    exit 1
fi

echo ""
echo "========================================"
echo "Quick Start Options:"
echo "========================================"
echo ""
echo "1. Scan current directory:"
echo -e "   ${BLUE}docker run --rm -v \"\$(pwd)\":/workspace environment-harmonizer:latest${NC}"
echo ""
echo "2. Scan with verbose output:"
echo -e "   ${BLUE}docker run --rm -v \"\$(pwd)\":/workspace environment-harmonizer:latest --verbose${NC}"
echo ""
echo "3. Preview fixes:"
echo -e "   ${BLUE}docker run --rm -v \"\$(pwd)\":/workspace environment-harmonizer:latest --fix --dry-run${NC}"
echo ""
echo "4. Apply fixes:"
echo -e "   ${BLUE}docker run --rm -v \"\$(pwd)\":/workspace environment-harmonizer:latest --fix${NC}"
echo ""
echo "5. Using docker-compose:"
echo -e "   ${BLUE}docker-compose run --rm harmonizer${NC}"
echo ""
echo "6. Interactive shell:"
echo -e "   ${BLUE}docker run --rm -it -v \"\$(pwd)\":/workspace environment-harmonizer:latest /bin/bash${NC}"
echo ""
echo "========================================"
echo ""

# Interactive menu
echo "What would you like to do?"
echo "[1] Scan current directory"
echo "[2] Scan with verbose output"
echo "[3] Preview fixes (dry-run)"
echo "[4] Exit"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Scanning current directory..."
        docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest
        ;;
    2)
        echo ""
        echo "Scanning with verbose output..."
        docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --verbose
        ;;
    3)
        echo ""
        echo "Previewing fixes..."
        docker run --rm -v "$(pwd)":/workspace environment-harmonizer:latest --fix --dry-run
        ;;
    4)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}Invalid choice.${NC} Exiting."
        exit 1
        ;;
esac

echo ""
echo ""
echo "Scan complete! For more options, see QUICKSTART.md"
echo ""
