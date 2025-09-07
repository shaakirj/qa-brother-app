# Quali - Internal QA Tool

> **Internal Development Tool** - For team use only

## 🚀 Quick Start

### Option 1: Using the startup script (Recommended)
```bash
./start-internal.sh
```

### Option 2: Manual startup
```bash
export FLASK_ENV=development
export USE_ENVOLE_THEME=1
python3 app.py
```

## 🌐 Access URLs

- **Main Application**: http://localhost:5001
- **Internal Documentation**: http://localhost:5001/internal-docs
- **Design QA**: http://localhost:5001/design-qa
- **Functional Testing**: http://localhost:5001/functional-testing
- **Analytics**: http://localhost:5001/analytics

## 🛠️ Features

### Design QA
- Compare Figma designs with live implementations
- Visual similarity scoring
- Automated diff generation
- Responsive design validation

### Functional Testing
- AI-generated test cases
- Automated test execution
- Cross-browser compatibility testing
- Jira ticket integration

### Analytics
- Team performance metrics
- Pattern detection
- Issue tracking and reporting

## ⚙️ Configuration

### Required Environment Variables
```bash
# Figma Integration
export FIGMA_ACCESS_TOKEN="your_figma_token"

# OpenAI Integration (Optional)
export OPENAI_API_KEY="your_openai_key"

# Jira Integration (Optional)
export JIRA_SERVER_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your_jira_token"
export JIRA_PROJECT_KEY="QA"
```

### Optional Environment Variables
```bash
# Theme Control
export USE_ENVOLE_THEME=1  # Enable dark theme (default: enabled)

# Flask Configuration
export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_PORT=5001
```

## 📋 Team Guidelines

### Best Practices
1. **Always test on multiple devices** - Use the mobile device options in Design QA
2. **Use descriptive Jira ticket IDs** - This helps with tracking and organization
3. **Review generated test cases** - AI-generated tests should be reviewed before execution
4. **Document custom configurations** - Keep track of any special settings you use

### Troubleshooting
- **API Issues**: Check that all required environment variables are set
- **Figma Issues**: Ensure URLs contain the `node-id` parameter
- **Web Access Issues**: Verify that target URLs are accessible from your network
- **Configuration Issues**: Contact the team lead for help with setup

## 🔧 Development

### Project Structure
```
web_app/
├── app.py                 # Main Flask application
├── run.py                 # Alternative startup script
├── start-internal.sh      # Internal startup script
├── requirements.txt       # Python dependencies
├── static/
│   └── css/
│       └── theme-envole.css  # Dark theme styles
├── templates/
│   ├── base.html         # Base template with theme
│   ├── index.html        # Homepage
│   ├── design-qa.html    # Design QA page
│   ├── functional-testing.html  # Functional testing page
│   ├── analytics.html    # Analytics page
│   └── internal-docs.html # Internal documentation
└── uploads/              # File uploads directory
```

### Adding New Features
1. Create new routes in `app.py`
2. Add corresponding templates in `templates/`
3. Update navigation in `base.html`
4. Test with the internal theme applied

## 🚨 Security Notes

- This tool is for **internal use only**
- Do not expose to public networks
- Keep API keys secure and never commit them to version control
- Use environment variables for all sensitive configuration

## 📞 Support

For issues or questions:
1. Check the internal documentation at `/internal-docs`
2. Review this README
3. Contact the development team lead

---

**Version**: 1.0.0-internal  
**Environment**: Development  
**Last Updated**: September 2024
