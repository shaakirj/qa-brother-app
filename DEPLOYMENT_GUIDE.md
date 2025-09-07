# Streamlit Cloud Deployment Guide

## Prerequisites
1. GitHub repository with your QA Brother code
2. Streamlit Cloud account (free)

## Steps to Deploy:

### 1. Prepare Repository
- Push your working monster2.py and design8.py to GitHub
- Ensure requirements.txt is complete
- Add secrets for API keys

### 2. Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Connect your GitHub account
3. Select repository and main file (monster2.py)
4. Add secrets in the dashboard for:
   - FIGMA_ACCESS_TOKEN
   - JIRA_API_TOKEN
   - OPENAI_API_KEY
   - etc.

### 3. Share with Team
- Get the public URL (e.g., https://your-app.streamlit.app)
- Team members just need the link - no installation required
- Works on any device with a web browser

## Benefits:
✅ Zero technical setup for users
✅ Always up-to-date
✅ Mobile-friendly
✅ Free hosting
✅ Built-in authentication options
✅ Easy updates via Git push

## Limitations:
⚠️ Public by default (can upgrade for private apps)
⚠️ Limited to Streamlit community cloud resources
⚠️ Need to manage secrets carefully
