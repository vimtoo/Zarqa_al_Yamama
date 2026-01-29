#!/bin/bash

# Zarqa al Yamama - Setup Script

echo "=================================================="
echo "    Zarqa al Yamama - Installation & Setup"
echo "=================================================="

# 1. Backend Setup
echo ""
echo "[1/2] Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    # Strict Python 3.11 Enforcement
    PYTHON_CMD="python3.11"
    if ! command -v $PYTHON_CMD &> /dev/null; then
        # Fallback: Check if python3 is 3.11
        if command -v python3 &> /dev/null && [ "$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == "3.11" ]; then
            PYTHON_CMD="python3"
        else
            echo "❌ ERROR: Python 3.11 is strictly required."
            echo "   Found: $(python3 --version 2>/dev/null || 'None')"
            echo "   Please install Python 3.11 to proceed."
            exit 1
        fi
    fi
    echo "Creating Python virtual environment using $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env configuration..."
    cp .env.example .env
else
    echo ".env file already exists."
fi

echo "Backend setup complete."

# 2. Frontend Setup
echo ""
echo "[2/2] Setting up Frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node modules (this may take a minute)..."
    npm install
else
    echo "Node modules already installed."
fi

echo "Frontend setup complete."

# 3. Final Instructions
echo ""
echo "=================================================="
echo "    Setup Finished Successfully! 🚀"
echo "=================================================="
echo ""
echo "To run the application, open TWO terminal tabs:"
echo ""
echo "TAB 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "TAB 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Access the app at: http://localhost:3000"
echo "=================================================="
