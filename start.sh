#!/bin/bash

# Function to handle shutdown
cleanup() {
    echo ""
    echo "Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID
    fi
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT SIGTERM

echo "========================================"
echo "Etihad Rail Monitoring - Starting"
echo "========================================"

# Start Backend
echo "Starting Backend (Port 8004)..."
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8004 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo ""
echo "Dashboard is running at:"
echo "  Local:   http://localhost:5175/"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for processes
wait
