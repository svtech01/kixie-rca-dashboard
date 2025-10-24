#!/bin/bash

# Kixie Powerlist RCA Dashboard - Quick Start Script

echo "🚀 Starting Kixie Powerlist RCA Dashboard..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/pyvenv.cfg" ] || [ ! -d ".venv/lib" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements-simple.txt
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment file..."
    cp env.example .env
    echo "✅ Environment file created. Please edit .env if needed."
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Start the application
echo "🌟 Starting Flask application..."
echo "📍 Dashboard will be available at: http://localhost:5004"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

python run.py
