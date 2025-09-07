#!/bin/bash

# Quali Internal QA Tool - Startup Script
# This script starts the internal QA tool for development team use

echo "🚀 Starting Quali Internal QA Tool..."
echo "=================================="

# Set environment variables for internal use
export FLASK_ENV=development
export USE_ENVOLE_THEME=1

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the web_app directory"
    exit 1
fi

# Create necessary directories
mkdir -p uploads reports static/css templates

echo "📁 Directories created/verified"
echo "🎨 Envolve theme enabled"
echo "🔧 Development mode activated"
echo ""

# Start the application
echo "🌐 Starting Flask application..."
echo "📍 Access the tool at: http://localhost:5001"
echo "📚 Internal docs: http://localhost:5001/internal-docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

python3 app.py
