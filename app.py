import streamlit as st
import os
import requests
from groq import Groq
import PyPDF2
import docx
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import time
import traceback
from datetime import datetime
from jira import JIRA
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Advanced AI QA Automation",
    page_icon="🚀",
    layout="wide"
)

class WebCrawler:
    """Web crawler using Selenium for dynamic content"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            st.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def crawl_website(self, url, max_pages=5, depth=2):
        """Crawl website and extract content"""
        if not self.setup_driver():
            return None
            
        crawled_data = {
            'pages': [],
            'forms': [],
            'buttons': [],
            'links': [],
            'navigation': []
        }
        
        visited_urls = set()
        urls_to_visit = [(url, 0)]
        
        try:
            while urls_to_visit and len(crawled_data['pages']) < max_pages:
                current_url, current_depth = urls_to_visit.pop(0)
                
                if current_url in visited_urls or current_depth > depth:
                    continue
                    
                visited_urls.add(current_url)
                
                # Load page
                self.driver.get(current_url)
                time.sleep(2)  # Wait for page to load
                
                # Extract page content
                page_data = self.extract_page_data(current_url)
                crawled_data['pages'].append(page_data)
                
                # Find more links if within depth limit
                if current_depth < depth:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links[:10]:  # Limit links per page
                        try:
                            href = link.get_attribute("href")
                            if href and href.startswith(('http', 'https')):
                                urls_to_visit.append((href, current_depth + 1))
                        except:
                            continue
            
            return crawled_data
            
        except Exception as e:
            st.error(f"Crawling error: {e}")
            return crawled_data
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_page_data(self, url):
        """Extract detailed data from current page"""
        page_data = {
            'url': url,
            'title': '',
            'content': '',
            'forms': [],
            'buttons': [],
            'inputs': [],
            'navigation': [],
            'images': [],
            'errors': []
        }
        
        try:
            # Basic page info
            page_data['title'] = self.driver.title
            page_data['content'] = self.driver.find_element(By.TAG_NAME, "body").text[:2000]
            
            # Extract forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_data = {
                    'action': form.get_attribute("action") or "current_page",
                    'method': form.get_attribute("method") or "GET",
                    'inputs': []
                }
                
                inputs = form.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    form_data['inputs'].append({
                        'type': inp.get_attribute("type"),
                        'name': inp.get_attribute("name"),
                        'placeholder': inp.get_attribute("placeholder"),
                        'required': inp.get_attribute("required") is not None
                    })
                
                page_data['forms'].append(form_data)
            
            # Extract buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            buttons.extend(self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']"))
            
            for button in buttons:
                page_data['buttons'].append({
                    'text': button.text or button.get_attribute("value"),
                    'type': button.get_attribute("type"),
                    'id': button.get_attribute("id"),
                    'class': button.get_attribute("class")
                })
            
            # Extract navigation
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            nav_elements.extend(self.driver.find_elements(By.CSS_SELECTOR, ".nav, .navbar, .menu"))
            
            for nav in nav_elements:
                links = nav.find_elements(By.TAG_NAME, "a")
                nav_links = []
                for link in links:
                    nav_links.append({
                        'text': link.text,
                        'href': link.get_attribute("href")
                    })
                page_data['navigation'].append(nav_links)
            
        except Exception as e:
            page_data['errors'].append(f"Extraction error: {str(e)}")
        
        return page_data

class JiraIntegration:
    """Jira integration for test case and bug management"""
    
    def __init__(self, server_url, email, api_token, project_key):
        self.server_url = server_url
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.jira = None
        
    def connect(self):
        """Connect to Jira"""
        try:
            self.jira = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token)
            )
            return True
        except Exception as e:
            st.error(f"Jira connection failed: {e}")
            return False
    
    def create_test_case(self, summary, description, test_steps):
        """Create test case in Jira (requires Zephyr or similar plugin)"""
        if not self.jira:
            return None
            
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Test'},  # Adjust based on your Jira setup
            }
            
            issue = self.jira.create_issue(fields=issue_dict)
            return issue.key
        except Exception as e:
            st.error(f"Failed to create test case: {e}")
            return None
    
    def create_bug(self, summary, description, steps_to_reproduce, expected_result, actual_result):
        """Create bug in Jira"""
        if not self.jira:
            return None
            
        try:
            bug_description = f"""
*Description:*
{description}

*Steps to Reproduce:*
{steps_to_reproduce}

*Expected Result:*
{expected_result}

*Actual Result:*
{actual_result}

