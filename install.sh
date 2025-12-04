#!/bin/bash
set -e

echo "========================================"
echo "Etihad Rail Monitoring - Installation"
echo "========================================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: node is not installed."
    exit 1
fi

# Backend Setup
echo ""
echo "[1/2] Setting up Backend..."
cd backend

# Check/Install uv
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "Installing backend dependencies..."
uv sync

cd ..

# Frontend Setup
echo ""
echo "[2/2] Setting up Frontend..."
cd frontend
echo "Installing frontend dependencies..."
npm install
cd ..

echo ""
echo "========================================"
echo "Installation Complete!"
echo "Run ./start.sh to launch the dashboard."
echo "========================================"
