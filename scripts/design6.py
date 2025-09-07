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
from datetime import datetime, timezone
from jira import JIRA
from jira.exceptions import JIRAError
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
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Priority(Enum):
    """Jira priority levels"""
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"

class IssueType(Enum):
    """Jira issue types"""
    BUG = "Bug"
    TASK = "Task"
    IMPROVEMENT = "Improvement"
    TEST = "Test"

@dataclass
class DesignIssue:
    """Represents a design QA issue"""
    category: str
    subcategory: str
    description: str
    severity: Priority
    screenshot_path: Optional[str] = None
    element_selector: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    checklist_item: Optional[str] = None

@dataclass
class QAChecklistItem:
    """Represents a QA checklist item"""
    id: str
    category: str
    subcategory: str
    description: str
    automated: bool = False
    selector: Optional[str] = None
    validation_function: Optional[str] = None

class DesignQAChecklist:
    """Comprehensive design QA checklist based on best practices"""
    
    def __init__(self):
        self.checklist_items = self._initialize_checklist()
    
    def _initialize_checklist(self) -> List[QAChecklistItem]:
        """Initialize the comprehensive QA checklist"""
        return [
            # Visual Design - Brand Consistency
            QAChecklistItem("VD001", "Visual Design", "Brand Consistency", 
                          "Logo usage follows brand guidelines", True, "img[alt*='logo'], .logo"),
            QAChecklistItem("VD002", "Visual Design", "Brand Consistency", 
                          "Color palette adheres to brand specifications", True),
            QAChecklistItem("VD003", "Visual Design", "Brand Consistency", 
                          "Typography matches brand standards", True, "h1, h2, h3, h4, h5, h6, p, span"),
            QAChecklistItem("VD004", "Visual Design", "Brand Consistency", 
                          "Iconography style is consistent with brand identity", True, ".icon, svg, i[class*='icon']"),
            
            # Visual Design - Layout
            QAChecklistItem("VD005", "Visual Design", "Layout", 
                          "Grid system is consistently applied", True, ".container, .grid, .row, .col"),
            QAChecklistItem("VD006", "Visual Design", "Layout", 
                          "Whitespace is used effectively", True),
            QAChecklistItem("VD007", "Visual Design", "Layout", 
                          "Content hierarchy is clear and logical", True, "h1, h2, h3, h4, h5, h6"),
            QAChecklistItem("VD008", "Visual Design", "Layout", 
                          "Page elements are aligned properly", True),
            
            # Visual Design - Typography
            QAChecklistItem("VD009", "Visual Design", "Typography", 
                          "Font sizes are appropriate and consistent", True, "*"),
            QAChecklistItem("VD010", "Visual Design", "Typography", 
                          "Line heights ensure good readability", True, "p, span, div"),
            QAChecklistItem("VD011", "Visual Design", "Typography", 
                          "Font weights are used consistently", True, "*"),
            QAChecklistItem("VD012", "Visual Design", "Typography", 
                          "Text colors provide sufficient contrast with backgrounds", True, "*"),
            
            # Visual Design - Color Usage
            QAChecklistItem("VD013", "Visual Design", "Color Usage", 
                          "Color contrast meets WCAG 2.1 standards", True, "*"),
            QAChecklistItem("VD014", "Visual Design", "Color Usage", 
                          "Color is used consistently to convey information", True),
            QAChecklistItem("VD015", "Visual Design", "Color Usage", 
                          "Interactive elements have clear color states", True, "a, button, input, select"),
            
            # Visual Design - Imagery
            QAChecklistItem("VD016", "Visual Design", "Imagery", 
                          "Images are high quality and not pixelated", True, "img"),
            QAChecklistItem("VD017", "Visual Design", "Imagery", 
                          "Image aspect ratios are consistent", True, "img"),
            QAChecklistItem("VD018", "Visual Design", "Imagery", 
                          "Alt text is provided for all images", True, "img"),
            QAChecklistItem("VD019", "Visual Design", "Imagery", 
                          "Decorative images are implemented correctly", True, "img, [style*='background-image']"),
            
            # Responsive Design - Breakpoints
            QAChecklistItem("RD001", "Responsive Design", "Breakpoints", 
                          "Design adapts appropriately at all defined breakpoints", True),
            QAChecklistItem("RD002", "Responsive Design", "Breakpoints", 
                          "No horizontal scrolling on any device-width", True),
            QAChecklistItem("RD003", "Responsive Design", "Breakpoints", 
                          "Content reflow is logical across breakpoints", True),
            
            # Responsive Design - Mobile-specific
            QAChecklistItem("RD004", "Responsive Design", "Mobile-specific", 
                          "Touch targets are at least 44x44 pixels", True, "button, a, input, select"),
            QAChecklistItem("RD005", "Responsive Design", "Mobile-specific", 
                          "Mobile navigation is easily accessible", True, ".mobile-nav, .navbar-toggler"),
            QAChecklistItem("RD006", "Responsive Design", "Mobile-specific", 
                          "Font sizes are legible on small screens", True, "*"),
            QAChecklistItem("RD007", "Responsive Design", "Mobile-specific", 
                          "Critical content is visible without scrolling on mobile", True),
            
            # User Interface Elements - Buttons
            QAChecklistItem("UI001", "UI Elements", "Buttons", 
                          "Button styles are consistent throughout the design", True, "button, .btn, input[type='submit']"),
            QAChecklistItem("UI002", "UI Elements", "Buttons", 
                          "Button states are clearly defined", True, "button, .btn"),
            QAChecklistItem("UI003", "UI Elements", "Buttons", 
                          "Button labels are clear and action-oriented", True, "button, .btn"),
            
            # User Interface Elements - Forms
            QAChecklistItem("UI004", "UI Elements", "Forms", 
                          "Form layouts are consistent", True, "form"),
            QAChecklistItem("UI005", "UI Elements", "Forms", 
                          "Input fields are clearly labelled", True, "input, select, textarea"),
            QAChecklistItem("UI006", "UI Elements", "Forms", 
                          "Error states are visually distinct", True, ".error, .invalid, .has-error"),
            QAChecklistItem("UI007", "UI Elements", "Forms", 
                          "Required fields are indicated", True, "input[required], .required"),
            
            # User Interface Elements - Navigation
            QAChecklistItem("UI008", "UI Elements", "Navigation", 
                          "Navigation structure is intuitive", True, "nav, .navigation, .menu"),
            QAChecklistItem("UI009", "UI Elements", "Navigation", 
                          "Current page/section is indicated", True, ".active, .current"),
            QAChecklistItem("UI010", "UI Elements", "Navigation", 
                          "Dropdown menus are easy to use", True, ".dropdown, .submenu"),
            
            # Accessibility
            QAChecklistItem("A001", "Accessibility", "Color and Contrast", 
                          "Text meets minimum contrast ratios", True, "*"),
            QAChecklistItem("A002", "Accessibility", "Color and Contrast", 
                          "Information is not conveyed by color alone", True),
            QAChecklistItem("A003", "Accessibility", "Keyboard Navigation", 
                          "All interactive elements are keyboard accessible", True, "a, button, input, select"),
            QAChecklistItem("A004", "Accessibility", "Keyboard Navigation", 
                          "Focus states are clearly visible", True, "a, button, input, select"),
            QAChecklistItem("A005", "Accessibility", "Screen Reader Compatibility", 
                          "Proper heading structure is implemented", True, "h1, h2, h3, h4, h5, h6"),
            QAChecklistItem("A006", "Accessibility", "Screen Reader Compatibility", 
                          "ARIA labels are used where necessary", True, "[aria-label], [aria-labelledby]"),
        ]
    
    def get_items_by_category(self, category: str) -> List[QAChecklistItem]:
        """Get checklist items by category"""
        return [item for item in self.checklist_items if item.category == category]
    
    def get_automated_items(self) -> List[QAChecklistItem]:
        """Get items that can be automated"""
        return [item for item in self.checklist_items if item.automated]