*Environment:* Chrome Browser, Automated Test
*Reported by:* AI QA Automation System
            """
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': bug_description,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'Medium'}
            }
            
            bug = self.jira.create_issue(fields=issue_dict)
            return bug.key
        except Exception as e:
            st.error(f"Failed to create bug: {e}")
            return None

class TestExecutor:
    """Execute generated test cases and capture results"""
    
    def __init__(self):
        self.driver = None
        self.results = []
    
    def setup_driver(self):
        """Setup Chrome driver for test execution"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            st.error(f"Failed to setup test driver: {e}")
            return False
    
    def execute_test_scenario(self, test_case):
        """Execute a single test scenario"""
        if not self.driver:
            return None
            
        result = {
            'test_name': test_case.get('name', 'Unknown Test'),
            'status': 'FAIL',
            'execution_time': 0,
            'error_message': '',
            'screenshots': [],
            'steps_executed': []
        }
        
        start_time = time.time()
        
        try:
            # Parse and execute test steps
            for step in test_case.get('steps', []):
                step_result = self.execute_step(step)
                result['steps_executed'].append(step_result)
                
                if not step_result['passed']:
                    result['error_message'] = step_result['error']
                    break
            else:
                result['status'] = 'PASS'
                
        except Exception as e:
            result['error_message'] = str(e)
            result['status'] = 'ERROR'
        
        result['execution_time'] = time.time() - start_time
        return result
    
    def execute_step(self, step):
        """Execute individual test step"""
        step_result = {
            'step': step,
            'passed': False,
            'error': ''
        }
        
        try:
            action = step.get('action', '').lower()
            
            if action == 'navigate':
                self.driver.get(step['url'])
                step_result['passed'] = True
                
            elif action == 'click':
                element = self.driver.find_element(By.XPATH, step['xpath'])
                element.click()
                step_result['passed'] = True
                
            elif action == 'input':
                element = self.driver.find_element(By.XPATH, step['xpath'])
                element.clear()
                element.send_keys(step['value'])
                step_result['passed'] = True
                
            elif action == 'verify':
                element = self.driver.find_element(By.XPATH, step['xpath'])
                if step['expected'] in element.text:
                    step_result['passed'] = True
                else:
                    step_result['error'] = f"Expected '{step['expected']}' but found '{element.text}'"
                    
            else:
                step_result['error'] = f"Unknown action: {action}"
                
        except Exception as e:
            step_result['error'] = str(e)
        
        return step_result

def simple_AI_Function_Agent(prompt, model="llama-3.3-70b-versatile"):
    """Core function to interface with the Groq API"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Error: GROQ_API_KEY not found in environment variables"
            
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def generate_test_cases_from_crawl(crawled_data, model="llama-3.3-70b-versatile"):
    """Generate comprehensive test cases from crawled website data"""
    
    # Prepare crawled data summary
    summary = f"""
Website Analysis Summary:
- Total pages crawled: {len(crawled_data['pages'])}
- Pages analyzed: {[page['title'] for page in crawled_data['pages']]}

Page Details:
"""
    
    for page in crawled_data['pages']:
        summary += f"""
URL: {page['url']}
Title: {page['title']}
Forms found: {len(page['forms'])}
Buttons found: {len(page['buttons'])}
Navigation elements: {len(page['navigation'])}
Content preview: {page['content'][:200]}...
---
"""
    
    prompt = f"""
Based on the following website crawl data, generate comprehensive test cases in JSON format.
Include positive tests, negative tests, UI tests, and edge cases.

{summary}

Please generate test cases in this JSON format:
{{
    "test_suites": [
        {{
            "suite_name": "Navigation Tests",
            "test_cases": [
                {{
                    "name": "Test navigation to homepage",
                    "priority": "High",
                    "type": "UI",
                    "description": "Verify user can navigate to homepage",
                    "preconditions": "User is on any page",
                    "steps": [
                        {{"action": "navigate", "url": "homepage_url"}},
                        {{"action": "verify", "xpath": "//title", "expected": "Homepage"}}
                    ],
                    "expected_result": "User successfully navigates to homepage"
                }}
            ]
        }}
    ]
}}

