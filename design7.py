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
    """Comprehensive design QA checklist based on the PDF document"""
    
    def __init__(self):
        self.checklist_items = self._initialize_checklist()
    
    def _initialize_checklist(self) -> List[QAChecklistItem]:
        """Initialize the comprehensive QA checklist from the PDF"""
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
        """Initialize Jira client with error handling"""
        try:
            if all([self.server_url, self.email, self.api_token]):
                self.jira_client = JIRA(
                    server=self.server_url,
                    basic_auth=(self.email, self.api_token)
                )
                logger.info("Jira client initialized successfully")
            else:
                logger.error("Missing Jira configuration")
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            self.jira_client = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and permissions"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized'}
        
        try:
            # Test basic connection
            user = self.jira_client.myself()
            
            # Test project access
            project = self.jira_client.project(self.project_key)
            
            # Get available issue types
            issue_types = self.jira_client.issue_types()
            
            # Get available priorities
            priorities = self.jira_client.priorities()
            
            return {
                'success': True,
                'user': user['displayName'],
                'project': project.name,
                'issue_types': [it.name for it in issue_types],
                'priorities': [p.name for p in priorities]
            }
        except JIRAError as e:
            return {'success': False, 'error': f'Jira API Error: {e.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Connection failed: {str(e)}'}
    
    def create_design_qa_ticket(self, issue: DesignIssue, 
                               assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a Jira ticket for a design QA issue"""
        if not self.jira_client:
            return {'success': False, 'error': 'Jira client not initialized'}
        
        try:
            # Prepare issue data
            summary = f"[Design QA] {issue.category} - {issue.subcategory}: {issue.description[:60]}..."
            
            description = self._format_issue_description(issue)
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': IssueType.BUG.value},
                'priority': {'name': issue.severity.value},
                'labels': ['design-qa', 'automated-testing', issue.category.lower().replace(' ', '-')]
            }
            
            # Add assignee if provided
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            
            # Add custom fields if configured
            custom_fields = self._get_custom_fields()
            if custom_fields:
                issue_dict.update(custom_fields)
            
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
            return {'success': False, 'error': f'Failed to create ticket: {e.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def create_bulk_tickets(self, issues: List[DesignIssue], 
                           assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create multiple Jira tickets in bulk"""
        results = {'successful': [], 'failed': []}
        
        for issue in issues:
            result = self.create_design_qa_ticket(issue, assignee)
            
            if result['success']:
                results['successful'].append({
                    'issue': issue,
                    'ticket_key': result['issue_key'],
                    'url': result['issue_url']
                })
            else:
                results['failed'].append({
                    'issue': issue,
                    'error': result['error']
                })
        
        return {
            'total_processed': len(issues),
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'results': results
        }
    
    def _format_issue_description(self, issue: DesignIssue) -> str:
        """Format issue description for Jira"""
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
_This ticket was automatically created by the Design QA Automation System_
_Created on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_
"""
        return description
    
    def _attach_screenshot(self, issue_key: str, screenshot_path: str):
        """Attach screenshot to Jira ticket"""
        try:
            with open(screenshot_path, 'rb') as f:
                self.jira_client.add_attachment(
                    issue=issue_key, 
                    attachment=f,
                    filename=f"screenshot_{issue_key}.png"
                )
            logger.info(f"Screenshot attached to {issue_key}")
        except Exception as e:
            logger.error(f"Failed to attach screenshot to {issue_key}: {e}")
    
    def _get_custom_fields(self) -> Dict[str, Any]:
        """Get custom field mappings if configured"""
        # This can be extended to support custom fields
        custom_fields = {}
        
        # Example custom field mapping
        if os.getenv("JIRA_CUSTOM_FIELD_BROWSER"):
            custom_fields[os.getenv("JIRA_CUSTOM_FIELD_BROWSER")] = "Chrome"
        
        if os.getenv("JIRA_CUSTOM_FIELD_ENVIRONMENT"):
            custom_fields[os.getenv("JIRA_CUSTOM_FIELD_ENVIRONMENT")] = "Testing"
        
        return custom_fields
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information"""
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
        except Exception as e:
            return {'error': f'Failed to get project info: {str(e)}'}

class AutomatedDesignValidator:
    """Automated design validation using the QA checklist"""
    
    def __init__(self, driver: 'EnhancedChromeDriver'):
        self.driver = driver
        self.checklist = DesignQAChecklist()
        self.issues_found = []
    
    def validate_page(self, url: str) -> List[DesignIssue]:
        """Validate a page against the design checklist"""
        if not self.driver.driver:
            return []
        
        try:
            self.driver.driver.get(url)
            WebDriverWait(self.driver.driver, 10).until(
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
            images = self.driver.driver.find_elements(By.TAG_NAME, "img")
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
            headings = self.driver.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
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
            images = self.driver.driver.find_elements(By.TAG_NAME, "img")
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
            inputs = self.driver.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type")
                if input_type not in ["hidden", "submit", "button"]:
                    # Check for label
                    input_id = input_elem.get_attribute("id")
                    has_label = False
                    
                    if input_id:
                        try:
                            self.driver.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
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
            buttons = self.driver.driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
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
            all_elements = self.driver.driver.find_elements(By.CSS_SELECTOR, "p, span, div, li, td, th")
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
        except Exception as e:
            logger.error(f"Typography check failed: {e}")
    
    def _check_responsive_design(self):
        """Check responsive design elements"""
        try:
            # Check viewport meta tag
            try:
                self.driver.driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
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
            page_width = self.driver.driver.execute_script("return document.body.scrollWidth")
            window_width = self.driver.driver.execute_script("return window.innerWidth")
            
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
            
            # Convert to PIL Image
            image = Image.open(BytesIO(screenshot))
            
            # If page is longer than viewport, capture remaining parts
            if total_height > viewport_height:
                # Create a new image for the full page
                full_image = Image.new('RGB', (image.width, total_height), (255, 255, 255))
                full_image.paste(image, (0, 0))
                
                # Capture remaining parts
                current_position = viewport_height
                while current_position < total_height:
                    # Scroll to next position
                    self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                    time.sleep(0.5)
                    
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
    
    def capture_element_screenshot(self, url, selector, wait_time=2):
        """Capture screenshot of specific element"""
        if not self.driver:
            return None
            
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for element
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            time.sleep(wait_time)
            
            # Find element
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            # Capture element screenshot
            screenshot = element.screenshot_as_png
            image = Image.open(BytesIO(screenshot))
            
            return image
            
        except Exception as e:
            logger.error(f"Element screenshot failed: {e}")
            return None
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

class FigmaDesignComparator:
    """Compare web implementation with Figma design"""
    
    def __init__(self):
        self.access_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.headers = {"X-Figma-Token": self.access_token}
    
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
                # Direct file ID
                file_id = figma_url
            else:
                return None
            
            # Validate file ID format
            if not re.match(r'^[a-zA-Z0-9]{15,25}$', file_id):
                return None
                
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to extract file ID: {e}")
            return None
    
    def get_file_info(self, file_id):
        """Get Figma file information"""
        try:
            url = f"https://api.figma.com/v1/files/{file_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Figma API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def get_image_urls(self, file_id, node_ids=None, scale=2, format="png"):
        """Get image URLs for specific nodes"""
        try:
            if node_ids:
                # Get specific nodes
                node_params = "&ids=" + ",".join(node_ids)
            else:
                # Get entire file
                node_params = ""
            
            url = f"https://api.figma.com/v1/images/{file_id}?scale={scale}&format={format}{node_params}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Figma image API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get image URLs: {e}")
            return None
    
    def download_image(self, image_url):
        """Download image from URL"""
        try:
            response = requests.get(image_url)
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
                web_image = web_image.resize(figma_image.size, Image.Resampling.LANCZOS)
            
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
            
            # Create heatmap
            diff_heatmap = self._create_heatmap(figma_array, web_array)
            
            return {
                'similarity_score': similarity,
                'is_match': similarity >= threshold,
                'difference_image': diff_image,
                'heatmap_image': diff_heatmap,
                'figma_image': figma_image,
                'web_image': web_image
            }
            
        except Exception as e:
            logger.error(f"Design comparison failed: {e}")
            return None
    
    def _create_heatmap(self, img1, img2):
        """Create heatmap showing differences"""
        try:
            # Convert to grayscale for difference calculation
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
            
            # Compute absolute difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Apply colormap for heatmap
            heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
            
            return Image.fromarray(cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logger.error(f"Heatmap creation failed: {e}")
            return None

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
        """Process complete QA request"""
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
            
            # Step 2: Get Figma file info and images
            file_info = self.figma_comparator.get_file_info(file_id)
            if not file_info:
                results['error'] = "Failed to get Figma file information"
                return results
            
            # Step 3: Capture web screenshots
            web_screenshot = self.chrome_driver.capture_full_page_screenshot(web_url)
            if not web_screenshot:
                results['error'] = "Failed to capture web screenshot"
                return results
            
            # Step 4: Get Figma images (simplified - in real implementation, 
            # you'd get specific frames/components)
            image_data = self.figma_comparator.get_image_urls(file_id)
            if not image_data or 'images' not in image_data:
                results['error'] = "Failed to get Figma images"
                return results
            
            # Step 5: Compare designs (simplified example)
            # In real implementation, you'd iterate through specific components
            figma_image_url = list(image_data['images'].values())[0]
            figma_image = self.figma_comparator.download_image(figma_image_url)
            
            if figma_image:
                comparison = self.figma_comparator.compare_designs(figma_image, web_screenshot)
                if comparison:
                    results['comparison_results'].append(comparison)
            
            # Step 6: Run automated validation
            self.validator = AutomatedDesignValidator(self.chrome_driver)
            validation_issues = self.validator.validate_page(web_url)
            results['validation_issues'] = validation_issues
            
            # Step 7: Create Jira tickets for issues
            if validation_issues and self.jira_integration.jira_client:
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

# Streamlit UI Application
class DesignQAApp:
    """Streamlit application for Design QA Automation"""
    
    def __init__(self):
        self.processor = DesignQAProcessor()
        self.setup_page_config()
    
    def setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="Design QA Automation",
            page_icon="🎨",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_sidebar(self):
        """Render sidebar with configuration and controls"""
        with st.sidebar:
            st.title("⚙️ Configuration")
            
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
                        
                        # Display results
                        for service, status in config_status.items():
                            col1, col2 = st.columns([1, 3])
                            col1.write(f"**{service.title()}**")
                            if status['status']:
                                col2.success("✓ Configured")
                            else:
                                col2.error(f"✗ {status['message']}")
                        
                        st.divider()
                        
                        for service, status in connection_status.items():
                            col1, col2 = st.columns([1, 3])
                            col1.write(f"**{service.title()}**")
                            if status['status']:
                                col2.success(f"✓ {status['message']}")
                            else:
                                col2.error(f"✗ {status['message']}")
            
            # Jira Settings
            with st.expander("Jira Settings", expanded=False):
                jira_assignee = st.text_input("Default Assignee",
                                            help="Jira username for ticket assignment")
                
                if st.button("Test Jira Connection"):
                    jira_info = self.processor.jira_integration.get_project_info()
                    if 'error' not in jira_info:
                        st.success(f"Connected to {jira_info['project_name']} ({jira_info['project_key']})")
                        st.write(f"Lead: {jira_info['project_lead']}")
                    else:
                        st.error(jira_info['error'])
    
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
        """Render main content area"""
        st.title("🎨 Design QA Automation")
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
                    st.image(screenshot, caption="Web Page Screenshot", width='stretch')
                    
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
                validator = AutomatedDesignValidator(self.processor.chrome_driver)
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
                        st.image(comp['figma_image'], caption="Figma Design", width='stretch')
                    
                    with col2:
                        st.image(comp['web_image'], caption="Web Implementation", width='stretch')
                    
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
                        st.image(comp['difference_image'], caption="Difference Map", width='stretch')
        
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
    
    def run(self):
        """Run the Streamlit application"""
        try:
            self.render_sidebar()
            self.render_main_content()
        finally:
            self.processor.cleanup()

# Main execution
if __name__ == "__main__":
    app = DesignQAApp()
    app.run()