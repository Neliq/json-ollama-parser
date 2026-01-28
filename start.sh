#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting AI Product Parser Stack..."

# 1. Check/Start Ollama
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 5 # Wait for Ollama to initialize
else
    echo "Ollama is already running."
fi

# Ensure Mistral model is available
echo "Checking for Mistral model..."
ollama pull mistral || true

# 2. Start Backend
echo "Starting Backend (FastAPI)..."
source ./venv/bin/activate
cd /home/neliq/Coding/json-ollama-parser
nohup python api.py > api.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID), logs in api.log"

# 3. Start Frontend
echo "Starting Frontend (Next.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend running (PID: $FRONTEND_PID)"

echo "------------------------------------------------"
echo "Full stack is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop everything."
echo "------------------------------------------------"

# Wait for any process to exit
wait -n
