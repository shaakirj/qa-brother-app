# Quali - Your AI Quality Assurance Buddy

A modern, beautiful web application that transforms your existing Streamlit-based QA system into a professional web platform inspired by TestSprite's design.

## 🚀 Features

### ✅ **Design QA**
- **Visual Regression Testing**: Compare Figma designs with live implementations
- **AI-Powered Analysis**: Advanced computer vision and similarity scoring
- **Multi-Device Testing**: Desktop, mobile, and tablet support
- **Real-time Progress Tracking**: Beautiful animated progress indicators
- **Jira Integration**: Automatic ticket creation for detected issues

### ✅ **Functional Testing**
- **AI-Generated Test Cases**: Create comprehensive test suites from requirements
- **Automated Test Execution**: Playwright-powered browser automation
- **User Story Generation**: Convert UX documents into actionable user stories
- **Screenshot Capture**: Visual evidence for failed tests
- **Jira Integration**: Automatic bug ticket creation

### ✅ **Analytics & Insights**
- **Performance Metrics**: Track test success rates, issues detected, time saved
- **Pattern Detection**: Identify recurring issue patterns
- **Fluid Breakpoints**: Generate responsive design animations
- **Real-time Dashboard**: Live updates and comprehensive reporting
- **Export Capabilities**: PDF, Excel, and CSV report generation

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **AI Integration**: OpenAI GPT, Computer Vision
- **Browser Automation**: Playwright
- **Design Integration**: Figma API
- **Issue Tracking**: Jira API
- **Image Processing**: Pillow, scikit-image, OpenCV

## 📋 Prerequisites

- Python 3.9+
- Node.js (for Playwright browsers)
- Figma Access Token
- OpenAI API Key
- Jira Credentials (optional)

## 🚀 Quick Start

### 1. **Navigate to the Web App Directory**
```bash
cd web_app
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Install Playwright Browsers**
```bash
playwright install
```

### 4. **Configure Environment Variables**
Copy the environment template and fill in your credentials:
```bash
cp env_template.txt .env
```

Edit `.env` with your actual values:
```env
OPENAI_API_KEY="your_openai_api_key_here"
FIGMA_ACCESS_TOKEN="your_figma_access_token_here"
JIRA_SERVER_URL="https://your-company.atlassian.net"
JIRA_EMAIL="your-jira-email@example.com"
JIRA_API_TOKEN="your_jira_api_token_here"
JIRA_PROJECT_KEY="YOURPROJECT"
```

### 5. **Start the Application**
```bash
python3 app.py
```

The application will be available at: **http://localhost:8000**

## 🎯 Usage

### **Design QA**
1. Navigate to the Design QA page
2. Enter your Figma design URL (must contain node-id)
3. Enter your web implementation URL
4. Configure similarity threshold and device type
5. Click "Start Analysis" and watch the real-time progress
6. Review results, view comparison images, and check Jira tickets

### **Functional Testing**
1. Navigate to the Functional Testing page
2. Provide Figma design URL and web URL
3. Enter Jira ticket ID for requirements
4. Optionally upload UX documents
5. Click "Start Testing" to generate and execute tests
6. Review test results, user stories, and created tickets

### **Analytics**
1. Navigate to the Analytics page
2. View real-time performance metrics
3. Generate fluid breakpoint animations
4. Analyze pattern detection results
5. Export comprehensive reports

## 🔧 API Endpoints

- `GET /` - Main dashboard
- `GET /design-qa` - Design QA page
- `GET /functional-testing` - Functional testing page
- `GET /analytics` - Analytics dashboard
- `POST /api/design-qa/analyze` - Design QA analysis
- `POST /api/functional-testing/run` - Functional testing
- `POST /api/fluid-breakpoints` - Generate breakpoint animations
- `GET /api/analytics/metrics` - Get performance metrics
- `GET /api/analytics/patterns` - Get pattern detection results
- `GET /api/health` - Health check

## 🎨 Design Features

- **TestSprite-Inspired UI**: Modern, professional design
- **Glassmorphism Effects**: Beautiful translucent elements
- **Responsive Design**: Works perfectly on all devices
- **Real-time Animations**: Smooth progress tracking and transitions
- **Dark/Light Theme**: Automatic theme detection
- **Mobile-First**: Optimized for mobile and tablet use

## 🔒 Security

- Environment variable configuration
- Secure file upload handling
- Input validation and sanitization
- Error handling and logging

## 📊 Performance

- **Fast Loading**: Optimized assets and lazy loading
- **Real-time Updates**: Live progress tracking
- **Efficient API**: RESTful endpoints with proper error handling
- **Scalable Architecture**: Easy to extend and maintain

## 🐛 Troubleshooting

### **Common Issues**

1. **Port 5000 in use**: The app runs on port 8000 by default
2. **Import errors**: Ensure all dependencies are installed
3. **API key issues**: Check your environment variables
4. **Playwright errors**: Run `playwright install`

### **Debug Mode**
The app runs in debug mode by default. Check the console for detailed error messages.

## 🚀 Deployment

### **Production Deployment**
1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server like Gunicorn
3. Configure proper logging and monitoring
4. Set up SSL certificates
5. Use a reverse proxy like Nginx

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

## 📈 Future Enhancements

- [ ] User authentication and session management
- [ ] Team collaboration features
- [ ] Advanced reporting and dashboards
- [ ] Integration with more design tools
- [ ] Machine learning model improvements
- [ ] Real-time notifications
- [ ] API rate limiting and caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

---

**Built with ❤️ for Quality Assurance Teams**

*Transform your QA process with AI-powered automation and beautiful design.*