#!/bin/bash

# QA Brother - One-Click Setup for Teams
# This script sets up QA Brother for your team

echo "🚀 Setting up QA Brother for your team..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "📥 Download: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install it."
    exit 1
fi

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cat > .env << EOF
# QA Brother Configuration
FIGMA_ACCESS_TOKEN=your_figma_token_here
JIRA_API_TOKEN=your_jira_token_here
OPENAI_API_KEY=your_openai_key_here
JIRA_SERVER_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_PROJECT_KEY=QA
EOF
    
    echo "⚙️  Please edit .env file with your actual API keys and configuration"
    echo "📖 See README.md for instructions on obtaining API keys"
    read -p "Press Enter after you've updated the .env file..."
fi

# Create necessary directories
mkdir -p reports uploads

# Build and start the application
echo "🔨 Building QA Brother container..."
docker-compose build

echo "🚀 Starting QA Brother..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ QA Brother is running successfully!"
    echo "🌐 Access the application at: http://localhost:8501"
    echo ""
    echo "📖 Team Instructions:"
    echo "   1. Share this URL with your team: http://localhost:8501"
    echo "   2. Team members can access it from any browser"
    echo "   3. To stop: docker-compose down"
    echo "   4. To restart: docker-compose up -d"
    echo "   5. To update: git pull && docker-compose build && docker-compose up -d"
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
fi