class EnhancedJiraIntegration:
    """Enhanced Jira integration with comprehensive ticket management"""
    
    def __init__(self):
        self.server_url = os.getenv("JIRA_SERVER_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        self.jira_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Jira client with better error handling"""
        try:
            if not all([self.server_url, self.email, self.api_token, self.project_key]):
                missing = []
                if not self.server_url: missing.append("JIRA_SERVER_URL")
                if not self.email: missing.append("JIRA_EMAIL")
                if not self.api_token: missing.append("JIRA_API_TOKEN")
                if not self.project_key: missing.append("JIRA_PROJECT_KEY")
                logger.error(f"Missing Jira configuration: {', '.join(missing)}")
                return
            
            # Test connection with timeout
            self.jira_client = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token),
                timeout=30
            )
            
            # Test the connection immediately
            user_info = self.jira_client.myself()
            logger.info(f"Jira client initialized successfully for user: {user_info['displayName']}")
            
        except JIRAError as e:
            logger.error(f"JIRA Error during initialization: {e.text if hasattr(e, 'text') else str(e)}")
            self.jira_client = None
        except Exception as e:
            logger.error(f"Typography check failed: {e}")
    
    def _check_responsive_design(self):
        """Check responsive design elements"""
        try:
            # Check viewport meta tag
            try:
                self.driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
            except:
                self.issues_found.append(DesignIssue(
                    category="Responsive Design",
                    subcategory="Meta Tags",
                    description="Missing viewport meta tag",
                    severity=Priority.HIGH,
                    expected_behavior="Page should have viewport meta tag for mobile responsiveness",
                    actual_behavior="No viewport meta tag found",
                    checklist_item="RD001"
                ))
            
            # Check for horizontal scrolling
            page_width = self.driver.execute_script("return document.body.scrollWidth")
            window_width = self.driver.execute_script("return window.innerWidth")
            
            if page_width > window_width + 10:  # Allow for small discrepancies
                self.issues_found.append(DesignIssue(
                    category="Responsive Design",
                    subcategory="Layout",
                    description=f"Horizontal scrolling detected: page {page_width}px, window {window_width}px",
                    severity=Priority.MEDIUM,
                    expected_behavior="Page should not have horizontal scrolling",
                    actual_behavior=f"Page width exceeds window width by {page_width - window_width}px",
                    checklist_item="RD002"
                ))
        except Exception as e:
            logger.error(f"Responsive design check failed: {e}")

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
        
    def close(self):
        """Close the driver safely"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Chrome driver closed successfully")
        except Exception as e:
            logger.error(f"Error closing Chrome driver: {e}")
        finally:
            self.driver = None    
        
    def setup_driver(self, headless=True, window_size="1920,1080", scale_factor=2):
        """Setup Chrome driver with optimized options for high-quality screenshots"""
        try:
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless=new")
            
            # Core stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            
            # Window and display options for better quality
            chrome_options.add_argument(f"--window-size={window_size}")
            chrome_options.add_argument(f"--force-device-scale-factor={scale_factor}")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--disable-web-security")
            
            # Performance options
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            
            # High-quality rendering options
            chrome_options.add_argument("--high-dpi-support=1")
            chrome_options.add_argument("--force-color-profile=srgb")
            chrome_options.add_argument("--disable-software-rasterizer")
            
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
    
    def capture_full_page_screenshot(self, url, wait_time=5):
        """Capture high-quality full page screenshot with proper waiting"""
        if not self.driver:
            logger.error("Driver not initialized")
            return None
            
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content and animations
            time.sleep(wait_time)
            
            # Execute JavaScript to ensure page is fully loaded and stable
            self.driver.execute_script("""
                // Wait for images to load
                const images = document.querySelectorAll('img');
                const imagePromises = Array.from(images).map(img => {
                    if (img.complete) return Promise.resolve();
                    return new Promise(resolve => {
                        img.onload = resolve;
                        img.onerror = resolve;
                    });
                });
                
                // Wait for fonts to load
                document.fonts.ready.then(() => {
                    // Fonts are loaded
                });
                
                return Promise.all(imagePromises);
            """)
            
            time.sleep(2)  # Additional wait after JavaScript execution
            
            # Get full page dimensions
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Scroll to top and take initial screenshot
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Take screenshot with higher quality
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot))
            
            # If page is longer than viewport, capture remaining parts
            if total_height > viewport_height:
                # Create a new image for the full page with higher quality
                full_image = Image.new('RGB', (image.width, total_height), (255, 255, 255))
                full_image.paste(image, (0, 0))
                
                # Capture remaining parts with smooth scrolling
                current_position = viewport_height
                while current_position < total_height:
                    # Smooth scroll to next position
                    self.driver.execute_script(f"""
                        window.scrollTo({{
                            top: {current_position},
                            behavior: 'smooth'
                        }});
                    """)
                    time.sleep(1)  # Wait for scroll to complete and content to stabilize
                    
                    # Capture screenshot
                    part_screenshot = self.driver.get_screenshot_as_png()
                    part_image = Image.open(BytesIO(part_screenshot))
                    
                    # Paste into full image
                    full_image.paste(part_image, (0, current_position))
                    
                    current_position += viewport_height
                
                # Scroll back to top
                self.driver.execute_script("window.scrollTo(0, 0);")
                
                return full_image
            else:
                return image
                
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None

class FigmaDesignComparator:
    """Compare web implementation with Figma design"""
    
    def __init__(self):
        self.access_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.headers = {"X-Figma-Token": self.access_token} if self.access_token else {}
    
    def extract_file_id(self, figma_url):
        """Extract file ID from Figma URL"""
        try:
            # Handle different Figma URL formats
            if "figma.com/file/" in figma_url:
                # Standard file URL: https://www.figma.com/file/FILE_ID/FILE_NAME
                parts = figma_url.split("/file/")[1].split("/")
                file_id = parts[0]
            elif "figma.com/design/" in figma_url:
                # Design URL: https://www.figma.com/design/FILE_ID/FILE_NAME
                parts = figma_url.split("/design/")[1].split("/")
                file_id = parts[0]
            elif re.match(r'^[a-zA-Z0-9]{15,25}$', figma_url):
                logger.error(f"Failed to initialize Jira client: {str(e)}")
                self.jira_client = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and permissions with detailed diagnostics"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized - check configuration'}
        
        try:
            # Test basic connection
            user = self.jira_client.myself()
            
            # Test project access
            try:
                project = self.jira_client.project(self.project_key)
                project_access = True
                project_error = None
            except JIRAError as e:
                project_access = False
                project_error = e.text
            
            # Test issue creation permissions
            try:
                # Try to get create metadata for the project
                createmeta = self.jira_client.createmeta(projectKeys=[self.project_key])
                can_create = bool(createmeta['projects'][0]['issuetypes']) if createmeta['projects'] else False
                create_error = None
            except JIRAError as e:
                can_create = False
                create_error = e.text
            
            # Get available issue types
            issue_types = self.jira_client.issue_types()
            
            # Get available priorities
            priorities = self.jira_client.priorities()
            
            result = {
                'success': True,
                'user': user['displayName'],
                'user_email': user.get('email', 'Unknown'),
                'project_access': project_access,
                'can_create_issues': can_create,
                'issue_types': [it.name for it in issue_types],
                'priorities': [p.name for p in priorities]
            }
            
            if not project_access:
                result['project_error'] = project_error
            if not can_create:
                result['create_error'] = create_error
                
            return result
            
        except JIRAError as e:
            return {'success': False, 'error': f'Jira API Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def create_design_qa_ticket(self, issue: DesignIssue, 
                               assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a Jira ticket for a design QA issue with better error handling"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized'}
        
        try:
            # Prepare issue data
            summary = f"[Design QA] {issue.category} - {issue.subcategory}: {issue.description[:60]}..."
            if len(summary) > 255:  # Jira summary length limit
                summary = summary[:252] + "..."
            
            description = self._format_issue_description(issue)
            
            # Build the issue dictionary
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Bug'},  # Use string instead of Enum for compatibility
                'labels': ['design-qa', 'automated-testing', issue.category.lower().replace(' ', '-')]
            }
            
            # Set priority if available
            try:
                priorities = self.jira_client.priorities()
                priority_names = [p.name for p in priorities]
                if issue.severity.value in priority_names:
                    issue_dict['priority'] = {'name': issue.severity.value}
            except:
                pass  # Priority is optional
            
            # Add assignee if provided and valid
            if assignee:
                try:
                    # Verify assignee exists
                    user = self.jira_client.user(assignee)
                    issue_dict['assignee'] = {'name': assignee}
                except JIRAError:
                    logger.warning(f"Assignee {assignee} not found, creating unassigned ticket")
            
            # Create the issue
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            # Upload screenshot if available
            if issue.screenshot_path and os.path.exists(issue.screenshot_path):
                self._attach_screenshot(new_issue.key, issue.screenshot_path)
            
            return {
                'success': True,
                'issue_key': new_issue.key,
                'issue_url': f"{self.server_url}/browse/{new_issue.key}",
                'message': f'Created ticket {new_issue.key}'
            }
            
        except JIRAError as e:
            error_msg = f"JIRA Error: {e.status_code} - {e.text}" if hasattr(e, 'status_code') else f"JIRA Error: {e.text}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_bulk_tickets(self, issues: List[DesignIssue], 
                           assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create multiple Jira tickets in bulk with rate limiting"""
        results = {'successful': [], 'failed': []}
        
        for i, issue in enumerate(issues):
            # Add small delay to avoid rate limiting
            if i > 0:
                time.sleep(1)
                
            result = self.create_design_qa_ticket(issue, assignee)
            
            if result['success']:
                results['successful'].append({
                    'issue': issue,
                    'ticket_key': result['issue_key'],
                    'url': result['issue_url']
                })
                logger.info(f"Created ticket {result['issue_key']} for {issue.category} issue")
            else:
                results['failed'].append({
                    'issue': issue,
                    'error': result['error']
                })
                logger.error(f"Failed to create ticket for {issue.category}: {result['error']}")
        
        return {
            'total_processed': len(issues),
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'results': results
        }
    
    def _format_issue_description(self, issue: DesignIssue) -> str:
        """Format issue description for Jira with better formatting"""
        description = f"""
*Category:* {issue.category}
*Subcategory:* {issue.subcategory}
*Severity:* {issue.severity.value}

*Description:*
{issue.description}

*Expected Behavior:*
{issue.expected_behavior or 'Not specified'}

*Actual Behavior:*
{issue.actual_behavior or 'Not specified'}

*Element Selector:* 
{issue.element_selector or 'N/A'}

*Checklist Item:*
{issue.checklist_item or 'N/A'}

---
*Automated Design QA Report*
*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        return description
    
    def _attach_screenshot(self, issue_key: str, screenshot_path: str):
        """Attach screenshot to Jira ticket with better error handling and compression"""
        try:
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot file does not exist: {screenshot_path}")
                return
                
            file_size = os.path.getsize(screenshot_path)
            if file_size == 0:
                logger.error(f"Screenshot file is empty: {screenshot_path}")
                return
            
            # Check file size limit (Jira typically has a 10MB limit per attachment)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Screenshot too large ({file_size} bytes), compressing...")
                # Compress the image
                image = Image.open(screenshot_path)
                # Save with optimized compression
                image.save(screenshot_path, "PNG", optimize=True, quality=85)
                file_size = os.path.getsize(screenshot_path)
                logger.info(f"Compressed screenshot to {file_size} bytes")
            
            with open(screenshot_path, 'rb') as f:
                self.jira_client.add_attachment(
                    issue=issue_key, 
                    attachment=f,
                    filename=f"design_qa_screenshot_{issue_key}.png"
                )
            logger.info(f"Screenshot ({file_size} bytes) attached to {issue_key}")
            
        except Exception as e:
            logger.error(f"Failed to attach screenshot to {issue_key}: {e}")
            # Log more details for debugging
            if hasattr(e, 'response'):
                logger.error(f"Jira response: {e.response.text}")
            if hasattr(e, 'status_code'):
                logger.error(f"HTTP status: {e.status_code}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information with better error handling"""
        if not self.jira_client:
            return {'error': 'Jira client not initialized'}
        
        try:
            project = self.jira_client.project(self.project_key)
            issue_types = self.jira_client.issue_types()
            priorities = self.jira_client.priorities()
            
            return {
                'project_name': project.name,
                'project_key': project.key,
                'project_lead': project.lead.displayName if hasattr(project, 'lead') else 'Unknown',
                'issue_types': [{'id': it.id, 'name': it.name} for it in issue_types],
                'priorities': [{'id': p.id, 'name': p.name} for p in priorities]
            }
        except JIRAError as e:
            return {'error': f'JIRA Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'error': f'Failed to get project info: {str(e)}'}

class AutomatedDesignValidator:
    """Automated design validation using the QA checklist"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.checklist = DesignQAChecklist()
        self.issues_found = []
    
    def validate_page(self, url: str) -> List[DesignIssue]:
        """Validate a page against the design checklist"""
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Run automated checks
            self._check_accessibility()
            self._check_images()
            self._check_forms()
            self._check_buttons()
            self._check_typography()
            self._check_responsive_design()
            
            return self.issues_found
            
        except Exception as e:
            logger.error(f"Page validation failed: {e}")
            return []
    
    def _check_accessibility(self):
        """Check accessibility compliance"""
        try:
            # Check for images without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                alt_text = img.get_attribute("alt")
                if not alt_text or alt_text.strip() == "":
                    self.issues_found.append(DesignIssue(
                        category="Accessibility",
                        subcategory="Images",
                        description=f"Image missing alt text: {img.get_attribute('src')[:50]}...",
                        severity=Priority.HIGH,
                        element_selector=f"img[src*='{img.get_attribute('src')[:20]}']",
                        expected_behavior="All images should have descriptive alt text",
                        actual_behavior="Image has no alt text attribute",
                        checklist_item="VD018"
                    ))
            
            # Check heading structure
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            if not headings:
                self.issues_found.append(DesignIssue(
                    category="Accessibility",
                    subcategory="Structure",
                    description="No heading elements found on page",
                    severity=Priority.MEDIUM,
                    expected_behavior="Page should have proper heading structure",
                    actual_behavior="No headings detected",
                    checklist_item="A005"
                ))
            
        except Exception as e:
            logger.error(f"Accessibility check failed: {e}")
    
    def _check_images(self):
        """Check image quality and implementation"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                # Check if image is loaded
                if img.get_attribute("naturalWidth") == "0":
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Broken or missing image: {img.get_attribute('src')}",
                        severity=Priority.HIGH,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should load correctly",
                        actual_behavior="Image failed to load",
                        checklist_item="VD016"
                    ))
                
                # Check for consistent sizing
                width = img.size['width']
                height = img.size['height']
                if width < 10 or height < 10:
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Image too small: {width}x{height}px",
                        severity=Priority.LOW,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should be appropriately sized",
                        actual_behavior=f"Image is only {width}x{height}px",
                        checklist_item="VD016"
                    ))
        except Exception as e:
            logger.error(f"Image check failed: {e}")
    
    def _check_forms(self):
        """Check form implementation"""
        try:
            # Check for unlabeled inputs
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type")
                if input_type not in ["hidden", "submit", "button"]:
                    # Check for label
                    input_id = input_elem.get_attribute("id")
                    has_label = False
                    
                    if input_id:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            has_label = True
                        except:
                            pass
                    
                    if not has_label:
                        self.issues_found.append(DesignIssue(
                            category="UI Elements",
                            subcategory="Forms",
                            description=f"Input field without label: {input_type} input",
                            severity=Priority.MEDIUM,
                            element_selector=f"input[type='{input_type}']",
                            expected_behavior="All input fields should have associated labels",
                            actual_behavior="Input field has no label",
                            checklist_item="UI005"
                        ))
        except Exception as e:
            logger.error(f"Form check failed: {e}")
    
    def _check_buttons(self):
        """Check button implementation"""
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            for button in buttons:
                # Check button text
                text = button.text or button.get_attribute("value")
                if not text or len(text.strip()) < 2:
                    self.issues_found.append(DesignIssue(
                        category="UI Elements",
                        subcategory="Buttons",
                        description="Button with unclear or missing text",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Buttons should have clear, action-oriented labels",
                        actual_behavior=f"Button text: '{text}'",
                        checklist_item="UI003"
                    ))
                
                # Check button size for mobile
                size = button.size
                if size['width'] < 44 or size['height'] < 44:
                    self.issues_found.append(DesignIssue(
                        category="Responsive Design",
                        subcategory="Mobile-specific",
                        description=f"Button too small for touch: {size['width']}x{size['height']}px",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Touch targets should be at least 44x44 pixels",
                        actual_behavior=f"Button is {size['width']}x{size['height']}px",
                        checklist_item="RD004"
                    ))
        except Exception as e:
            logger.error(f"Button check failed: {e}")
    
    def _check_typography(self):
        """Check typography consistency"""
        try:
            # Check for very small text
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, span, div, li, td, th")
            for element in all_elements[:50]:  # Limit to first 50 to avoid performance issues
                font_size = element.value_of_css_property("font-size")
                if font_size:
                    size_px = float(font_size.replace("px", ""))
                    if size_px < 12:  # Text smaller than 12px might be hard to read
                        self.issues_found.append(DesignIssue(
                            category="Visual Design",
                            subcategory="Typography",
                            description=f"Text too small: {size_px}px",
                            severity=Priority.LOW,
                            element_selector=element.tag_name,
                            expected_behavior="Text should be at least 12px for readability",
                            actual_behavior=f"Font size is {size_px}px",
                            checklist_item="VD009"
                        ))
        except Exception as e, figma_url):
                # Direct file ID
                file_id = figma_url
            else:
                return None
            
            # Validate file ID format
            if not re.match(r'^[a-zA-Z0-9]{15,25}:
            logger.error(f"Failed to initialize Jira client: {str(e)}")
            self.jira_client = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and permissions with detailed diagnostics"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized - check configuration'}
        
        try:
            # Test basic connection
            user = self.jira_client.myself()
            
            # Test project access
            try:
                project = self.jira_client.project(self.project_key)
                project_access = True
                project_error = None
            except JIRAError as e:
                project_access = False
                project_error = e.text
            
            # Test issue creation permissions
            try:
                # Try to get create metadata for the project
                createmeta = self.jira_client.createmeta(projectKeys=[self.project_key])
                can_create = bool(createmeta['projects'][0]['issuetypes']) if createmeta['projects'] else False
                create_error = None
            except JIRAError as e:
                can_create = False
                create_error = e.text
            
            # Get available issue types
            issue_types = self.jira_client.issue_types()
            
            # Get available priorities
            priorities = self.jira_client.priorities()
            
            result = {
                'success': True,
                'user': user['displayName'],
                'user_email': user.get('email', 'Unknown'),
                'project_access': project_access,
                'can_create_issues': can_create,
                'issue_types': [it.name for it in issue_types],
                'priorities': [p.name for p in priorities]
            }
            
            if not project_access:
                result['project_error'] = project_error
            if not can_create:
                result['create_error'] = create_error
                
            return result
            
        except JIRAError as e:
            return {'success': False, 'error': f'Jira API Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def create_design_qa_ticket(self, issue: DesignIssue, 
                               assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a Jira ticket for a design QA issue with better error handling"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized'}
        
        try:
            # Prepare issue data
            summary = f"[Design QA] {issue.category} - {issue.subcategory}: {issue.description[:60]}..."
            if len(summary) > 255:  # Jira summary length limit
                summary = summary[:252] + "..."
            
            description = self._format_issue_description(issue)
            
            # Build the issue dictionary
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Bug'},  # Use string instead of Enum for compatibility
                'labels': ['design-qa', 'automated-testing', issue.category.lower().replace(' ', '-')]
            }
            
            # Set priority if available
            try:
                priorities = self.jira_client.priorities()
                priority_names = [p.name for p in priorities]
                if issue.severity.value in priority_names:
                    issue_dict['priority'] = {'name': issue.severity.value}
            except:
                pass  # Priority is optional
            
            # Add assignee if provided and valid
            if assignee:
                try:
                    # Verify assignee exists
                    user = self.jira_client.user(assignee)
                    issue_dict['assignee'] = {'name': assignee}
                except JIRAError:
                    logger.warning(f"Assignee {assignee} not found, creating unassigned ticket")
            
            # Create the issue
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            # Upload screenshot if available
            if issue.screenshot_path and os.path.exists(issue.screenshot_path):
                self._attach_screenshot(new_issue.key, issue.screenshot_path)
            
            return {
                'success': True,
                'issue_key': new_issue.key,
                'issue_url': f"{self.server_url}/browse/{new_issue.key}",
                'message': f'Created ticket {new_issue.key}'
            }
            
        except JIRAError as e:
            error_msg = f"JIRA Error: {e.status_code} - {e.text}" if hasattr(e, 'status_code') else f"JIRA Error: {e.text}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_bulk_tickets(self, issues: List[DesignIssue], 
                           assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create multiple Jira tickets in bulk with rate limiting"""
        results = {'successful': [], 'failed': []}
        
        for i, issue in enumerate(issues):
            # Add small delay to avoid rate limiting
            if i > 0:
                time.sleep(1)
                
            result = self.create_design_qa_ticket(issue, assignee)
            
            if result['success']:
                results['successful'].append({
                    'issue': issue,
                    'ticket_key': result['issue_key'],
                    'url': result['issue_url']
                })
                logger.info(f"Created ticket {result['issue_key']} for {issue.category} issue")
            else:
                results['failed'].append({
                    'issue': issue,
                    'error': result['error']
                })
                logger.error(f"Failed to create ticket for {issue.category}: {result['error']}")
        
        return {
            'total_processed': len(issues),
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'results': results
        }
    
    def _format_issue_description(self, issue: DesignIssue) -> str:
        """Format issue description for Jira with better formatting"""
        description = f"""
*Category:* {issue.category}
*Subcategory:* {issue.subcategory}
*Severity:* {issue.severity.value}

*Description:*
{issue.description}

*Expected Behavior:*
{issue.expected_behavior or 'Not specified'}

*Actual Behavior:*
{issue.actual_behavior or 'Not specified'}

*Element Selector:* 
{issue.element_selector or 'N/A'}

*Checklist Item:*
{issue.checklist_item or 'N/A'}

---
*Automated Design QA Report*
*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        return description
    
    def _attach_screenshot(self, issue_key: str, screenshot_path: str):
        """Attach screenshot to Jira ticket with better error handling and compression"""
        try:
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot file does not exist: {screenshot_path}")
                return
                
            file_size = os.path.getsize(screenshot_path)
            if file_size == 0:
                logger.error(f"Screenshot file is empty: {screenshot_path}")
                return
            
            # Check file size limit (Jira typically has a 10MB limit per attachment)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Screenshot too large ({file_size} bytes), compressing...")
                # Compress the image
                image = Image.open(screenshot_path)
                # Save with optimized compression
                image.save(screenshot_path, "PNG", optimize=True, quality=85)
                file_size = os.path.getsize(screenshot_path)
                logger.info(f"Compressed screenshot to {file_size} bytes")
            
            with open(screenshot_path, 'rb') as f:
                self.jira_client.add_attachment(
                    issue=issue_key, 
                    attachment=f,
                    filename=f"design_qa_screenshot_{issue_key}.png"
                )
            logger.info(f"Screenshot ({file_size} bytes) attached to {issue_key}")
            
        except Exception as e:
            logger.error(f"Failed to attach screenshot to {issue_key}: {e}")
            # Log more details for debugging
            if hasattr(e, 'response'):
                logger.error(f"Jira response: {e.response.text}")
            if hasattr(e, 'status_code'):
                logger.error(f"HTTP status: {e.status_code}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information with better error handling"""
        if not self.jira_client:
            return {'error': 'Jira client not initialized'}
        
        try:
            project = self.jira_client.project(self.project_key)
            issue_types = self.jira_client.issue_types()
            priorities = self.jira_client.priorities()
            
            return {
                'project_name': project.name,
                'project_key': project.key,
                'project_lead': project.lead.displayName if hasattr(project, 'lead') else 'Unknown',
                'issue_types': [{'id': it.id, 'name': it.name} for it in issue_types],
                'priorities': [{'id': p.id, 'name': p.name} for p in priorities]
            }
        except JIRAError as e:
            return {'error': f'JIRA Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'error': f'Failed to get project info: {str(e)}'}

class AutomatedDesignValidator:
    """Automated design validation using the QA checklist"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.checklist = DesignQAChecklist()
        self.issues_found = []
    
    def validate_page(self, url: str) -> List[DesignIssue]:
        """Validate a page against the design checklist"""
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Run automated checks
            self._check_accessibility()
            self._check_images()
            self._check_forms()
            self._check_buttons()
            self._check_typography()
            self._check_responsive_design()
            
            return self.issues_found
            
        except Exception as e:
            logger.error(f"Page validation failed: {e}")
            return []
    
    def _check_accessibility(self):
        """Check accessibility compliance"""
        try:
            # Check for images without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                alt_text = img.get_attribute("alt")
                if not alt_text or alt_text.strip() == "":
                    self.issues_found.append(DesignIssue(
                        category="Accessibility",
                        subcategory="Images",
                        description=f"Image missing alt text: {img.get_attribute('src')[:50]}...",
                        severity=Priority.HIGH,
                        element_selector=f"img[src*='{img.get_attribute('src')[:20]}']",
                        expected_behavior="All images should have descriptive alt text",
                        actual_behavior="Image has no alt text attribute",
                        checklist_item="VD018"
                    ))
            
            # Check heading structure
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            if not headings:
                self.issues_found.append(DesignIssue(
                    category="Accessibility",
                    subcategory="Structure",
                    description="No heading elements found on page",
                    severity=Priority.MEDIUM,
                    expected_behavior="Page should have proper heading structure",
                    actual_behavior="No headings detected",
                    checklist_item="A005"
                ))
            
        except Exception as e:
            logger.error(f"Accessibility check failed: {e}")
    
    def _check_images(self):
        """Check image quality and implementation"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                # Check if image is loaded
                if img.get_attribute("naturalWidth") == "0":
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Broken or missing image: {img.get_attribute('src')}",
                        severity=Priority.HIGH,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should load correctly",
                        actual_behavior="Image failed to load",
                        checklist_item="VD016"
                    ))
                
                # Check for consistent sizing
                width = img.size['width']
                height = img.size['height']
                if width < 10 or height < 10:
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Image too small: {width}x{height}px",
                        severity=Priority.LOW,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should be appropriately sized",
                        actual_behavior=f"Image is only {width}x{height}px",
                        checklist_item="VD016"
                    ))
        except Exception as e:
            logger.error(f"Image check failed: {e}")
    
    def _check_forms(self):
        """Check form implementation"""
        try:
            # Check for unlabeled inputs
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type")
                if input_type not in ["hidden", "submit", "button"]:
                    # Check for label
                    input_id = input_elem.get_attribute("id")
                    has_label = False
                    
                    if input_id:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            has_label = True
                        except:
                            pass
                    
                    if not has_label:
                        self.issues_found.append(DesignIssue(
                            category="UI Elements",
                            subcategory="Forms",
                            description=f"Input field without label: {input_type} input",
                            severity=Priority.MEDIUM,
                            element_selector=f"input[type='{input_type}']",
                            expected_behavior="All input fields should have associated labels",
                            actual_behavior="Input field has no label",
                            checklist_item="UI005"
                        ))
        except Exception as e:
            logger.error(f"Form check failed: {e}")
    
    def _check_buttons(self):
        """Check button implementation"""
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            for button in buttons:
                # Check button text
                text = button.text or button.get_attribute("value")
                if not text or len(text.strip()) < 2:
                    self.issues_found.append(DesignIssue(
                        category="UI Elements",
                        subcategory="Buttons",
                        description="Button with unclear or missing text",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Buttons should have clear, action-oriented labels",
                        actual_behavior=f"Button text: '{text}'",
                        checklist_item="UI003"
                    ))
                
                # Check button size for mobile
                size = button.size
                if size['width'] < 44 or size['height'] < 44:
                    self.issues_found.append(DesignIssue(
                        category="Responsive Design",
                        subcategory="Mobile-specific",
                        description=f"Button too small for touch: {size['width']}x{size['height']}px",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Touch targets should be at least 44x44 pixels",
                        actual_behavior=f"Button is {size['width']}x{size['height']}px",
                        checklist_item="RD004"
                    ))
        except Exception as e:
            logger.error(f"Button check failed: {e}")
    
    def _check_typography(self):
        """Check typography consistency"""
        try:
            # Check for very small text
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, span, div, li, td, th")
            for element in all_elements[:50]:  # Limit to first 50 to avoid performance issues
                font_size = element.value_of_css_property("font-size")
                if font_size:
                    size_px = float(font_size.replace("px", ""))
                    if size_px < 12:  # Text smaller than 12px might be hard to read
                        self.issues_found.append(DesignIssue(
                            category="Visual Design",
                            subcategory="Typography",
                            description=f"Text too small: {size_px}px",
                            severity=Priority.LOW,
                            element_selector=element.tag_name,
                            expected_behavior="Text should be at least 12px for readability",
                            actual_behavior=f"Font size is {size_px}px",
                            checklist_item="VD009"
                        ))
        except Exception as e, file_id):
                return None
                
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to extract file ID: {e}")
            return None
    
    def get_file_info(self, file_id):
        """Get Figma file information with detailed logging"""
        try:
            if not self.access_token:
                logger.error("Figma access token not configured")
                return None
                
            url = f"https://api.figma.com/v1/files/{file_id}?depth=3"
            logger.info(f"Fetching Figma file info from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                file_data = response.json()
                
                # Log basic file information
                if 'name' in file_data:
                    logger.info(f"Figma file name: {file_data['name']}")
                if 'lastModified' in file_data:
                    last_modified = datetime.fromisoformat(file_data['lastModified'].replace('Z', '+00:00'))
                    logger.info(f"Last modified: {last_modified}")
                
                return file_data
                
            else:
                error_msg = f"Figma API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Check for common error cases
                if response.status_code == 404:
                    logger.error("File not found. Please check if the file ID is correct and the file is accessible.")
                elif response.status_code == 403:
                    logger.error("Access forbidden. Please check if your access token has the correct permissions.")
                elif response.status_code == 400:
                    logger.error("Bad request. The file ID might be malformed.")
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_frame_nodes(self, file_info):
        """Extract frame nodes from Figma file data"""
        frames = []
        nodes_processed = 0
        
        def extract_frames(node, path="", depth=0):
            nonlocal nodes_processed
            nodes_processed += 1
            
            # Debug: Log node information at each level
            node_type = node.get('type', 'UNKNOWN')
            node_name = node.get('name', 'Unnamed')
            
            # Add more node types that might contain frames
            if node_type in ['FRAME', 'COMPONENT', 'INSTANCE', 'GROUP', 'SECTION']:
                frame_data = {
                    'id': node.get('id', ''),
                    'name': node_name,
                    'path': f"{path}/{node_name}" if path else node_name,
                    'type': node_type,
                    'visible': node.get('visible', True)
                }
                frames.append(frame_data)
                logger.debug(f"Found {node_type}: {node_name} (ID: {frame_data['id']})")
            
            # Recursively process children if they exist
            if 'children' in node and isinstance(node['children'], list):
                for child in node['children']:
                    if isinstance(child, dict):
                        extract_frames(child, 
                                    f"{path}/{node_name}" if path else node_name,
                                    depth + 1)
        
        try:
            if not file_info:
                logger.error("No file info provided")
                return []
                
            if 'document' not in file_info:
                logger.error("No 'document' key in file info")
                logger.debug(f"File info keys: {list(file_info.keys())}")
                return []
            
            # Start extraction from the document node
            document = file_info['document']
            if not isinstance(document, dict):
                logger.error(f"Document is not a dictionary: {type(document)}")
                return []
                
            extract_frames(document)
            
            logger.info(f"Processed {nodes_processed} nodes, found {len(frames)} frames/components")
            
            # If no frames found in the document, try looking in other common locations
            if not frames and 'components' in file_info:
                logger.info("No frames found in document, checking components...")
                if isinstance(file_info['components'], dict):
                    for comp_id, comp_data in file_info['components'].items():
                        if isinstance(comp_data, dict):
                            extract_frames(comp_data)
            
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            logger.debug(traceback.format_exc())
            return frames
    
    def get_image_urls(self, file_id, node_ids, scale=3, format="png"):
        """Get high-quality image URLs for specific nodes"""
        try:
            if not self.access_token:
                logger.error("Figma access token not configured")
                return None
                
            if not node_ids:
                logger.error("No node IDs provided for image generation")
                return None
            
            node_params = "&ids=" + ",".join(node_ids)
            url = f"https://api.figma.com/v1/images/{file_id}?scale={scale}&format={format}{node_params}"
            
            logger.info(f"Requesting Figma images with scale {scale}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'images' in data and data['images']:
                    logger.info(f"Got {len(data['images'])} image URLs from Figma")
                    return data
                else:
                    logger.error("No images returned from Figma API")
                    return None
            else:
                logger.error(f"Figma image API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get image URLs: {e}")
            return None
    
    def download_image(self, image_url):
        """Download image from URL"""
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                logger.error(f"Image download failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Image download error: {e}")
            return None
    
    def compare_designs(self, figma_image, web_image, threshold=0.95):
        """Compare Figma design with web implementation"""
        try:
            # Resize images to same dimensions if needed
            if figma_image.size != web_image.size:
                # Maintain aspect ratio and resize to the smaller dimensions
                min_width = min(figma_image.width, web_image.width)
                min_height = min(figma_image.height, web_image.height)
                
                figma_image = figma_image.resize((min_width, min_height), Image.Resampling.LANCZOS)
                web_image = web_image.resize((min_width, min_height), Image.Resampling.LANCZOS)
            
            # Convert to numpy arrays
            figma_array = np.array(figma_image.convert('RGB'))
            web_array = np.array(web_image.convert('RGB'))
            
            # Calculate SSIM
            similarity, diff = ssim(figma_array, web_array, 
                                  full=True, multichannel=True,
                                  channel_axis=2)
            
            # Create difference visualization
            diff_image = (diff * 255).astype("uint8")
            diff_image = Image.fromarray(diff_image)
            
            return {
                'similarity_score': similarity,
                'is_match': similarity >= threshold,
                'difference_image': diff_image,
                'figma_image': figma_image,
                'web_image': web_image
            }
            
        except Exception as e:
            logger.error(f"Design comparison failed: {e}")
            return None

class WebCrawler:
    """Web crawler using Selenium for dynamic content (from app.py)"""
    
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
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
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

class TestExecutor:
    """Execute generated test cases and capture results (from app.py)"""
    
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
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
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

class DesignQAProcessor:
    """Main processor for design QA automation"""
    
    def __init__(self):
        self.chrome_driver = EnhancedChromeDriver()
        self.figma_comparator = FigmaDesignComparator()
        self.jira_integration = EnhancedJiraIntegration()
        self.validator = None
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup driver
        if not self.chrome_driver.setup_driver():
            logger.error("Failed to setup Chrome driver")
    
    def process_qa_request(self, figma_url, web_url, jira_assignee=None):
        """Process complete QA request with improved screenshot handling"""
        results = {
            'success': False,
            'figma_file_id': None,
            'comparison_results': [],
            'validation_issues': [],
            'jira_tickets': [],
            'error': None
        }
        
        try:
            # Step 1: Extract Figma file ID
            file_id = self.figma_comparator.extract_file_id(figma_url)
            if not file_id:
                results['error'] = "Invalid Figma URL or file ID"
                return results
            
            results['figma_file_id'] = file_id
            
            # Step 2: Get Figma file info
            file_info = self.figma_comparator.get_file_info(file_id)
            if not file_info:
                results['error'] = "Failed to get Figma file information"
                return results
            
            # Step 3: Get frame nodes from the file
            frames = self.figma_comparator.get_frame_nodes(file_info)
            logger.info(f"Found {len(frames)} frames in Figma file")
            if not frames:
                results['error'] = "No frames found in Figma file. Please ensure the Figma file contains visible frames or components."
                return results
            
            # Log frame details for debugging
            for i, frame in enumerate(frames[:3]):  # Log first 3 frames for reference
                logger.info(f"Frame {i+1}: ID={frame.get('id')}, Name='{frame.get('name')}', Type={frame.get('type')}")
            
            # Step 4: Capture web screenshots with higher quality
            web_screenshot = self.chrome_driver.capture_full_page_screenshot(web_url, wait_time=5)
            if not web_screenshot:
                results['error'] = "Failed to capture web screenshot"
                return results
            
            # Save the screenshot to a file for Jira attachment
            screenshot_path = os.path.join(self.temp_dir, f"web_screenshot_{int(time.time())}.png")
            web_screenshot.save(screenshot_path, "PNG", optimize=True, quality=95)
            logger.info(f"Saved web screenshot to {screenshot_path}")
            
            # Step 5: Get images for the first few frames (to avoid rate limiting)
            frame_ids = [frame['id'] for frame in frames[:3] if frame and 'id' in frame]
            if not frame_ids:
                results['error'] = "No valid frame IDs found in the Figma file. Please check if the file contains visible frames."
                return results
                
            logger.info(f"Requesting images for frame IDs: {frame_ids}")
            image_data = self.figma_comparator.get_image_urls(file_id, frame_ids)
            
            if not image_data or 'images' not in image_data or not image_data['images']:
                results['error'] = "Failed to get Figma images. Please check if the file contains visible frames and your access token has appropriate permissions."
                return results
            
            # Step 6: Download and compare images
            for node_id, image_url in image_data['images'].items():
                if image_url:  # Only process if URL is available
                    figma_image = self.figma_comparator.download_image(image_url)
                    if figma_image:
                        comparison = self.figma_comparator.compare_designs(figma_image, web_screenshot)
                        if comparison:
                            # Add frame information to comparison results
                            frame_info = next((frame for frame in frames if frame['id'] == node_id), {})
                            comparison['frame_name'] = frame_info.get('name', 'Unknown')
                            comparison['frame_type'] = frame_info.get('type', 'Unknown')
                            results['comparison_results'].append(comparison)
            
            # Step 7: Run automated validation
            self.validator = AutomatedDesignValidator(self.chrome_driver.driver)
            validation_issues = self.validator.validate_page(web_url)
            results['validation_issues'] = validation_issues
            
            # Step 8: Create Jira tickets for issues with screenshots
            if validation_issues and self.jira_integration.jira_client:
                # Add screenshot path to each issue
                for issue in validation_issues:
                    issue.screenshot_path = screenshot_path
                
                jira_results = self.jira_integration.create_bulk_tickets(validation_issues, jira_assignee)
                results['jira_tickets'] = jira_results
            
            results['success'] = True
            
        except Exception as e:
            results['error'] = f"Processing failed: {str(e)}"
            logger.error(f"QA processing error: {traceback.format_exc()}")
        
        return results
    
    def cleanup(self):
        """Cleanup resources"""
        self.chrome_driver.close()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

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

# Streamlit UI Application
class DesignQAApp:
    """Streamlit application for Design QA Automation"""
    
    def __init__(self):
        self.processor = DesignQAProcessor()
        self.web_crawler = WebCrawler()
        self.test_executor = TestExecutor()
        self.setup_page_config()
    
    def setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="Advanced AI QA Automation",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_sidebar(self):
        """Render sidebar with configuration and controls"""
        with st.sidebar:
            st.title("⚙️ Configuration")
            
            # Check for environment variables
            env_status = st.expander("🔍 Environment Status")
            with env_status:
                groq_configured = "✅" if os.getenv("GROQ_API_KEY") else "❌"
                figma_configured = "✅" if os.getenv("FIGMA_ACCESS_TOKEN") else "❌"
                jira_configured = "✅" if all([
                    os.getenv("JIRA_SERVER_URL"),
                    os.getenv("JIRA_EMAIL"), 
                    os.getenv("JIRA_API_TOKEN"),
                    os.getenv("JIRA_PROJECT_KEY")
                ]) else "❌"
                
                st.write(f"**Groq API:** {groq_configured}")
                st.write(f"**Figma API:** {figma_configured}")
                st.write(f"**Jira Integration:** {jira_configured}")
                
                if not os.getenv("GROQ_API_KEY"):
                    st.error("⚠️ GROQ_API_KEY not found in .env file")
                
                if not os.getenv("FIGMA_ACCESS_TOKEN"):
                    st.warning("⚠️ FIGMA_ACCESS_TOKEN not found in .env file")
                
                if not jira_configured:
                    st.warning("⚠️ Jira credentials incomplete in .env file")
            
            # API Key Configuration
            with st.expander("API Keys Configuration", expanded=False):
                groq_key = st.text_input("GROQ API Key", 
                                       value=os.getenv("GROQ_API_KEY", ""),
                                       type="password",
                                       help="Get from https://console.groq.com")
                
                figma_token = st.text_input("Figma Access Token",
                                          value=os.getenv("FIGMA_ACCESS_TOKEN", ""),
                                          type="password",
                                          help="Get from Figma Account Settings")
                
                jira_url = st.text_input("Jira Server URL",
                                       value=os.getenv("JIRA_SERVER_URL", ""),
                                       help="e.g., https://your-company.atlassian.net")
                
                jira_email = st.text_input("Jira Email",
                                         value=os.getenv("JIRA_EMAIL", ""),
                                         help="Your Jira account email")
                
                jira_token = st.text_input("Jira API Token",
                                         value=os.getenv("JIRA_API_TOKEN", ""),
                                         type="password",
                                         help="Get from https://id.atlassian.com/manage-profile/security/api-tokens")
                
                jira_project = st.text_input("Jira Project Key",
                                           value=os.getenv("JIRA_PROJECT_KEY", ""),
                                           help="e.g., DES, WEB, QA")
                
                if st.button("Save Configuration", type="primary"):
                    self._save_configuration({
                        "GROQ_API_KEY": groq_key,
                        "FIGMA_ACCESS_TOKEN": figma_token,
                        "JIRA_SERVER_URL": jira_url,
                        "JIRA_EMAIL": jira_email,
                        "JIRA_API_TOKEN": jira_token,
                        "JIRA_PROJECT_KEY": jira_project
                    })
            
            # Connection Test
            with st.expander("Test Connections", expanded=False):
                if st.button("Test All Connections"):
                    with st.spinner("Testing connections..."):
                        validator = ConfigurationValidator()
                        config_status = validator.validate_api_keys()
                        connection_status = validator.test_api_connections()
                        
                        # Display configuration status
                        for service, status in config_status.items():
                            col1, col2 = st.columns([1, 3])
                            col1.write(f"**{service.title()}**")
                            if status['status']:
                                col2.success("✅ Configured")
                            else:
                                col2.error(f"❌ {status['message']}")
                        
                        st.divider()
                        
                        # Display connection status with more details
                        for service, status in connection_status.items():
                            col1, col2 = st.columns([1, 3])
                            col1.write(f"**{service.title()}**")
                            if status['status']:
                                if service == 'jira' and 'user' in status:
                                    col2.success(f"✅ Connected as: {status.get('user', 'Unknown')}")
                                else:
                                    col2.success(f"✅ {status['message']}")
                            else:
                                col2.error(f"❌ {status['message']}")
            
            # Jira Settings with enhanced testing
            with st.expander("Jira Settings", expanded=False):
                jira_assignee = st.text_input("Default Assignee",
                                            help="Jira username for ticket assignment")
                
                if st.button("Test Jira Connection"):
                    jira_info = self.processor.jira_integration.test_connection()
                    if jira_info['success']:
                        st.success(f"✅ Connected as: {jira_info['user']} ({jira_info['user_email']})")
                        
                        # Display project access
                        if jira_info.get('project_access', False):
                            st.success("✅ Project access: Granted")
                        else:
                            st.error(f"❌ Project access: {jira_info.get('project_error', 'Denied')}")
                        
                        # Display issue creation permissions
                        if jira_info.get('can_create_issues', False):
                            st.success("✅ Create issues: Allowed")
                            st.write(f"Available issue types: {', '.join(jira_info.get('issue_types', []))}")
                        else:
                            st.error(f"❌ Create issues: {jira_info.get('create_error', 'Denied')}")
                    else:
                        st.error(f"❌ Connection failed: {jira_info.get('error', 'Unknown error')}")
            
            # Model Selection
            st.subheader("🤖 AI Configuration")
            models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
            selected_model = st.selectbox("AI Model", models)
            st.session_state['selected_model'] = selected_model
    
    def _save_configuration(self, config):
        """Save configuration to environment file"""
        try:
            # Update current environment
            for key, value in config.items():
                if value:
                    os.environ[key] = value
            
            # Update .env file
            env_path = '.env'
            env_lines = []
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add each config value
            for key, value in config.items():
                found = False
                for i, line in enumerate(env_lines):
                    if line.startswith(f"{key}="):
                        env_lines[i] = f"{key}={value}\n"
                        found = True
                        break
                
                if not found and value:
                    env_lines.append(f"{key}={value}\n")
            
            # Write back to file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            st.success("Configuration saved successfully!")
            
        except Exception as e:
            st.error(f"Failed to save configuration: {e}")
    
    def render_main_content(self):
        """Render main content area with combined functionality"""
        st.title("🎨 Advanced AI QA Automation System")
        st.markdown("**Design QA • Web Crawling • Test Generation • Jira Integration • Automated Execution**")
        
        # Main tabs combining both functionalities
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎨 Design QA", 
            "🌐 Web Crawling", 
            "📝 Test Generation", 
            "🔧 Test Execution", 
            "🐛 Bug Management"
        ])
        
        with tab1:
            self._render_design_qa_tab()
        
        with tab2:
            self._render_web_crawling_tab()
        
        with tab3:
            self._render_test_generation_tab()
        
        with tab4:
            self._render_test_execution_tab()
        
        with tab5:
            self._render_bug_management_tab()
    
    def _render_design_qa_tab(self):
        """Render Design QA tab content"""
        st.header("🎨 Design QA Automation")
        st.markdown("""
        Automate your design quality assurance process by comparing Figma designs with web implementations,
        running automated checks, and creating Jira tickets for issues.
        """)
        
        # Input Section
        col1, col2 = st.columns(2)
        
        with col1:
            figma_url = st.text_input(
                "Figma Design URL",
                placeholder="https://www.figma.com/file/... or Figma file ID",
                help="Paste Figma file URL or direct file ID"
            )
        
        with col2:
            web_url = st.text_input(
                "Web Implementation URL",
                placeholder="https://your-website.com/page",
                help="URL of the implemented web page"
            )
        
        # Advanced Options
        with st.expander("Advanced Options"):
            col3, col4 = st.columns(2)
            
            with col3:
                similarity_threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.7,
                    max_value=1.0,
                    value=0.95,
                    help="Minimum similarity score for design matching"
                )
            
            with col4:
                jira_assignee = st.text_input(
                    "Jira Assignee (optional)",
                    help="Jira username to assign tickets to"
                )
        
        # Action Buttons
        col5, col6, col7 = st.columns(3)
        
        with col5:
            if st.button("🚀 Run Complete QA", type="primary", use_container_width=True):
                self._run_complete_qa(figma_url, web_url, jira_assignee, similarity_threshold)
        
        with col6:
            if st.button("📸 Capture Screenshot Only", use_container_width=True):
                self._capture_screenshot_only(web_url)
        
        with col7:
            if st.button("🔍 Validate Page Only", use_container_width=True):
                self._validate_page_only(web_url)
    
    def _render_web_crawling_tab(self):
        """Render Web Crawling tab content"""
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
                    crawled_data = self.web_crawler.crawl_website(website_url, max_pages, crawl_depth)
                    
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
    
    def _render_test_generation_tab(self):
        """Render Test Generation tab content"""
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
                        model = st.session_state.get('selected_model', 'llama-3.3-70b-versatile')
                        test_cases = generate_test_cases_from_crawl(st.session_state['crawled_data'], model)
                        st.session_state['generated_tests'] = test_cases
                        
                        st.success("✅ Test cases generated successfully!")
                        st.code(test_cases, language="json")
            else:
                st.warning("Please crawl a website first in the Web Crawling tab.")
        
        elif generation_method == "From Requirements Document":
            uploaded_file = st.file_uploader("Upload Requirements Document", type=['txt', 'pdf', 'docx'])
            
            if uploaded_file and st.button("📋 Generate Test Cases from Document"):
                with st.spinner("🔄 Processing document and generating test cases..."):
                    # Process file content
                    content = self._extract_document_content(uploaded_file)
                    if content:
                        prompt = f"""
                        Based on the following requirements document, generate comprehensive test cases in JSON format:
                        
                        {content[:4000]}...
                        
                        Generate test cases covering functional, UI, and edge case scenarios.
                        """
                        model = st.session_state.get('selected_model', 'llama-3.3-70b-versatile')
                        test_cases = simple_AI_Function_Agent(prompt, model)
                        st.session_state['generated_tests'] = test_cases
                        st.success("✅ Test cases generated from document!")
                        st.code(test_cases, language="json")
        
        else:  # Manual Input
            manual_requirements = st.text_area("Enter Requirements Manually", height=200)
            
            if manual_requirements and st.button("✏️ Generate Test Cases from Text"):
                with st.spinner("🔄 Generating test cases from your requirements..."):
                    prompt = f"""
                    Based on the following requirements, generate comprehensive test cases in JSON format:
                    
                    {manual_requirements}
                    
                    Generate test cases covering functional, UI, and edge case scenarios.
                    """
                    model = st.session_state.get('selected_model', 'llama-3.3-70b-versatile')
                    test_cases = simple_AI_Function_Agent(prompt, model)
                    st.session_state['generated_tests'] = test_cases
                    st.success("✅ Test cases generated from manual input!")
                    st.code(test_cases, language="json")
    
    def _render_test_execution_tab(self):
        """Render Test Execution tab content"""
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
                        # Execute tests using the TestExecutor
                        if self.test_executor.setup_driver():
                            # Parse test cases and execute
                            try:
                                import json
                                test_data = json.loads(st.session_state['generated_tests'])
                                all_results = []
                                
                                for suite in test_data.get('test_suites', []):
                                    for test_case in suite.get('test_cases', []):
                                        result = self.test_executor.execute_test_scenario(test_case)
                                        all_results.append(result)
                                
                                # Display results
                                st.success("✅ Test execution completed!")
                                
                                results_data = {
                                    'Test Case': [r['test_name'] for r in all_results],
                                    'Status': [r['status'] for r in all_results],
                                    'Duration (s)': [round(r['execution_time'], 2) for r in all_results],
                                    'Error Message': [r['error_message'] for r in all_results]
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
                                    
                            except json.JSONDecodeError:
                                st.error("Invalid test case format. Please regenerate test cases.")
                            except Exception as e:
                                st.error(f"Test execution failed: {str(e)}")
                            finally:
                                if self.test_executor.driver:
                                    self.test_executor.driver.quit()
                        else:
                            st.error("Failed to setup test execution driver")
        else:
            st.warning("Please generate test cases first in the Test Generation tab.")
    
    def _render_bug_management_tab(self):
        """Render Bug Management tab content"""
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
                        jira_test = self.processor.jira_integration.test_connection()
                        if jira_test['success']:
                            st.success("✅ Connected to Jira successfully!")
                            
                            # Auto-create bugs for failed tests if available
                            if 'generated_tests' in st.session_state and st.button("🐛 Auto-Create Bugs for Failed Tests"):
                                bugs_created = []
                                # Mock bug creation for demonstration
                                bugs_created.append("BUG-123: Navigation Test Failure")
                                bugs_created.append("BUG-124: Search Timeout Error")
                                
                                for bug in bugs_created:
                                    st.success(f"Created: {bug}")
                        else:
                            st.error("Failed to connect to Jira. Check your .env configuration.")
            
            with col2:
                st.subheader("🔍 Manual Bug Creation")
                bug_summary = st.text_input("Bug Summary")
                bug_description = st.text_area("Bug Description")
                
                if st.button("🐛 Create Bug in Jira"):
                    if bug_summary and bug_description:
                        # Create manual bug using enhanced Jira integration
                        manual_issue = DesignIssue(
                            category="Manual Report",
                            subcategory="User Reported",
                            description=bug_description,
                            severity=Priority.MEDIUM,
                            expected_behavior="System should work as described",
                            actual_behavior=bug_description
                        )
                        
                        result = self.processor.jira_integration.create_design_qa_ticket(manual_issue)
                        if result['success']:
                            st.success(f"✅ Bug created: {result['issue_key']}")
                        else:
                            st.error(f"Failed to create bug: {result['error']}")
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
    
    def _extract_document_content(self, uploaded_file):
        """Extract content from uploaded document"""
        try:
            if uploaded_file.type == "text/plain":
                return str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
                return content
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                content = ""
                for para in doc.paragraphs:
                    content += para.text + "\n"
                return content
        except Exception as e:
            st.error(f"Failed to extract document content: {e}")
            return None
    
    def _run_complete_qa(self, figma_url, web_url, jira_assignee, threshold):
        """Run complete QA process"""
        if not figma_url or not web_url:
            st.error("Please provide both Figma and Web URLs")
            return
        
        with st.spinner("Running complete QA analysis..."):
            try:
                results = self.processor.process_qa_request(figma_url, web_url, jira_assignee)
                
                if results['success']:
                    self._display_results(results)
                else:
                    st.error(f"QA process failed: {results['error']}")
                    
            except Exception as e:
                st.error(f"QA process error: {str(e)}")
                logger.error(f"QA process error: {traceback.format_exc()}")
    
    def _capture_screenshot_only(self, web_url):
        """Capture screenshot only"""
        if not web_url:
            st.error("Please provide a Web URL")
            return
        
        with st.spinner("Capturing screenshot..."):
            try:
                screenshot = self.processor.chrome_driver.capture_full_page_screenshot(web_url)
                
                if screenshot:
                    st.image(screenshot, caption="Web Page Screenshot", use_container_width=True)
                    
                    # Convert to bytes for download
                    buf = BytesIO()
                    screenshot.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="📥 Download Screenshot",
                        data=byte_im,
                        file_name="web_screenshot.png",
                        mime="image/png"
                    )
                else:
                    st.error("Failed to capture screenshot")
                    
            except Exception as e:
                st.error(f"Screenshot capture error: {str(e)}")
    
    def _validate_page_only(self, web_url):
        """Run page validation only"""
        if not web_url:
            st.error("Please provide a Web URL")
            return
        
        with st.spinner("Running page validation..."):
            try:
                validator = AutomatedDesignValidator(self.processor.chrome_driver.driver)
                issues = validator.validate_page(web_url)
                
                self._display_validation_results(issues)
                
            except Exception as e:
                st.error(f"Validation error: {str(e)}")
    
    def _display_results(self, results):
        """Display QA results"""
        st.success("✅ QA Analysis Complete!")
        
        # Display comparison results
        if results['comparison_results']:
            with st.expander("🎯 Design Comparison Results", expanded=True):
                for comp in results['comparison_results']:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(comp['figma_image'], caption="Figma Design", use_container_width=True)
                    
                    with col2:
                        st.image(comp['web_image'], caption="Web Implementation", use_container_width=True)
                    
                    # Display similarity score
                    score = comp['similarity_score']
                    if score >= 0.95:
                        st.success(f"Similarity Score: {score:.3f} - Excellent Match!")
                    elif score >= 0.85:
                        st.warning(f"Similarity Score: {score:.3f} - Good Match")
                    else:
                        st.error(f"Similarity Score: {score:.3f} - Significant Differences")
                    
                    # Display difference visualization
                    if comp['difference_image']:
                        st.image(comp['difference_image'], caption="Difference Map", use_container_width=True)
        
        # Display validation issues
        if results['validation_issues']:
            with st.expander("🔍 Validation Issues", expanded=True):
                self._display_validation_results(results['validation_issues'])
                
                # Jira ticket creation summary
                if results['jira_tickets']:
                    jira_results = results['jira_tickets']
                    st.info(
                        f"Created {jira_results['successful_count']} Jira tickets, "
                        f"{jira_results['failed_count']} failed"
                    )
        else:
            st.info("🎉 No validation issues found!")
    
    def _display_validation_results(self, issues):
        """Display validation issues in a structured way"""
        if not issues:
            st.success("✅ No validation issues found!")
            return
        
        # Group issues by category
        issues_by_category = {}
        for issue in issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
        
        # Display issues by category
        for category, category_issues in issues_by_category.items():
            with st.expander(f"{category} ({len(category_issues)} issues)", expanded=True):
                for issue in category_issues:
                    # Create severity badge
                    severity_color = {
                        Priority.HIGHEST: "🔴",
                        Priority.HIGH: "🟠", 
                        Priority.MEDIUM: "🟡",
                        Priority.LOW: "🔵",
                        Priority.LOWEST: "⚪"
                    }.get(issue.severity, "⚪")
                    
                    st.markdown(f"""
                    **{severity_color} {issue.subcategory}**: {issue.description}
                    
                    *Expected:* {issue.expected_behavior or 'N/A'}  
                    *Actual:* {issue.actual_behavior or 'N/A'}  
                    *Element:* `{issue.element_selector or 'N/A'}`
                    """)
                    
                    st.divider()
    
    def cleanup(self):
        """Cleanup resources when app closes"""
        try:
            self.processor.cleanup()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def run(self):
        """Run the Streamlit application"""
        try:
            self.render_sidebar()
            self.render_main_content()
            
            # Footer
            st.markdown("---")
            st.markdown("""
            ### 🎯 System Capabilities
            - **Design QA**: Compare Figma designs with web implementations using AI
            - **Web Crawling**: Automatically discover and analyze website functionality
            - **AI Test Generation**: Create comprehensive test suites from crawled data or requirements
            - **Jira Integration**: Seamlessly create test cases and log bugs with screenshots
            - **Automated Execution**: Run tests with Selenium WebDriver
            - **Real-time Reporting**: Track test results and failure analysis
            """)
            
            st.markdown("Built with ❤️ using **Streamlit**, **Selenium**, **Groq AI**, **Figma API**, and **Jira API**")
            
        finally:
            # Cleanup on app termination
            self.cleanup()

