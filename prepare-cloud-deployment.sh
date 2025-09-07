#!/bin/bash

# QA Brother - Streamlit Cloud Deployment Preparation Script

echo "🚀 Preparing QA Brother for Streamlit Cloud deployment..."

# Create .gitignore for sensitive files
cat > .gitignore << EOF
# Environment and secrets
.env
*.env
.streamlit/secrets.toml
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Local development
qa_env/
.vscode/
.DS_Store
*.log

# Reports and uploads (too large for git)
reports/
uploads/
*.webm
*.mp4
*.gif

# Temporary files
*.tmp
temp/
EOF

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
fi

# Create a clean commit
echo "📦 Staging files for deployment..."
git add .
git status

echo "✅ Repository prepared for Streamlit Cloud!"
echo ""
echo "🔄 Next Steps:"
echo "1. Commit your changes: git commit -m 'Prepare QA Brother for Streamlit Cloud'"
echo "2. Push to GitHub: git push origin main"
echo "3. Go to https://share.streamlit.io and deploy!"
echo ""
echo "📋 Don't forget to:"
echo "   - Add your API keys to Streamlit Cloud secrets"
echo "   - Use requirements-cloud.txt as your requirements file"
echo "   - Set monster2.py as your main file"
