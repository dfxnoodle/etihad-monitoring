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
echo "Starting Backend (Unix Socket)..."
cd backend
# Remove existing socket if present
rm -f /tmp/etihad-monitoring.sock
uv run uvicorn main:app --uds /tmp/etihad-monitoring.sock &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize and set permissions
sleep 2
chmod 666 /tmp/etihad-monitoring.sock

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev -- --host --port 5175 &
FRONTEND_PID=$!
cd ..

echo ""
echo "Dashboard is running at:"
echo "  Local:   http://localhost:5175/"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for processes
wait