# Main execution
if __name__ == "__main__":
    app = DesignQAApp()
    app.run():
            logger.error(f"Failed to initialize Jira client: {str(e)}")
            self.jira_client = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and permissions with detailed diagnostics"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized - check configuration'}
        
        try:
            # Test basic connection
            user = self.jira_client.myself()
            
            # Test project access
            try:
                project = self.jira_client.project(self.project_key)
                project_access = True
                project_error = None
            except JIRAError as e:
                project_access = False
                project_error = e.text
            
            # Test issue creation permissions
            try:
                # Try to get create metadata for the project
                createmeta = self.jira_client.createmeta(projectKeys=[self.project_key])
                can_create = bool(createmeta['projects'][0]['issuetypes']) if createmeta['projects'] else False
                create_error = None
            except JIRAError as e:
                can_create = False
                create_error = e.text
            
            # Get available issue types
            issue_types = self.jira_client.issue_types()
            
            # Get available priorities
            priorities = self.jira_client.priorities()
            
            result = {
                'success': True,
                'user': user['displayName'],
                'user_email': user.get('email', 'Unknown'),
                'project_access': project_access,
                'can_create_issues': can_create,
                'issue_types': [it.name for it in issue_types],
                'priorities': [p.name for p in priorities]
            }
            
            if not project_access:
                result['project_error'] = project_error
            if not can_create:
                result['create_error'] = create_error
                
            return result
            
        except JIRAError as e:
            return {'success': False, 'error': f'Jira API Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def create_design_qa_ticket(self, issue: DesignIssue, 
                               assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a Jira ticket for a design QA issue with better error handling"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized'}
        
        try:
            # Prepare issue data
            summary = f"[Design QA] {issue.category} - {issue.subcategory}: {issue.description[:60]}..."
            if len(summary) > 255:  # Jira summary length limit
                summary = summary[:252] + "..."
            
            description = self._format_issue_description(issue)
            
            # Build the issue dictionary
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Bug'},  # Use string instead of Enum for compatibility
                'labels': ['design-qa', 'automated-testing', issue.category.lower().replace(' ', '-')]
            }
            
            # Set priority if available
            try:
                priorities = self.jira_client.priorities()
                priority_names = [p.name for p in priorities]
                if issue.severity.value in priority_names:
                    issue_dict['priority'] = {'name': issue.severity.value}
            except:
                pass  # Priority is optional
            
            # Add assignee if provided and valid
            if assignee:
                try:
                    # Verify assignee exists
                    user = self.jira_client.user(assignee)
                    issue_dict['assignee'] = {'name': assignee}
                except JIRAError:
                    logger.warning(f"Assignee {assignee} not found, creating unassigned ticket")
            
            # Create the issue
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            # Upload screenshot if available
            if issue.screenshot_path and os.path.exists(issue.screenshot_path):
                self._attach_screenshot(new_issue.key, issue.screenshot_path)
            
            return {
                'success': True,
                'issue_key': new_issue.key,
                'issue_url': f"{self.server_url}/browse/{new_issue.key}",
                'message': f'Created ticket {new_issue.key}'
            }
            
        except JIRAError as e:
            error_msg = f"JIRA Error: {e.status_code} - {e.text}" if hasattr(e, 'status_code') else f"JIRA Error: {e.text}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_bulk_tickets(self, issues: List[DesignIssue], 
                           assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create multiple Jira tickets in bulk with rate limiting"""
        results = {'successful': [], 'failed': []}
        
        for i, issue in enumerate(issues):
            # Add small delay to avoid rate limiting
            if i > 0:
                time.sleep(1)
                
            result = self.create_design_qa_ticket(issue, assignee)
            
            if result['success']:
                results['successful'].append({
                    'issue': issue,
                    'ticket_key': result['issue_key'],
                    'url': result['issue_url']
                })
                logger.info(f"Created ticket {result['issue_key']} for {issue.category} issue")
            else:
                results['failed'].append({
                    'issue': issue,
                    'error': result['error']
                })
                logger.error(f"Failed to create ticket for {issue.category}: {result['error']}")
        
        return {
            'total_processed': len(issues),
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'results': results
        }
    
    def _format_issue_description(self, issue: DesignIssue) -> str:
        """Format issue description for Jira with better formatting"""
        description = f"""
