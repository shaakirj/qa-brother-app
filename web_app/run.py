#!/usr/bin/env python3
"""
Quali - AI Quality Assurance Buddy
Web Application Startup Script
"""

import os
import sys
import logging
from pathlib import Path

# Ensure we import the Flask app from this folder (web_app)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'FIGMA_ACCESS_TOKEN',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("Some features may not work properly without these variables.")
    
    # Optional but recommended variables
    optional_vars = [
        'JIRA_SERVER_URL',
        'JIRA_EMAIL',
        'JIRA_API_TOKEN',
        'JIRA_PROJECT_KEY',
        'GROQ_API_KEY'
    ]
    
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    if missing_optional:
        logger.info(f"Optional environment variables not set: {missing_optional}")
        logger.info("These features will be disabled: Jira integration, Groq AI")

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'reports', 'static', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def main():
    """Main startup function"""
    logger.info("Starting Quali - AI Quality Assurance Buddy")
    
    # Check environment
    check_environment()
    
    # Create directories
    create_directories()
    
    # Import and run Flask app
    try:
        from app import app
        logger.info("Flask app imported successfully")

        # Run the application
        app.run(
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 5001))
        )
    except ImportError as e:
        logger.error(f"Failed to import Flask app: {e}")
        logger.error("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()






