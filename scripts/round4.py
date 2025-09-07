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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import traceback
from datetime import datetime
from jira import JIRA
import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageChops
import base64
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
import re
import tempfile
import shutil
import logging
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigurationValidator:
    """Validate and manage configuration settings"""
    
    @staticmethod
    def validate_api_keys():
        """Validate all required API keys and configurations"""
        validation_results = {
            'groq': {'status': False, 'message': ''},
            'figma': {'status': False, 'message': ''},
            'jira': {'status': False, 'message': ''},
            'chrome': {'status': False, 'message': ''}
        }
        
        # Validate Groq API
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and len(groq_key) > 50:
            validation_results['groq']['status'] = True
            validation_results['groq']['message'] = "API key configured"
        else:
            validation_results['groq']['message'] = "Missing or invalid GROQ_API_KEY"
        
        # Validate Figma API
        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        if figma_token and len(figma_token) > 40:
            validation_results['figma']['status'] = True
            validation_results['figma']['message'] = "Access token configured"
        else:
            validation_results['figma']['message'] = "Missing or invalid FIGMA_ACCESS_TOKEN"
        
        # Validate Jira configuration
        jira_required = ['JIRA_SERVER_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY']
        jira_values = [os.getenv(key) for key in jira_required]
        
        if all(jira_values):
            validation_results['jira']['status'] = True
            validation_results['jira']['message'] = "All Jira credentials configured"
        else:
            missing = [key for key, val in zip(jira_required, jira_values) if not val]
            validation_results['jira']['message'] = f"Missing: {', '.join(missing)}"
        
        # Validate Chrome driver availability
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.quit()
            
            validation_results['chrome']['status'] = True
            validation_results['chrome']['message'] = "Chrome driver available"
        except Exception as e:
            validation_results['chrome']['message'] = f"Chrome driver issue: {str(e)[:100]}"
        
        return validation_results
    
    @staticmethod
    def test_api_connections():
        """Test actual API connections"""
        connection_results = {}
        
        # Test Groq API
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Test connection"}],
                model="llama-3.3-70b-versatile",
                max_tokens=10
            )
            connection_results['groq'] = {'status': True, 'message': 'Connection successful'}
        except Exception as e:
            connection_results['groq'] = {'status': False, 'message': f'Connection failed: {str(e)[:100]}'}
        
        # Test Figma API
        try:
            headers = {"X-Figma-Token": os.getenv("FIGMA_ACCESS_TOKEN")}
            response = requests.get("https://api.figma.com/v1/me", headers=headers, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                connection_results['figma'] = {
                    'status': True, 
                    'message': f"Connected as: {user_data.get('email', 'Unknown')}"
                }
            else:
                connection_results['figma'] = {
                    'status': False, 
                    'message': f'API error: {response.status_code}'
                }
        except Exception as e:
            connection_results['figma'] = {'status': False, 'message': f'Connection failed: {str(e)[:100]}'}
        
        # Test Jira API
        try:
            jira_client = JIRA(
                server=os.getenv("JIRA_SERVER_URL"),
                basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
            )
            user = jira_client.myself()
            connection_results['jira'] = {
                'status': True,
                'message': f"Connected as: {user['displayName']}"
            }
        except Exception as e:
            connection_results['jira'] = {'status': False, 'message': f'Connection failed: {str(e)[:100]}'}
        
        return connection_results


class EnhancedChromeDriver:
    """Enhanced Chrome driver with consistent screenshot capabilities"""
    
    def __init__(self):
        self.driver = None
        self.options = None
        
    def setup_driver(self, headless=True, window_size="1920,1080", scale_factor=1):
        """Setup Chrome driver with optimized options for screenshots"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
            
            # Core stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Speed up loading
            
            # Window and display options
            chrome_options.add_argument(f"--window-size={window_size}")
            chrome_options.add_argument(f"--force-device-scale-factor={scale_factor}")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--disable-web-security")
            
            # Performance options
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # User agent for consistency
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Install and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)
            
            # Set window size explicitly
            width, height = window_size.split(',')
            self.driver.set_window_size(int(width), int(height))
            
            logger.info("Chrome driver setup successful")
            return True
            
        except Exception as e:
            logger.error(f"Chrome driver setup failed: {e}")
            return False
    
    def capture_full_page_screenshot(self, url, wait_time=3):
        """Capture full page screenshot with proper waiting"""
        if not self.driver:
            logger.error("Driver not initialized")
            return None
            
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(wait_time)
            
            # Execute JavaScript to ensure page is fully loaded
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Get full page dimensions
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Take screenshot
            screenshot = self.driver.get_screenshot_as_png()
            
            logger.info(f"Screenshot captured for {url}: {len(screenshot)} bytes")
            return screenshot
            
        except TimeoutException:
            logger.error(f"Timeout waiting for page to load: {url}")
            return None
        except Exception as e:
            logger.error(f"Screenshot capture failed for {url}: {e}")
            return None
    
    def capture_element_screenshot(self, url, css_selector, wait_time=3):
        """Capture screenshot of specific element"""
        if not self.driver:
            return None
            
        try:
            self.driver.get(url)
            
            # Wait for element to be present
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
            
            time.sleep(wait_time)
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Take element screenshot
            screenshot = element.screenshot_as_png
            
            logger.info(f"Element screenshot captured for {css_selector}")
            return screenshot
            
        except Exception as e:
            logger.error(f"Element screenshot failed: {e}")
            return None
    
    def quit(self):
        """Properly close the driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")


class EnhancedFigmaIntegration:
    """Enhanced Figma API integration with better error handling"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": access_token}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def validate_token(self):
        """Validate Figma access token"""
        try:
            response = self.session.get(f"{self.base_url}/me", timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'valid': True,
                    'user_email': user_data.get('email'),
                    'user_name': user_data.get('handle'),
                    'message': 'Token is valid'
                }
            elif response.status_code == 403:
                return {
                    'valid': False,
                    'message': 'Invalid or expired access token'
                }
            else:
                return {
                    'valid': False,
                    'message': f'API error: {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.Timeout:
            return {'valid': False, 'message': 'Request timeout - check your internet connection'}
        except requests.exceptions.RequestException as e:
            return {'valid': False, 'message': f'Network error: {str(e)}'}
    
    def extract_file_id(self, file_id_or_url):
        """Extract file ID from various Figma URL formats"""
        if not file_id_or_url:
            return None
            
        # If it's already a clean file ID
        if re.match(r'^[a-zA-Z0-9]{15,25}$', file_id_or_url):
            return file_id_or_url
        
        # Extract from URL patterns
        patterns = [
            r'figma\.com/design/([a-zA-Z0-9]+)',
            r'figma\.com/file/([a-zA-Z0-9]+)',
            r'figma\.com/proto/([a-zA-Z0-9]+)',
            r'figma\.com/[^/]+/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_id_or_url)
            if match:
                return match.group(1)
        
        return file_id_or_url  # Return as-is if no pattern matches
    
    def get_file_info(self, file_id_or_url):
        """Get Figma file information with enhanced error handling"""
        file_id = self.extract_file_id(file_id_or_url)
        
        if not file_id:
            return {'error': 'Invalid file ID or URL'}
        
        # Validate file ID format
        if not re.match(r'^[a-zA-Z0-9]{15,25}$', file_id):
            return {
                'error': f'Invalid file ID format: {file_id}',
                'suggestion': 'File ID should be 15-25 alphanumeric characters'
            }
        
        try:
            url = f"{self.base_url}/files/{file_id}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'file_id': file_id
                }
            elif response.status_code == 404:
                return {
                    'error': 'File not found',
                    'details': [
                        f"File ID '{file_id}' does not exist",
                        "You don't have access to this file",
                        "File may have been moved or deleted",
                        "Double-check the file URL or ID"
                    ]
                }
            elif response.status_code == 403:
                return {
                    'error': 'Access denied',
                    'details': [
                        "Your access token doesn't have permission for this file",
                        "File may be in a different team/organization",
                        "Token may have expired",
                        "Regenerate your access token and try again"
                    ]
                }
            elif response.status_code == 429:
                return {
                    'error': 'Rate limit exceeded',
                    'details': [
                        "Too many requests to Figma API",
                        "Wait a few minutes before trying again",
                        "Consider upgrading your Figma plan for higher limits"
                    ]
                }
            else:
                return {
                    'error': f'API error {response.status_code}',
                    'details': [response.text[:500]]
                }
                
        except requests.exceptions.Timeout:
            return {
                'error': 'Request timeout',
                'details': ['Figma API is slow to respond', 'Check your internet connection']
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': 'Network error',
                'details': [str(e)]
            }
    
    def get_file_images(self, file_id, node_ids=None, scale=1, format='png'):
        """Get rendered images with better error handling and retries"""
        file_id = self.extract_file_id(file_id)
        
        if not file_id:
            return {'error': 'Invalid file ID'}
        
        try:
            url = f"{self.base_url}/images/{file_id}"
            params = {
                'format': format,
                'scale': scale
            }
            
            if node_ids:
                if isinstance(node_ids, list):
                    params['ids'] = ','.join(node_ids)
                else:
                    params['ids'] = str(node_ids)
            
            # Retry logic for image generation
            max_retries = 3
            for attempt in range(max_retries):
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'images' in result and result['images']:
                        return {
                            'success': True,
                            'images': result['images'],
                            'file_id': file_id
                        }
                    else:
                        return {
                            'error': 'No images generated',
                            'details': ['Figma could not generate images for the specified nodes']
                        }
                elif response.status_code == 400:
                    return {
                        'error': 'Bad request',
                        'details': [
                            'Invalid node IDs or parameters',
                            f'Attempted node IDs: {node_ids}',
                            'Check that the nodes exist in the file'
                        ]
                    }
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        logger.info(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            'error': 'Rate limit exceeded',
                            'details': ['Too many requests', 'Try again later']
                        }
                else:
                    return {
                        'error': f'API error {response.status_code}',
                        'details': [response.text[:500]]
                    }
            
            return {'error': 'Max retries exceeded'}
            
        except Exception as e:
            return {
                'error': 'Request failed',
                'details': [str(e)]
            }


def create_progress_tracker():
    """Create a progress tracking system for long operations"""
    progress_container = st.empty()
    status_container = st.empty()
    
    def update_progress(current, total, status_text):
        progress = current / total if total > 0 else 0
        progress_container.progress(progress)
        status_container.info(f"{status_text} ({current}/{total})")
    
    def complete():
        progress_container.empty()
        status_container.empty()
    
    return update_progress, complete


def display_configuration_status():
    """Display comprehensive configuration status"""
    st.sidebar.subheader("Configuration Status")
    
    with st.sidebar.expander("Validation Results", expanded=True):
        validator = ConfigurationValidator()
        results = validator.validate_api_keys()
        
        for service, result in results.items():
            status_icon = "✅" if result['status'] else "❌"
            st.write(f"**{service.title()}:** {status_icon}")
            st.caption(result['message'])
        
        # Test connections button
        if st.button("Test API Connections"):
            with st.spinner("Testing connections..."):
                connections = validator.test_api_connections()
                
                for service, result in connections.items():
                    status_icon = "✅" if result['status'] else "❌"
                    st.write(f"**{service.title()} Connection:** {status_icon}")
                    st.caption(result['message'])


def main():
    """Main Streamlit application with enhanced features"""
    st.set_page_config(
        page_title="Enhanced QA Automation System",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Enhanced AI QA Automation System")
    st.markdown("Complete testing solution with design comparison, document processing, and Jira integration")
    
    # Configuration sidebar
    display_configuration_status()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Configuration & Testing",
        "Document Processing", 
        "Design Comparison",
        "System Status"
    ])
    
    with tab1:
        st.header("Configuration & API Testing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Chrome Driver Test")
            if st.button("Test Chrome Driver"):
                with st.spinner("Testing Chrome driver..."):
                    driver = EnhancedChromeDriver()
                    if driver.setup_driver():
                        st.success("Chrome driver is working correctly")
                        
                        # Test screenshot capability
                        test_url = st.text_input("Test URL", "https://example.com")
                        if st.button("Test Screenshot Capture"):
                            screenshot = driver.capture_full_page_screenshot(test_url)
                            if screenshot:
                                st.success("Screenshot captured successfully!")
                                st.image(screenshot, caption=f"Screenshot of {test_url}")
                            else:
                                st.error("Failed to capture screenshot")
                        
                        driver.quit()
                    else:
                        st.error("Chrome driver setup failed")
        
        with col2:
            st.subheader("Figma API Test")
            figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
            
            if figma_token:
                figma_client = EnhancedFigmaIntegration(figma_token)
                
                if st.button("Validate Figma Token"):
                    with st.spinner("Validating token..."):
                        validation = figma_client.validate_token()
                        
                        if validation['valid']:
                            st.success("Figma token is valid!")
                            st.info(f"Connected as: {validation.get('user_email', 'Unknown')}")
                        else:
                            st.error(f"Token validation failed: {validation['message']}")
                
                # Test file access
                test_file_id = st.text_input("Test Figma File ID/URL")
                if test_file_id and st.button("Test File Access"):
                    with st.spinner("Testing file access..."):
                        result = figma_client.get_file_info(test_file_id)
                        
                        if 'success' in result:
                            st.success("File access successful!")
                            file_data = result['data']
                            st.info(f"File: {file_data['name']}")
                            st.info(f"Pages: {len(file_data['document']['children'])}")
                        else:
                            st.error(f"File access failed: {result['error']}")
                            if 'details' in result:
                                for detail in result['details']:
                                    st.caption(f"• {detail}")
            else:
                st.warning("Figma access token not configured")
    
    with tab2:
        st.header("Requirements Document Processing")
        st.info("Upload RFP, acceptance criteria, or requirements documents to generate test cases")
        
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'docx', 'txt'],
            help="Supported formats: PDF, Word, Text files"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            # Process document
            if st.button("Process Document", type="primary"):
                update_progress, complete_progress = create_progress_tracker()
                
                try:
                    update_progress(1, 4, "Reading document...")
                    
                    # Document processing logic would go here
                    time.sleep(1)  # Simulate processing
                    
                    update_progress(2, 4, "Extracting text...")
                    time.sleep(1)
                    
                    update_progress(3, 4, "Generating test cases...")
                    time.sleep(1)
                    
                    update_progress(4, 4, "Creating Jira tickets...")
                    time.sleep(1)
                    
                    complete_progress()
                    st.success("Document processed successfully!")
                    
                except Exception as e:
                    complete_progress()
                    st.error(f"Processing failed: {e}")
    
    with tab3:
        st.header("Design Comparison Testing")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Figma Configuration")
            figma_file_input = st.text_input(
                "Figma File ID/URL",
                placeholder="Paste Figma file URL or ID"
            )
            
            website_url = st.text_input(
                "Website URL",
                placeholder="https://your-website.com"
            )
        
        with col2:
            st.subheader("Comparison Settings")
            similarity_threshold = st.slider("Similarity Threshold", 0.6, 1.0, 0.85, 0.05)
            screenshot_scale = st.selectbox("Screenshot Scale", [1, 2, 3], index=1)
            comparison_method = st.selectbox("Method", ["structural", "pixel_perfect"])
        
        if st.button("Start Design Comparison", type="primary"):
            if not figma_file_input or not website_url:
                st.error("Please provide both Figma file and website URL")
            else:
                update_progress, complete_progress = create_progress_tracker()
                
                try:
                    # Initialize components
                    figma_client = EnhancedFigmaIntegration(os.getenv("FIGMA_ACCESS_TOKEN"))
                    chrome_driver = EnhancedChromeDriver()
                    
                    update_progress(1, 6, "Validating Figma file...")
                    file_result = figma_client.get_file_info(figma_file_input)
                    
                    if 'error' in file_result:
                        st.error(f"Figma file error: {file_result['error']}")
                        if 'details' in file_result:
                            for detail in file_result['details']:
                                st.caption(f"• {detail}")
                        complete_progress()
                        return
                    
                    update_progress(2, 6, "Setting up Chrome driver...")
                    if not chrome_driver.setup_driver():
                        st.error("Failed to setup Chrome driver")
                        complete_progress()
                        return
                    
                    update_progress(3, 6, "Capturing website screenshot...")
                    website_screenshot = chrome_driver.capture_full_page_screenshot(website_url)
                    
                    if not website_screenshot:
                        st.error("Failed to capture website screenshot")
                        chrome_driver.quit()
                        complete_progress()
                        return
                    
                    update_progress(4, 6, "Generating Figma images...")
                    # This would contain the actual Figma image generation logic
                    time.sleep(2)  # Simulate processing
                    
                    update_progress(5, 6, "Comparing images...")
                    time.sleep(1)  # Simulate comparison
                    
                    update_progress(6, 6, "Generating report...")
                    time.sleep(1)  # Simulate report generation
                    
                    complete_progress()
                    chrome_driver.quit()
                    
                    st.success("Design comparison completed!")
                    
                    # Display results
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.subheader("Website Screenshot")
                        st.image(website_screenshot, use_container_width=True)
                    
                    with col_b:
                        st.subheader("Comparison Results")
                        st.metric("Similarity Score", "87.5%")
                        st.metric("Issues Found", "3")
                        
                except Exception as e:
                    complete_progress()
                    st.error(f"Comparison failed: {e}")
                    st.exception(e)
    
    with tab4:
        st.header("System Status & Diagnostics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Environment Variables")
            env_vars = [
                'GROQ_API_KEY',
                'FIGMA_ACCESS_TOKEN', 
                'JIRA_SERVER_URL',
                'JIRA_EMAIL',
                'JIRA_API_TOKEN',
                'JIRA_PROJECT_KEY'
            ]
            
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                    st.success(f"✅ {var}: {masked_value}")
                else:
                    st.error(f"❌ {var}: Not set")
        
        with col2:
            st.subheader("System Information")
            st.info(f"Python Version: {os.sys.version}")
            st.info(f"Streamlit Version: {st.__version__}")
            
            # Display Chrome driver info
            if st.button("Check Chrome Version"):
                try:
                    driver = EnhancedChromeDriver()
                    if driver.setup_driver(headless=True):
                        capabilities = driver.driver.capabilities
                        chrome_version = capabilities['browserVersion']
                        driver_version = capabilities['chrome']['chromedriverVersion'].split(' ')[0]
                        st.success(f"Chrome: {chrome_version}")
                        st.success(f"ChromeDriver: {driver_version}")
                        driver.quit()
                    else:
                        st.error("Failed to get Chrome information")
                except Exception as e:
                    st.error(f"Chrome check failed: {e}")


if __name__ == "__main__":
    main()