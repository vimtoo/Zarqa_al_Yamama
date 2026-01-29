#!/bin/bash

# ZARQA AL YAMAMA - ONE-CLICK STARTUP SCRIPT
# Run this from the project root directory.

echo "🚀 Starting Zarqa al Yamama..."

# Get the absolute path of the current directory to ensure reliable cd
PROJECT_ROOT=$(pwd)

echo "📂 Project Root: $PROJECT_ROOT"

# Function to start Backend in a new Terminal tab
start_backend() {
    echo "📦 Starting Backend Server..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_ROOT/backend' && echo 'Installing dependencies...' && pip3 install -r requirements.txt && echo 'Starting Uvicorn...' && uvicorn app.main:app --reload\""
}

# Function to start Frontend in a new Terminal tab
start_frontend() {
    echo "✨ Starting Frontend Server..."
    osascript -e "tell application \"Terminal\" to do script \"cd '$PROJECT_ROOT/frontend' && echo 'Starting Next.js...' && npm run dev\""
}

# Execute
start_backend
sleep 2 # Small delay to let backend init
start_frontend

echo "✅ Startup commands sent to new Terminal windows."
echo "🌍 Open your browser to: http://localhost:3000 (or 3001 if 3000 is taken)"
