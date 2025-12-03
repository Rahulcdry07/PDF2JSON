#!/bin/bash
# Quick start script for PDF2JSON DSR System

set -e

echo "======================================"
echo "PDF2JSON DSR System - Quick Start"
echo "======================================"
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✓ Docker and Docker Compose detected"
    echo ""
    echo "Choose deployment method:"
    echo "1) Docker (Recommended)"
    echo "2) Local Python environment"
    read -p "Enter choice (1 or 2): " choice
    
    if [ "$choice" == "1" ]; then
        echo ""
        echo "Starting services with Docker..."
        echo ""
        
        # Create .env if it doesn't exist
        if [ ! -f .env ]; then
            echo "Creating .env file..."
            cp .env.example .env
        fi
        
        # Build and start services
        docker-compose up -d
        
        echo ""
        echo "✓ Services started successfully!"
        echo ""
        echo "Access the applications:"
        echo "  - Main Web Interface: http://localhost:8000"
        echo "  - MCP Web Interface:  http://localhost:5001"
        echo ""
        echo "View logs with: docker-compose logs -f"
        echo "Stop services with: docker-compose down"
        exit 0
    fi
fi

# Local Python setup
echo ""
echo "Setting up local Python environment..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null

echo ""
echo "✓ Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Activate environment: source .venv/bin/activate"
echo "  2. Start main web:    python -m src.pdf2json.web"
echo "  3. Start MCP web:     python mcp_web_interface.py"
echo "  4. Start DB manager:  python database_manager.py"
echo ""
echo "Or use Docker: docker-compose up -d"
echo "Run tests with: pytest tests/"
echo ""
