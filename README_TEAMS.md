# 🤖 QA Brother - Team Setup Guide

QA Brother is your AI-powered quality assurance companion that helps teams automate design and functional testing without requiring coding experience.

## 🚀 Quick Start Options (Choose One)

### Option 1: Streamlit Cloud (Recommended for Remote Teams)
**Best for:** Remote teams, no installation required, always up-to-date

1. **Deploy to Cloud:**
   - Fork this repository to your GitHub account
   - Go to [https://share.streamlit.io/](https://share.streamlit.io/)
   - Connect your GitHub and deploy `monster2.py`
   - Add your API keys in the Streamlit Cloud secrets

2. **Share with Team:**
   - Get your app URL: `https://your-app.streamlit.app`
   - Share this URL with your team members
   - Everyone can access it from any browser

**✅ Pros:** No installation, automatic updates, mobile-friendly  
**⚠️ Cons:** Requires internet, limited by cloud resources

---

### Option 2: Docker Setup (Recommended for Local Teams)
**Best for:** Local teams, more control, works offline

1. **Prerequisites:**
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Download this project to your computer

2. **One-Command Setup:**
   ```bash
   ./setup-for-teams.sh
   ```

3. **Manual Setup (if script fails):**
   ```bash
   # Copy and edit environment file
   cp .env.example .env
   # Edit .env with your API keys
   
   # Start the application
   docker-compose up -d
   
   # Access at http://localhost:8501
   ```

**✅ Pros:** Full control, works offline, better performance  
**⚠️ Cons:** Requires Docker installation, team needs local access

---

### Option 3: Simple Python Install (Recommended for Single Users)
**Best for:** Individual users, developers, testing

1. **Prerequisites:**
   - Install Python 3.9+ from [python.org](https://python.org)
   - Download this project

2. **Setup:**
   ```bash
   # Create virtual environment
   python -m venv qa_env
   
   # Activate it (Windows)
   qa_env\Scripts\activate
   # Or on Mac/Linux
   source qa_env/bin/activate
   
   # Install requirements
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your API keys
   
   # Run the app
   streamlit run monster2.py
   ```

**✅ Pros:** Full control, fastest performance  
**⚠️ Cons:** Requires technical setup, manual updates

---

## 🔑 Required API Keys

You'll need these API keys for full functionality:

### Figma (Required for Design QA)
1. Go to [Figma Settings > Account](https://www.figma.com/settings)
2. Scroll to "Personal access tokens"
3. Click "Create new token"
4. Copy the token

### OpenAI (Required for AI Analysis)
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)

### Jira (Optional - for ticket creation)
1. Go to [Atlassian Account](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the token
4. You'll also need your Jira server URL and email

---

## 👥 Team Usage Instructions

### For Non-Technical Team Members:

1. **Access the App:**
   - Use the URL provided by your admin
   - Bookmark it for easy access

2. **Design QA Testing:**
   - Copy your Figma design URL
   - Enter the live website URL
   - Choose device type (mobile/tablet/desktop)
   - Click "Start Design QA"
   - Wait for results and review the report

3. **Key Tips:**
   - Figma URLs must include `node-id=` parameter
   - Test mobile designs using mobile device emulation
   - Save frequently tested sites as presets
   - Check the "Welcome" tab for detailed guides

### For Admins/IT:

1. **Setup Monitoring:**
   - Check logs regularly: `docker-compose logs`
   - Monitor resource usage
   - Backup the `reports` folder periodically

2. **Team Management:**
   - Share the app URL securely
   - Train team on basic usage
   - Set up shared folders for reports
   - Configure Jira integration for the team

---

## 🆘 Troubleshooting

### Common Issues:

**"Could not parse Figma URL"**
- Ensure URL includes `node-id=` parameter
- Example: `https://figma.com/file/ABC123/Design?node-id=1-2`

**"Browser setup failed"**
- Restart the application
- Try different browser types in settings
- Check internet connection

**"Tests taking too long"**
- Use smaller page sections
- Disable full-page screenshots for long pages
- Ensure stable internet connection

**"App won't start"**
- Check Docker is running (for Docker setup)
- Verify API keys are correct
- Check the logs for specific error messages

### Getting Help:

1. Check the built-in "Welcome" tab for guides
2. Review the troubleshooting section in the app
3. Check application logs for error details
4. Contact your admin or IT team

---

## 🔒 Security Notes

- Keep API keys secure and never share them
- Use environment variables or secrets management
- Regularly rotate API keys
- Don't commit API keys to version control
- Use HTTPS in production deployments

---

## 📊 Features Overview

✅ **Design QA:** Compare Figma designs with live websites  
✅ **Multi-Device Testing:** Test on mobile, tablet, and desktop  
✅ **Multi-Browser Support:** Chrome, Firefox, Safari  
✅ **AI Analysis:** Get intelligent feedback on design differences  
✅ **Responsive Testing:** Animated breakpoint testing  
✅ **Video Recording:** Record test sessions for review  
✅ **Jira Integration:** Automatically create tickets for issues  
✅ **Team Friendly:** No coding required, intuitive interface  
✅ **Report Generation:** HTML/PDF reports for stakeholders  

---

## 🆕 Updates and Maintenance

### For Cloud Deployments:
- Updates happen automatically when you push to GitHub
- Monitor the Streamlit Cloud dashboard for issues

### For Docker Deployments:
```bash
# Update to latest version
git pull
docker-compose build
docker-compose up -d
```

### For Python Installs:
```bash
# Update the code
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart the app
streamlit run monster2.py
```

---

**Need help?** Check the Welcome tab in the app or contact your team administrator.