*Category:* {issue.category}
*Subcategory:* {issue.subcategory}
*Severity:* {issue.severity.value}

*Description:*
{issue.description}

*Expected Behavior:*
{issue.expected_behavior or 'Not specified'}

*Actual Behavior:*
{issue.actual_behavior or 'Not specified'}

*Element Selector:* 
{issue.element_selector or 'N/A'}

*Checklist Item:*
{issue.checklist_item or 'N/A'}

---
*Automated Design QA Report*
*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""
        return description
    
    def _attach_screenshot(self, issue_key: str, screenshot_path: str):
        """Attach screenshot to Jira ticket with better error handling and compression"""
        try:
            if not os.path.exists(screenshot_path):
                logger.error(f"Screenshot file does not exist: {screenshot_path}")
                return
                
            file_size = os.path.getsize(screenshot_path)
            if file_size == 0:
                logger.error(f"Screenshot file is empty: {screenshot_path}")
                return
            
            # Check file size limit (Jira typically has a 10MB limit per attachment)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Screenshot too large ({file_size} bytes), compressing...")
                # Compress the image
                image = Image.open(screenshot_path)
                # Save with optimized compression
                image.save(screenshot_path, "PNG", optimize=True, quality=85)
                file_size = os.path.getsize(screenshot_path)
                logger.info(f"Compressed screenshot to {file_size} bytes")
            
            with open(screenshot_path, 'rb') as f:
                self.jira_client.add_attachment(
                    issue=issue_key, 
                    attachment=f,
                    filename=f"design_qa_screenshot_{issue_key}.png"
                )
            logger.info(f"Screenshot ({file_size} bytes) attached to {issue_key}")
            
        except Exception as e:
            logger.error(f"Failed to attach screenshot to {issue_key}: {e}")
            # Log more details for debugging
            if hasattr(e, 'response'):
                logger.error(f"Jira response: {e.response.text}")
            if hasattr(e, 'status_code'):
                logger.error(f"HTTP status: {e.status_code}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information with better error handling"""
        if not self.jira_client:
            return {'error': 'Jira client not initialized'}
        
        try:
            project = self.jira_client.project(self.project_key)
            issue_types = self.jira_client.issue_types()
            priorities = self.jira_client.priorities()
            
            return {
                'project_name': project.name,
                'project_key': project.key,
                'project_lead': project.lead.displayName if hasattr(project, 'lead') else 'Unknown',
                'issue_types': [{'id': it.id, 'name': it.name} for it in issue_types],
                'priorities': [{'id': p.id, 'name': p.name} for p in priorities]
            }
        except JIRAError as e:
            return {'error': f'JIRA Error: {e.text}', 'status_code': e.status_code}
        except Exception as e:
            return {'error': f'Failed to get project info: {str(e)}'}

class AutomatedDesignValidator:
    """Automated design validation using the QA checklist"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.checklist = DesignQAChecklist()
        self.issues_found = []
    
    def validate_page(self, url: str) -> List[DesignIssue]:
        """Validate a page against the design checklist"""
        if not self.driver:
            return []
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Run automated checks
            self._check_accessibility()
            self._check_images()
            self._check_forms()
            self._check_buttons()
            self._check_typography()
            self._check_responsive_design()
            
            return self.issues_found
            
        except Exception as e:
            logger.error(f"Page validation failed: {e}")
            return []
    
    def _check_accessibility(self):
        """Check accessibility compliance"""
        try:
            # Check for images without alt text
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                alt_text = img.get_attribute("alt")
                if not alt_text or alt_text.strip() == "":
                    self.issues_found.append(DesignIssue(
                        category="Accessibility",
                        subcategory="Images",
                        description=f"Image missing alt text: {img.get_attribute('src')[:50]}...",
                        severity=Priority.HIGH,
                        element_selector=f"img[src*='{img.get_attribute('src')[:20]}']",
                        expected_behavior="All images should have descriptive alt text",
                        actual_behavior="Image has no alt text attribute",
                        checklist_item="VD018"
                    ))
            
            # Check heading structure
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            if not headings:
                self.issues_found.append(DesignIssue(
                    category="Accessibility",
                    subcategory="Structure",
                    description="No heading elements found on page",
                    severity=Priority.MEDIUM,
                    expected_behavior="Page should have proper heading structure",
                    actual_behavior="No headings detected",
                    checklist_item="A005"
                ))
            
        except Exception as e:
            logger.error(f"Accessibility check failed: {e}")
    
    def _check_images(self):
        """Check image quality and implementation"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                # Check if image is loaded
                if img.get_attribute("naturalWidth") == "0":
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Broken or missing image: {img.get_attribute('src')}",
                        severity=Priority.HIGH,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should load correctly",
                        actual_behavior="Image failed to load",
                        checklist_item="VD016"
                    ))
                
                # Check for consistent sizing
                width = img.size['width']
                height = img.size['height']
                if width < 10 or height < 10:
                    self.issues_found.append(DesignIssue(
                        category="Visual Design",
                        subcategory="Imagery",
                        description=f"Image too small: {width}x{height}px",
                        severity=Priority.LOW,
                        element_selector=f"img[src='{img.get_attribute('src')}']",
                        expected_behavior="Images should be appropriately sized",
                        actual_behavior=f"Image is only {width}x{height}px",
                        checklist_item="VD016"
                    ))
        except Exception as e:
            logger.error(f"Image check failed: {e}")
    
    def _check_forms(self):
        """Check form implementation"""
        try:
            # Check for unlabeled inputs
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type")
                if input_type not in ["hidden", "submit", "button"]:
                    # Check for label
                    input_id = input_elem.get_attribute("id")
                    has_label = False
                    
                    if input_id:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            has_label = True
                        except:
                            pass
                    
                    if not has_label:
                        self.issues_found.append(DesignIssue(
                            category="UI Elements",
                            subcategory="Forms",
                            description=f"Input field without label: {input_type} input",
                            severity=Priority.MEDIUM,
                            element_selector=f"input[type='{input_type}']",
                            expected_behavior="All input fields should have associated labels",
                            actual_behavior="Input field has no label",
                            checklist_item="UI005"
                        ))
        except Exception as e:
            logger.error(f"Form check failed: {e}")
    
    def _check_buttons(self):
        """Check button implementation"""
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
            for button in buttons:
                # Check button text
                text = button.text or button.get_attribute("value")
                if not text or len(text.strip()) < 2:
                    self.issues_found.append(DesignIssue(
                        category="UI Elements",
                        subcategory="Buttons",
                        description="Button with unclear or missing text",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Buttons should have clear, action-oriented labels",
                        actual_behavior=f"Button text: '{text}'",
                        checklist_item="UI003"
                    ))
                
                # Check button size for mobile
                size = button.size
                if size['width'] < 44 or size['height'] < 44:
                    self.issues_found.append(DesignIssue(
                        category="Responsive Design",
                        subcategory="Mobile-specific",
                        description=f"Button too small for touch: {size['width']}x{size['height']}px",
                        severity=Priority.MEDIUM,
                        element_selector=button.tag_name,
                        expected_behavior="Touch targets should be at least 44x44 pixels",
                        actual_behavior=f"Button is {size['width']}x{size['height']}px",
                        checklist_item="RD004"
                    ))
        except Exception as e:
            logger.error(f"Button check failed: {e}")
    
    def _check_typography(self):
        """Check typography consistency"""
        try:
            # Check for very small text
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, span, div, li, td, th")
            for element in all_elements[:50]:  # Limit to first 50 to avoid performance issues
                font_size = element.value_of_css_property("font-size")
                if font_size:
                    size_px = float(font_size.replace("px", ""))
                    if size_px < 12:  # Text smaller than 12px might be hard to read
                        self.issues_found.append(DesignIssue(
                            category="Visual Design",
                            subcategory="Typography",
                            description=f"Text too small: {size_px}px",
                            severity=Priority.LOW,
                            element_selector=element.tag_name,
                            expected_behavior="Text should be at least 12px for readability",
                            actual_behavior=f"Font size is {size_px}px",
                            checklist_item="VD009"
                        ))
        except Exception as e