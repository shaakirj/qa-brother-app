#!/bin/bash

# Quali - AI Quality Assurance Buddy
# Startup script for the web application

echo "🤖 Starting Quali - AI Quality Assurance Buddy"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Check environment variables
echo "🔍 Checking environment variables..."
if [ -z "$FIGMA_ACCESS_TOKEN" ]; then
    echo "⚠️  FIGMA_ACCESS_TOKEN not set. Some features may not work."
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. AI features will be disabled."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads reports static templates

# Start the application
echo "🚀 Starting Quali web application..."
echo "   Access the application at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

python run.py