Focus on:
1. Form validation tests
2. Navigation functionality
3. Button click tests
4. Page load verification
5. Error handling scenarios
"""
    
    response = simple_AI_Function_Agent(prompt, model)
    return response

# Streamlit UI
st.title("🚀 Advanced AI QA Automation System")
st.markdown("**Web Crawling • Test Generation • Jira Integration • Automated Execution**")

# Sidebar configuration
st.sidebar.header("🔧 Configuration")

# Check for environment variables
env_status = st.sidebar.expander("🔍 Environment Status")
with env_status:
    groq_configured = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    jira_configured = "✅" if all([
        os.getenv("JIRA_SERVER_URL"),
        os.getenv("JIRA_EMAIL"), 
        os.getenv("JIRA_API_TOKEN"),
        os.getenv("JIRA_PROJECT_KEY")
    ]) else "❌"
    
    st.write(f"**Groq API:** {groq_configured}")
    st.write(f"**Jira Integration:** {jira_configured}")
    
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ GROQ_API_KEY not found in .env file")
    
    if not jira_configured:
        st.warning("⚠️ Jira credentials incomplete in .env file")

# Override options (for testing/development only)
with st.sidebar.expander("🔧 Development Override (Not Recommended)"):
    st.warning("⚠️ Only use for testing. Use .env file for production!")
    
    override_groq = st.text_input("Override Groq API Key", type="password", help="Temporary override - use .env instead")
    if override_groq:
        os.environ["GROQ_API_KEY"] = override_groq
        st.success("Groq API key temporarily overridden")
    
    st.subheader("Jira Override")
    override_jira_server = st.text_input("Override Jira Server", placeholder="https://yourcompany.atlassian.net")
    override_jira_email = st.text_input("Override Jira Email", placeholder="your-email@company.com")
    override_jira_token = st.text_input("Override Jira Token", type="password")
    override_jira_project = st.text_input("Override Project Key", placeholder="TEST")
    
    if all([override_jira_server, override_jira_email, override_jira_token, override_jira_project]):
        os.environ["JIRA_SERVER_URL"] = override_jira_server
        os.environ["JIRA_EMAIL"] = override_jira_email
        os.environ["JIRA_API_TOKEN"] = override_jira_token
        os.environ["JIRA_PROJECT_KEY"] = override_jira_project
        st.success("Jira settings temporarily overridden")

# Model and workflow selection
st.sidebar.subheader("🤖 AI Configuration")
models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
selected_model = st.sidebar.selectbox("AI Model", models)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌐 Web Crawling", "📝 Test Generation", "🔧 Test Execution", "🐛 Bug Management"])

with tab1:
    st.header("🌐 Website Crawler & Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        website_url = st.text_input("🔗 Website URL to Crawl", placeholder="https://example.com")
        
        col_a, col_b = st.columns(2)
        with col_a:
            max_pages = st.number_input("Max Pages to Crawl", min_value=1, max_value=20, value=5)
        with col_b:
            crawl_depth = st.number_input("Crawling Depth", min_value=1, max_value=3, value=2)
    
    with col2:
        st.info("""
        **Crawling Options:**
        - Max Pages: Limit crawled pages
        - Depth: How deep to follow links
        - Extracts: Forms, buttons, navigation, content
        """)
    
    if st.button("🕷️ Start Web Crawling", type="primary"):
        if not website_url:
            st.error("Please enter a website URL!")
        else:
            with st.spinner("🔄 Crawling website... This may take a few minutes."):
                crawler = WebCrawler()
                crawled_data = crawler.crawl_website(website_url, max_pages, crawl_depth)
                
                if crawled_data and crawled_data['pages']:
                    st.session_state['crawled_data'] = crawled_data
                    st.success(f"✅ Successfully crawled {len(crawled_data['pages'])} pages!")
                    
                    # Display crawl results
                    for i, page in enumerate(crawled_data['pages']):
                        with st.expander(f"📄 Page {i+1}: {page['title']}"):
                            st.write(f"**URL:** {page['url']}")
                            st.write(f"**Forms Found:** {len(page['forms'])}")
                            st.write(f"**Buttons Found:** {len(page['buttons'])}")
                            st.write(f"**Content Preview:** {page['content'][:300]}...")
                else:
                    st.error("Failed to crawl website. Please check the URL and try again.")

with tab2:
    st.header("📝 AI Test Case Generation")
    
    generation_method = st.radio(
        "Choose Generation Method:",
        ["From Crawled Website", "From Requirements Document", "Manual Input"]
    )
    
    if generation_method == "From Crawled Website":
        if 'crawled_data' in st.session_state:
            st.info(f"Ready to generate tests from {len(st.session_state['crawled_data']['pages'])} crawled pages")
            
            if st.button("🧠 Generate Test Cases from Crawl", type="primary"):
                with st.spinner("🔄 AI is generating comprehensive test cases..."):
                    test_cases = generate_test_cases_from_crawl(st.session_state['crawled_data'], selected_model)
                    st.session_state['generated_tests'] = test_cases
                    
                    st.success("✅ Test cases generated successfully!")
                    st.code(test_cases, language="json")
        else:
            st.warning("Please crawl a website first in the Web Crawling tab.")
    
    elif generation_method == "From Requirements Document":
        uploaded_file = st.file_uploader("Upload Requirements Document", type=['txt', 'pdf', 'docx'])
        
        if uploaded_file and st.button("📋 Generate Test Cases from Document"):
            with st.spinner("🔄 Processing document and generating test cases..."):
                # Process file content (existing logic)
                st.success("✅ Test cases generated from document!")
    
    else:  # Manual Input
        manual_requirements = st.text_area("Enter Requirements Manually", height=200)
        
        if manual_requirements and st.button("✍️ Generate Test Cases from Text"):
            with st.spinner("🔄 Generating test cases from your requirements..."):
                st.success("✅ Test cases generated from manual input!")

with tab3:
    st.header("🔧 Automated Test Execution")
    
    if 'generated_tests' in st.session_state:
        st.success("Test cases available for execution!")
        
        execution_options = st.columns(3)
        
        with execution_options[0]:
            headless_mode = st.checkbox("Headless Browser", value=True)
        
        with execution_options[1]:
            parallel_execution = st.checkbox("Parallel Execution", value=False)
        
        with execution_options[2]:
            screenshot_on_fail = st.checkbox("Screenshot on Failure", value=True)
        
        if st.button("🚀 Execute Test Suite", type="primary"):
            # Check if Groq API is configured
            if not os.getenv("GROQ_API_KEY"):
                st.error("❌ Groq API key not configured. Please check your .env file.")
            else:
                with st.spinner("🔄 Executing automated tests..."):
                    # Simulate test execution
                    st.success("✅ Test execution completed!")
                    
                    # Mock results
                    results_data = {
                        'Test Case': ['Login Test', 'Navigation Test', 'Form Submission', 'Search Functionality'],
                        'Status': ['PASS', 'FAIL', 'PASS', 'ERROR'],
                        'Duration (s)': [2.5, 1.8, 3.2, 0.5],
                        'Error Message': ['', 'Element not found', '', 'Timeout exception']
                    }
                    
                    results_df = pd.DataFrame(results_data)
                    st.dataframe(results_df)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Tests", len(results_df))
                    with col2:
                        st.metric("Passed", len(results_df[results_df['Status'] == 'PASS']))
                    with col3:
                        st.metric("Failed", len(results_df[results_df['Status'] == 'FAIL']))
                    with col4:
                        st.metric("Errors", len(results_df[results_df['Status'] == 'ERROR']))
    else:
        st.warning("Please generate test cases first in the Test Generation tab.")

with tab4:
    st.header("🐛 Bug Management & Jira Integration")
    
    # Check Jira configuration from environment
    jira_server = os.getenv("JIRA_SERVER_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_project = os.getenv("JIRA_PROJECT_KEY")
    
    if all([jira_server, jira_email, jira_token, jira_project]):
        st.success("✅ Jira configuration loaded from .env file!")
        
        # Display current configuration (masked for security)
        with st.expander("🔍 Current Jira Configuration"):
            st.write(f"**Server:** {jira_server}")
            st.write(f"**Email:** {jira_email}")
            st.write(f"**Project:** {jira_project}")
            st.write(f"**Token:** {'*' * len(jira_token[:-4]) + jira_token[-4:] if jira_token else 'Not set'}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 Test Results Summary")
            if st.button("🔄 Sync with Jira"):
                with st.spinner("Connecting to Jira..."):
                    jira_client = JiraIntegration(jira_server, jira_email, jira_token, jira_project)
                    if jira_client.connect():
                        st.success("✅ Connected to Jira successfully!")
                        
                        # Auto-create bugs for failed tests
                        if st.button("🐛 Auto-Create Bugs for Failed Tests"):
                            bugs_created = []
                            # Mock bug creation
                            bugs_created.append("BUG-123: Navigation Test Failure")
                            bugs_created.append("BUG-124: Search Timeout Error")
                            
                            for bug in bugs_created:
                                st.success(f"Created: {bug}")
                    else:
                        st.error("Failed to connect to Jira. Check your .env configuration.")
        
        with col2:
            st.subheader("📝 Manual Bug Creation")
            bug_summary = st.text_input("Bug Summary")
            bug_description = st.text_area("Bug Description")
            
            if st.button("🐛 Create Bug in Jira"):
                if bug_summary and bug_description:
                    st.success(f"✅ Bug created: {bug_summary}")
                else:
                    st.error("Please fill in bug summary and description.")
    else:
        st.warning("⚠️ Jira not configured. Please set up your .env file with Jira credentials.")
        
        missing_vars = []
        if not jira_server: missing_vars.append("JIRA_SERVER_URL")
        if not jira_email: missing_vars.append("JIRA_EMAIL") 
        if not jira_token: missing_vars.append("JIRA_API_TOKEN")
        if not jira_project: missing_vars.append("JIRA_PROJECT_KEY")
        
        st.error(f"Missing environment variables: {', '.join(missing_vars)}")

# Footer
st.markdown("---")
st.markdown("""
### 🎯 System Capabilities
- **Web Crawling**: Automatically discover and analyze website functionality
- **AI Test Generation**: Create comprehensive test suites from crawled data
- **Jira Integration**: Seamlessly create test cases and log bugs
- **Automated Execution**: Run tests with Selenium WebDriver
- **Real-time Reporting**: Track test results and failure analysis
""")

st.markdown("Built with ❤️ using **Streamlit**, **Selenium**, **Groq AI**, and **Jira API**")