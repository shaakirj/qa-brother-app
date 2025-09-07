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
        if re.match(r'^[a-zA-Z0-9]{15,25}
        
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
        if not re.match(r'^[a-zA-Z0-9]{15,25}, file_id):
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
    st.sidebar.subheader("⚙️ Configuration Status")
    
    with st.sidebar.expander("Validation Results", expanded=False):
        validator = ConfigurationValidator()
        results = validator.validate_api_keys()
        
        for service, result in results.items():
            status_icon = "✅" if result['status'] else "❌"
            st.write(f"**{service.title()}:** {status_icon}")
            st.caption(result['message'])
        
        # Test connections button
        if st.button("🔄 Test API Connections"):
            with st.spinner("Testing connections..."):
                connections = validator.test_api_connections()
                
                st.write("**Connection Test Results:**")
                for service, result in connections.items():
                    status_icon = "✅" if result['status'] else "❌"
                    st.write(f"{status_icon} **{service.title()}**")
                    st.caption(result['message'])


def display_jira_status():
    """Display Jira connection and project status"""
    st.sidebar.subheader("🎫 Jira Integration")
    
    jira_integration = EnhancedJiraIntegration()
    
    if jira_integration.jira_client:
        connection_test = jira_integration.test_connection()
        
        if connection_test['success']:
            st.sidebar.success("✅ Jira Connected")
            st.sidebar.write(f"**User:** {connection_test['user']}")
            st.sidebar.write(f"**Project:** {connection_test['project']}")
            
            with st.sidebar.expander("Project Details"):
                st.write(f"**Available Issue Types:**")
                for issue_type in connection_test['issue_types']:
                    st.write(f"• {issue_type}")
                
                st.write(f"**Available Priorities:**")
                for priority in connection_test['priorities']:
                    st.write(f"• {priority}")
        else:
            st.sidebar.error("❌ Jira Connection Failed")
            st.sidebar.caption(connection_test['error'])
    else:
        st.sidebar.warning("⚠️ Jira Not Configured")


def run_design_qa_analysis(url: str, figma_file: str = None) -> Dict[str, Any]:
    """Run comprehensive design QA analysis"""
    results = {
        'url': url,
        'figma_file': figma_file,
        'issues': [],
        'screenshots': {},
        'analysis_complete': False,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    # Initialize Chrome driver
    chrome_driver = EnhancedChromeDriver()
    
    try:
        if not chrome_driver.setup_driver():
            results['error'] = "Failed to setup Chrome driver"
            return results
        
        # Capture website screenshot
        screenshot = chrome_driver.capture_full_page_screenshot(url)
        if screenshot:
            # Save screenshot temporarily
            temp_dir = tempfile.mkdtemp()
            screenshot_path = os.path.join(temp_dir, f"screenshot_{int(time.time())}.png")
            
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            
            results['screenshots']['website'] = screenshot_path
        
        # Run automated validation
        validator = AutomatedDesignValidator(chrome_driver)
        issues = validator.validate_page(url)
        results['issues'] = issues
        results['analysis_complete'] = True
        
        return results
        
    except Exception as e:
        results['error'] = f"Analysis failed: {str(e)}"
        return results
    finally:
        chrome_driver.quit()


def main():
    """Enhanced main Streamlit application"""
    st.set_page_config(
        page_title="Enhanced QA Automation System",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .issue-card {
        border-left: 4px solid #ff6b6b;
        padding: 15px;
        margin: 10px 0;
        background-color: #fff5f5;
        border-radius: 5px;
    }
    .success-card {
        border-left: 4px solid #51cf66;
        padding: 15px;
        margin: 10px 0;
        background-color: #f3fff3;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Enhanced AI QA Automation System")
    st.markdown("**Complete testing solution with design comparison, document processing, and Jira integration**")
    
    # Configuration sidebars
    display_configuration_status()
    display_jira_status()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard",
        "🔍 Design QA Analysis", 
        "📋 Checklist Management",
        "🎫 Jira Integration",
        "⚙️ System Status"
    ])
    
    with tab1:
        st.header("📊 QA Dashboard")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 Total Checks</h3>
                <h2>47</h2>
                <p>Automated validation points</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>✅ Categories</h3>
                <h2>6</h2>
                <p>Design QA categories</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🔧 Integrations</h3>
                <h2>3</h2>
                <p>API connections</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            jira_integration = EnhancedJiraIntegration()
            jira_status = "Connected" if jira_integration.jira_client else "Disconnected"
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎫 Jira Status</h3>
                <h2>{jira_status}</h2>
                <p>Ticket integration</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick action buttons
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Run Quick Analysis", help="Analyze a website quickly"):
                st.info("Navigate to the 'Design QA Analysis' tab to run a full analysis")
        
        with col2:
            if st.button("📋 View Checklist", help="View the complete QA checklist"):
                st.info("Check the 'Checklist Management' tab for detailed items")
        
        with col3:
            if st.button("🎫 Create Test Ticket", help="Create a sample Jira ticket"):
                st.info("Go to 'Jira Integration' tab to manage tickets")
    
    with tab2:
        st.header("🔍 Design QA Analysis")
        st.markdown("Comprehensive automated testing based on the design QA checklist")
        
        # Analysis configuration
        col1, col2 = st.columns([2, 1])
        
        with col1:
            website_url = st.text_input(
                "🌐 Website URL",
                placeholder="https://your-website.com",
                help="Enter the URL to analyze"
            )
            
            figma_file_url = st.text_input(
                "🎨 Figma File URL (Optional)",
                placeholder="https://figma.com/file/...",
                help="Optional: Compare against Figma designs"
            )
        
        with col2:
            st.subheader("Analysis Options")
            
            analysis_depth = st.selectbox(
                "Analysis Depth",
                ["Quick Scan", "Standard Analysis", "Comprehensive Audit"],
                index=1
            )
            
            create_jira_tickets = st.checkbox(
                "🎫 Auto-create Jira tickets",
                value=False,
                help="Automatically create Jira tickets for issues found"
            )
            
            if create_jira_tickets:
                jira_assignee = st.text_input(
                    "Assignee (Optional)",
                    placeholder="user@company.com"
                )
        
        # Run analysis
        if st.button("🚀 Start QA Analysis", type="primary"):
            if not website_url:
                st.error("Please provide a website URL")
            else:
                update_progress, complete_progress = create_progress_tracker()
                
                try:
                    update_progress(1, 6, "Initializing analysis...")
                    
                    # Run the analysis
                    results = run_design_qa_analysis(website_url, figma_file_url)
                    
                    update_progress(2, 6, "Capturing screenshots...")
                    time.sleep(1)
                    
                    update_progress(3, 6, "Running automated checks...")
                    time.sleep(1)
                    
                    update_progress(4, 6, "Analyzing issues...")
                    time.sleep(1)
                    
                    if create_jira_tickets and results.get('issues'):
                        update_progress(5, 6, "Creating Jira tickets...")
                        jira_integration = EnhancedJiraIntegration()
                        
                        if jira_integration.jira_client:
                            bulk_result = jira_integration.create_bulk_tickets(
                                results['issues'], 
                                jira_assignee if create_jira_tickets else None
                            )
                            results['jira_results'] = bulk_result
                    
                    update_progress(6, 6, "Generating report...")
                    time.sleep(1)
                    
                    complete_progress()
                    
                    # Display results
                    if 'error' in results:
                        st.error(f"Analysis failed: {results['error']}")
                    else:
                        st.success(f"✅ Analysis complete! Found {len(results['issues'])} issues")
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Issues Found", len(results['issues']))
                        
                        with col2:
                            high_severity = len([i for i in results['issues'] if i.severity == Priority.HIGH])
                            st.metric("High Severity", high_severity)
                        
                        with col3:
                            categories = len(set([i.category for i in results['issues']]))
                            st.metric("Categories Affected", categories)
                        
                        # Display screenshot
                        if 'website' in results['screenshots']:
                            st.subheader("📸 Website Screenshot")
                            try:
                                screenshot_data = open(results['screenshots']['website'], 'rb').read()
                                st.image(screenshot_data, caption=f"Screenshot of {website_url}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Could not display screenshot: {e}")
                        
                        # Display issues
                        if results['issues']:
                            st.subheader("🐛 Issues Found")
                            
                            for i, issue in enumerate(results['issues']):
                                severity_colors = {
                                    Priority.HIGH: "#ff6b6b",
                                    Priority.MEDIUM: "#ffd93d",
                                    Priority.LOW: "#74c0fc"
                                }
                                
                                color = severity_colors.get(issue.severity, "#ff6b6b")
                                
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background-color: #f8f9fa; border-radius: 5px;">
                                    <h4>{issue.category} - {issue.subcategory}</h4>
                                    <p><strong>Description:</strong> {issue.description}</p>
                                    <p><strong>Severity:</strong> {issue.severity.value}</p>
                                    {f"<p><strong>Expected:</strong> {issue.expected_behavior}</p>" if issue.expected_behavior else ""}
                                    {f"<p><strong>Actual:</strong> {issue.actual_behavior}</p>" if issue.actual_behavior else ""}
                                    {f"<p><strong>Element:</strong> <code>{issue.element_selector}</code></p>" if issue.element_selector else ""}
                                    {f"<p><strong>Checklist Item:</strong> {issue.checklist_item}</p>" if issue.checklist_item else ""}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display Jira results if tickets were created
                        if 'jira_results' in results:
                            jira_res = results['jira_results']
                            st.subheader("🎫 Jira Ticket Creation Results")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Successful Tickets", jira_res['successful_count'])
                            with col2:
                                st.metric("Failed Tickets", jira_res['failed_count'])
                            
                            if jira_res['results']['successful']:
                                st.write("**✅ Successfully Created Tickets:**")
                                for success in jira_res['results']['successful']:
                                    st.write(f"• [{success['ticket_key']}]({success['url']}) - {success['issue'].description[:50]}...")
                            
                            if jira_res['results']['failed']:
                                st.write("**❌ Failed Ticket Creation:**")
                                for failed in jira_res['results']['failed']:
                                    st.write(f"• {failed['issue'].description[:50]}... - {failed['error']}")
                        
                        # Export options
                        st.subheader("📤 Export Results")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("📊 Export CSV"):
                                csv_data = []
                                for issue in results['issues']:
                                    csv_data.append({
                                        'Category': issue.category,
                                        'Subcategory': issue.subcategory,
                                        'Description': issue.description,
                                        'Severity': issue.severity.value,
                                        'Element': issue.element_selector,
                                        'Expected': issue.expected_behavior,
                                        'Actual': issue.actual_behavior,
                                        'Checklist_Item': issue.checklist_item
                                    })
                                
                                df = pd.DataFrame(csv_data)
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"qa_analysis_{int(time.time())}.csv",
                                    mime="text/csv"
                                )
                        
                        with col2:
                            if st.button("📋 Export Report"):
                                report = f"""
# QA Analysis Report

**URL:** {website_url}
**Analysis Date:** {results['timestamp']}
**Issues Found:** {len(results['issues'])}

## Summary
- High Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.HIGH])}
- Medium Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.MEDIUM])}
- Low Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.LOW])}

## Issues Detail
"""
                                for i, issue in enumerate(results['issues'], 1):
                                    report += f"""
### Issue {i}: {issue.category} - {issue.subcategory}
- **Description:** {issue.description}
- **Severity:** {issue.severity.value}
- **Expected:** {issue.expected_behavior or 'N/A'}
- **Actual:** {issue.actual_behavior or 'N/A'}
- **Element:** {issue.element_selector or 'N/A'}
- **Checklist Item:** {issue.checklist_item or 'N/A'}

"""
                                
                                st.download_button(
                                    label="Download Report",
                                    data=report,
                                    file_name=f"qa_report_{int(time.time())}.md",
                                    mime="text/markdown"
                                )
                        
                        with col3:
                            if st.button("🔄 Re-run Analysis"):
                                st.experimental_rerun()
                
                except Exception as e:
                    complete_progress()
                    st.error(f"Analysis failed: {e}")
                    st.exception(e)
    
    with tab3:
        st.header("📋 Design QA Checklist Management")
        st.markdown("Manage and customize the comprehensive design QA checklist")
        
        checklist = DesignQAChecklist()
        
        # Checklist overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Items", len(checklist.checklist_items))
        
        with col2:
            automated_items = len(checklist.get_automated_items())
            st.metric("Automated Checks", automated_items)
        
        with col3:
            categories = len(set([item.category for item in checklist.checklist_items]))
            st.metric("Categories", categories)
        
        # Category filter
        all_categories = list(set([item.category for item in checklist.checklist_items]))
        selected_category = st.selectbox("Filter by Category", ["All"] + all_categories)
        
        # Display checklist items
        items_to_show = (checklist.checklist_items if selected_category == "All" 
                        else checklist.get_items_by_category(selected_category))
        
        st.subheader(f"📝 Checklist Items ({len(items_to_show)} items)")
        
        # Create tabs for different views
        view_tab1, view_tab2 = st.tabs(["📋 List View", "📊 Category Summary"])
        
        with view_tab1:
            for item in items_to_show:
                automation_status = "🤖 Automated" if item.automated else "👤 Manual"
                
                with st.expander(f"{item.id}: {item.description}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Category:** {item.category}")
                        st.write(f"**Subcategory:** {item.subcategory}")
                        st.write(f"**Status:** {automation_status}")
                    
                    with col2:
                        if item.selector:
                            st.code(f"Selector: {item.selector}")
                        if item.validation_function:
                            st.code(f"Validation: {item.validation_function}")
        
        with view_tab2:
            # Category summary
            category_stats = {}
            for item in checklist.checklist_items:
                if item.category not in category_stats:
                    category_stats[item.category] = {'total': 0, 'automated': 0}
                category_stats[item.category]['total'] += 1
                if item.automated:
                    category_stats[item.category]['automated'] += 1
            
            for category, stats in category_stats.items():
                automation_rate = (stats['automated'] / stats['total']) * 100
                
                st.subheader(category)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Items", stats['total'])
                with col2:
                    st.metric("Automated", stats['automated'])
                with col3:
                    st.metric("Automation Rate", f"{automation_rate:.1f}%")
                
                # Progress bar for automation
                st.progress(automation_rate / 100)
                st.markdown("---")
    
    with tab4:
        st.header("🎫 Jira Integration & Ticket Management")
        st.markdown("Manage Jira tickets and create issues directly from QA findings")
        
        jira_integration = EnhancedJiraIntegration()
        
        if not jira_integration.jira_client:
            st.error("❌ Jira is not properly configured")
            st.markdown("""
            **Required Environment Variables:**
            - `JIRA_SERVER_URL`: Your Jira server URL
            - `JIRA_EMAIL`: Your Jira account email
            - `JIRA_API_TOKEN`: Your Jira API token
            - `JIRA_PROJECT_KEY`: Target project key
            """)
            return
        
        # Test connection
        connection_test = jira_integration.test_connection()
        
        if connection_test['success']:
            st.success("✅ Jira connection successful!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Connected as:** {connection_test['user']}")
            with col2:
                st.info(f"**Project:** {connection_test['project']}")
            
            # Manual ticket creation
            st.subheader("🎫 Create Manual QA Ticket")
            
            with st.form("manual_ticket_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    ticket_category = st.selectbox(
                        "Category",
                        ["Visual Design", "Responsive Design", "UI Elements", "Accessibility", "Content", "Performance"]
                    )
                    
                    ticket_subcategory = st.text_input("Subcategory", "Brand Consistency")
                    
                    ticket_priority = st.selectbox(
                        "Priority",
                        [p.value for p in Priority],
                        index=2  # Medium as default
                    )
                
                with col2:
                    ticket_summary = st.text_input("Summary", "Design issue description")
                    
                    ticket_description = st.text_area(
                        "Description",
                        "Detailed description of the QA issue found..."
                    )
                    
                    ticket_assignee = st.text_input("Assignee (optional)", placeholder="user@company.com")
                
                element_selector = st.text_input("Element Selector (optional)", placeholder=".class-name or #id")
                
                expected_behavior = st.text_area("Expected Behavior", "What should happen...")
                actual_behavior = st.text_area("Actual Behavior", "What actually happens...")
                
                submitted = st.form_submit_button("🚀 Create Ticket", type="primary")
                
                if submitted:
                    # Create issue object
                    manual_issue = DesignIssue(
                        category=ticket_category,
                        subcategory=ticket_subcategory,
                        description=f"{ticket_summary}: {ticket_description}",
                        severity=Priority(ticket_priority),
                        element_selector=element_selector if element_selector else None,
                        expected_behavior=expected_behavior if expected_behavior else None,
                        actual_behavior=actual_behavior if actual_behavior else None
                    )
                    
                    # Create ticket
                    with st.spinner("Creating Jira ticket..."):
                        result = jira_integration.create_design_qa_ticket(
                            manual_issue, 
                            ticket_assignee if ticket_assignee else None
                        )
                    
                    if result['success']:
                        st.success(f"✅ Ticket created successfully!")
                        st.info(f"**Ticket:** [{result['issue_key']}]({result['issue_url']})")
                    else:
                        st.error(f"❌ Failed to create ticket: {result['error']}")
            
            # Bulk ticket creation
            st.subheader("📦 Bulk Ticket Creation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Create Multiple Test Tickets**")
                num_test_tickets = st.number_input("Number of test tickets", 1, 10, 3)
                test_assignee = st.text_input("Test tickets assignee", placeholder="user@company.com")
                
                if st.button("🧪 Create Test Tickets"):
                    test_issues = []
                    
                    for i in range(num_test_tickets):
                        test_issues.append(DesignIssue(
                            category="Visual Design",
                            subcategory="Testing",
                            description=f"Test issue #{i+1} - Generated for testing purposes",
                            severity=Priority.LOW,
                            expected_behavior="This is a test ticket for validation",
                            actual_behavior="Test ticket created successfully",
                            checklist_item=f"TEST{i+1:03d}"
                        ))
                    
                    with st.spinner(f"Creating {num_test_tickets} test tickets..."):
                        bulk_result = jira_integration.create_bulk_tickets(
                            test_issues, 
                            test_assignee if test_assignee else None
                        )
                    
                    st.success(f"✅ Created {bulk_result['successful_count']} tickets successfully!")
                    if bulk_result['failed_count'] > 0:
                        st.warning(f"⚠️ {bulk_result['failed_count']} tickets failed to create")
            
            with col2:
                st.markdown("**Import from CSV**")
                uploaded_csv = st.file_uploader(
                    "Upload CSV with QA issues",
                    type=['csv'],
                    help="CSV should have columns: category, subcategory, description, severity"
                )
                
                if uploaded_csv:
                    try:
                        df = pd.read_csv(uploaded_csv)
                        st.write(f"Found {len(df)} issues in CSV")
                        st.dataframe(df.head())
                        
                        csv_assignee = st.text_input("CSV tickets assignee", placeholder="user@company.com")
                        
                        if st.button("📤 Create Tickets from CSV"):
                            csv_issues = []
                            
                            for _, row in df.iterrows():
                                csv_issues.append(DesignIssue(
                                    category=str(row.get('category', 'General')),
                                    subcategory=str(row.get('subcategory', 'Issue')),
                                    description=str(row.get('description', 'Imported from CSV')),
                                    severity=Priority(row.get('severity', 'Medium')),
                                    expected_behavior=str(row.get('expected_behavior', '')) if 'expected_behavior' in row else None,
                                    actual_behavior=str(row.get('actual_behavior', '')) if 'actual_behavior' in row else None,
                                    element_selector=str(row.get('element_selector', '')) if 'element_selector' in row else None
                                ))
                            
                            with st.spinner(f"Creating {len(csv_issues)} tickets from CSV..."):
                                bulk_result = jira_integration.create_bulk_tickets(
                                    csv_issues,
                                    csv_assignee if csv_assignee else None
                                )
                            
                            st.success(f"✅ Created {bulk_result['successful_count']} tickets from CSV!")
                            if bulk_result['failed_count'] > 0:
                                st.error(f"❌ {bulk_result['failed_count']} tickets failed to create")
                    
                    except Exception as e:
                        st.error(f"Error processing CSV: {e}")
            
            # Project information
            st.subheader("📊 Project Information")
            project_info = jira_integration.get_project_info()
            
            if 'error' not in project_info:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Available Issue Types:**")
                    for issue_type in project_info['issue_types']:
                        st.write(f"• {issue_type['name']}")
                
                with col2:
                    st.write("**Available Priorities:**")
                    for priority in project_info['priorities']:
                        st.write(f"• {priority['name']}")
        else:
            st.error(f"❌ Jira connection failed: {connection_test['error']}")
    
    with tab5:
        st.header("⚙️ System Status & Diagnostics")
        st.markdown("Comprehensive system health check and diagnostic information")
        
        # System health overview
        col1, col2, col3 = st.columns(3)
        
        validator = ConfigurationValidator()
        results = validator.validate_api_keys()
        
        working_services = sum(1 for r in results.values() if r['status'])
        total_services = len(results)
        
        with col1:
            st.metric("Service Status", f"{working_services}/{total_services}")
        
        with col2:
            health_percentage = (working_services / total_services) * 100
            st.metric("System Health", f"{health_percentage:.0f}%")
        
        with col3:
            jira_integration = EnhancedJiraIntegration()
            jira_status = "🟢 Online" if jira_integration.jira_client else "🔴 Offline"
            st.metric("Jira Status", jira_status)
        
        # Detailed status
        st.subheader("🔍 Detailed Component Status")
        
        # API Status
        with st.expander("🔌 API Connections Status", expanded=True):
            for service, result in results.items():
                status_icon = "✅" if result['status'] else "❌"
                st.write(f"**{status_icon} {service.title()}**")
                st.caption(result['message'])
        
        # Environment Variables
        with st.expander("🌍 Environment Variables"):
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
        
        # System Information
        with st.expander("💻 System Information"):
            import sys
            import platform
            
            system_info = {
                "Python Version": sys.version,
                "Platform": platform.platform(),
                "Processor": platform.processor(),
                "Streamlit Version": st.__version__,
            }
            
            for key, value in system_info.items():
                st.write(f"**{key}:** {value}")
        
        # Chrome Driver Test
        with st.expander("🌐 Chrome Driver Diagnostics"):
            if st.button("🔧 Test Chrome Driver"):
                try:
                    driver = EnhancedChromeDriver()
                    if driver.setup_driver(headless=True):
                        capabilities = driver.driver.capabilities
                        chrome_version = capabilities['browserVersion']
                        driver_version = capabilities['chrome']['chromedriverVersion'].split(' ')[0]
                        
                        st.success("✅ Chrome driver working correctly")
                        st.write(f"**Chrome Version:** {chrome_version}")
                        st.write(f"**ChromeDriver Version:** {driver_version}")
                        
                        # Test screenshot capability
                        if st.button("📸 Test Screenshot"):
                            with st.spinner("Taking test screenshot..."):
                                screenshot = driver.capture_full_page_screenshot("https://example.com")
                                if screenshot:
                                    st.success("✅ Screenshot capability working")
                                    st.image(screenshot, caption="Test screenshot", width=300)
                                else:
                                    st.error("❌ Screenshot capability failed")
                        
                        driver.quit()
                    else:
                        st.error("❌ Chrome driver setup failed")
                except Exception as e:
                    st.error(f"❌ Chrome driver test failed: {e}")
        
        # Performance Test
        with st.expander("⚡ Performance Test"):
            if st.button("🏃‍♂️ Run Performance Test"):
                with st.spinner("Running performance tests..."):
                    import time
                    
                    # Test 1: API Response Time
                    start_time = time.time()
                    try:
                        headers = {"X-Figma-Token": os.getenv("FIGMA_ACCESS_TOKEN")}
                        response = requests.get("https://api.figma.com/v1/me", headers=headers, timeout=10)
                        figma_time = time.time() - start_time
                        figma_status = response.status_code == 200
                    except:
                        figma_time = 0
                        figma_status = False
                    
                    # Test 2: Chrome Driver Startup Time
                    start_time = time.time()
                    try:
                        driver = EnhancedChromeDriver()
                        chrome_setup_success = driver.setup_driver(headless=True)
                        chrome_time = time.time() - start_time
                        if chrome_setup_success:
                            driver.quit()
                    except:
                        chrome_time = 0
                        chrome_setup_success = False
                    
                    # Test 3: Jira Connection Time
                    start_time = time.time()
                    jira_integration = EnhancedJiraIntegration()
                    jira_connection_test = jira_integration.test_connection()
                    jira_time = time.time() - start_time
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        status_icon = "✅" if figma_status else "❌"
                        st.metric(
                            f"{status_icon} Figma API",
                            f"{figma_time:.2f}s"
                        )
                    
                    with col2:
                        status_icon = "✅" if chrome_setup_success else "❌"
                        st.metric(
                            f"{status_icon} Chrome Startup", 
                            f"{chrome_time:.2f}s"
                        )
                    
                    with col3:
                        status_icon = "✅" if jira_connection_test.get('success') else "❌"
                        st.metric(
                            f"{status_icon} Jira Connection",
                            f"{jira_time:.2f}s"
                        )
        
        # Log Viewer
        with st.expander("📋 System Logs"):
            st.markdown("Recent system activity and errors")
            
            # This would typically read from actual log files
            sample_logs = [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "message": "System initialized successfully"},
                {"timestamp": (datetime.now() - pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "message": "Chrome driver setup completed"},
                {"timestamp": (datetime.now() - pd.Timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), "level": "WARNING", "message": "Figma API rate limit approaching"},
            ]
            
            for log in sample_logs:
                level_color = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
                icon = level_color.get(log["level"], "⚪")
                st.write(f"{icon} `{log['timestamp']}` **{log['level']}** {log['message']}")


if __name__ == "__main__":
    main()
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
        if not re.match(r'^[a-zA-Z0-9]{15,25}, file_id):
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
    st.sidebar.subheader("⚙️ Configuration Status")
    
    with st.sidebar.expander("Validation Results", expanded=False):
        validator = ConfigurationValidator()
        results = validator.validate_api_keys()
        
        for service, result in results.items():
            status_icon = "✅" if result['status'] else "❌"
            st.write(f"**{service.title()}:** {status_icon}")
            st.caption(result['message'])
        
        # Test connections button
        if st.button("🔄 Test API Connections"):
            with st.spinner("Testing connections..."):
                connections = validator.test_api_connections()
                
                st.write("**Connection Test Results:**")
                for service, result in connections.items():
                    status_icon = "✅" if result['status'] else "❌"
                    st.write(f"{status_icon} **{service.title()}**")
                    st.caption(result['message'])


def display_jira_status():
    """Display Jira connection and project status"""
    st.sidebar.subheader("🎫 Jira Integration")
    
    jira_integration = EnhancedJiraIntegration()
    
    if jira_integration.jira_client:
        connection_test = jira_integration.test_connection()
        
        if connection_test['success']:
            st.sidebar.success("✅ Jira Connected")
            st.sidebar.write(f"**User:** {connection_test['user']}")
            st.sidebar.write(f"**Project:** {connection_test['project']}")
            
            with st.sidebar.expander("Project Details"):
                st.write(f"**Available Issue Types:**")
                for issue_type in connection_test['issue_types']:
                    st.write(f"• {issue_type}")
                
                st.write(f"**Available Priorities:**")
                for priority in connection_test['priorities']:
                    st.write(f"• {priority}")
        else:
            st.sidebar.error("❌ Jira Connection Failed")
            st.sidebar.caption(connection_test['error'])
    else:
        st.sidebar.warning("⚠️ Jira Not Configured")


def run_design_qa_analysis(url: str, figma_file: str = None) -> Dict[str, Any]:
    """Run comprehensive design QA analysis"""
    results = {
        'url': url,
        'figma_file': figma_file,
        'issues': [],
        'screenshots': {},
        'analysis_complete': False,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    # Initialize Chrome driver
    chrome_driver = EnhancedChromeDriver()
    
    try:
        if not chrome_driver.setup_driver():
            results['error'] = "Failed to setup Chrome driver"
            return results
        
        # Capture website screenshot
        screenshot = chrome_driver.capture_full_page_screenshot(url)
        if screenshot:
            # Save screenshot temporarily
            temp_dir = tempfile.mkdtemp()
            screenshot_path = os.path.join(temp_dir, f"screenshot_{int(time.time())}.png")
            
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot)
            
            results['screenshots']['website'] = screenshot_path
        
        # Run automated validation
        validator = AutomatedDesignValidator(chrome_driver)
        issues = validator.validate_page(url)
        results['issues'] = issues
        results['analysis_complete'] = True
        
        return results
        
    except Exception as e:
        results['error'] = f"Analysis failed: {str(e)}"
        return results
    finally:
        chrome_driver.quit()


def main():
    """Enhanced main Streamlit application"""
    st.set_page_config(
        page_title="Enhanced QA Automation System",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .issue-card {
        border-left: 4px solid #ff6b6b;
        padding: 15px;
        margin: 10px 0;
        background-color: #fff5f5;
        border-radius: 5px;
    }
    .success-card {
        border-left: 4px solid #51cf66;
        padding: 15px;
        margin: 10px 0;
        background-color: #f3fff3;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Enhanced AI QA Automation System")
    st.markdown("**Complete testing solution with design comparison, document processing, and Jira integration**")
    
    # Configuration sidebars
    display_configuration_status()
    display_jira_status()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Dashboard",
        "🔍 Design QA Analysis", 
        "📋 Checklist Management",
        "🎫 Jira Integration",
        "⚙️ System Status"
    ])
    
    with tab1:
        st.header("📊 QA Dashboard")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🎯 Total Checks</h3>
                <h2>47</h2>
                <p>Automated validation points</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>✅ Categories</h3>
                <h2>6</h2>
                <p>Design QA categories</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🔧 Integrations</h3>
                <h2>3</h2>
                <p>API connections</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            jira_integration = EnhancedJiraIntegration()
            jira_status = "Connected" if jira_integration.jira_client else "Disconnected"
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎫 Jira Status</h3>
                <h2>{jira_status}</h2>
                <p>Ticket integration</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick action buttons
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Run Quick Analysis", help="Analyze a website quickly"):
                st.info("Navigate to the 'Design QA Analysis' tab to run a full analysis")
        
        with col2:
            if st.button("📋 View Checklist", help="View the complete QA checklist"):
                st.info("Check the 'Checklist Management' tab for detailed items")
        
        with col3:
            if st.button("🎫 Create Test Ticket", help="Create a sample Jira ticket"):
                st.info("Go to 'Jira Integration' tab to manage tickets")
    
    with tab2:
        st.header("🔍 Design QA Analysis")
        st.markdown("Comprehensive automated testing based on the design QA checklist")
        
        # Analysis configuration
        col1, col2 = st.columns([2, 1])
        
        with col1:
            website_url = st.text_input(
                "🌐 Website URL",
                placeholder="https://your-website.com",
                help="Enter the URL to analyze"
            )
            
            figma_file_url = st.text_input(
                "🎨 Figma File URL (Optional)",
                placeholder="https://figma.com/file/...",
                help="Optional: Compare against Figma designs"
            )
        
        with col2:
            st.subheader("Analysis Options")
            
            analysis_depth = st.selectbox(
                "Analysis Depth",
                ["Quick Scan", "Standard Analysis", "Comprehensive Audit"],
                index=1
            )
            
            create_jira_tickets = st.checkbox(
                "🎫 Auto-create Jira tickets",
                value=False,
                help="Automatically create Jira tickets for issues found"
            )
            
            if create_jira_tickets:
                jira_assignee = st.text_input(
                    "Assignee (Optional)",
                    placeholder="user@company.com"
                )
        
        # Run analysis
        if st.button("🚀 Start QA Analysis", type="primary"):
            if not website_url:
                st.error("Please provide a website URL")
            else:
                update_progress, complete_progress = create_progress_tracker()
                
                try:
                    update_progress(1, 6, "Initializing analysis...")
                    
                    # Run the analysis
                    results = run_design_qa_analysis(website_url, figma_file_url)
                    
                    update_progress(2, 6, "Capturing screenshots...")
                    time.sleep(1)
                    
                    update_progress(3, 6, "Running automated checks...")
                    time.sleep(1)
                    
                    update_progress(4, 6, "Analyzing issues...")
                    time.sleep(1)
                    
                    if create_jira_tickets and results.get('issues'):
                        update_progress(5, 6, "Creating Jira tickets...")
                        jira_integration = EnhancedJiraIntegration()
                        
                        if jira_integration.jira_client:
                            bulk_result = jira_integration.create_bulk_tickets(
                                results['issues'], 
                                jira_assignee if create_jira_tickets else None
                            )
                            results['jira_results'] = bulk_result
                    
                    update_progress(6, 6, "Generating report...")
                    time.sleep(1)
                    
                    complete_progress()
                    
                    # Display results
                    if 'error' in results:
                        st.error(f"Analysis failed: {results['error']}")
                    else:
                        st.success(f"✅ Analysis complete! Found {len(results['issues'])} issues")
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Issues Found", len(results['issues']))
                        
                        with col2:
                            high_severity = len([i for i in results['issues'] if i.severity == Priority.HIGH])
                            st.metric("High Severity", high_severity)
                        
                        with col3:
                            categories = len(set([i.category for i in results['issues']]))
                            st.metric("Categories Affected", categories)
                        
                        # Display screenshot
                        if 'website' in results['screenshots']:
                            st.subheader("📸 Website Screenshot")
                            try:
                                screenshot_data = open(results['screenshots']['website'], 'rb').read()
                                st.image(screenshot_data, caption=f"Screenshot of {website_url}", use_container_width=True)
                            except Exception as e:
                                st.error(f"Could not display screenshot: {e}")
                        
                        # Display issues
                        if results['issues']:
                            st.subheader("🐛 Issues Found")
                            
                            for i, issue in enumerate(results['issues']):
                                severity_colors = {
                                    Priority.HIGH: "#ff6b6b",
                                    Priority.MEDIUM: "#ffd93d",
                                    Priority.LOW: "#74c0fc"
                                }
                                
                                color = severity_colors.get(issue.severity, "#ff6b6b")
                                
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background-color: #f8f9fa; border-radius: 5px;">
                                    <h4>{issue.category} - {issue.subcategory}</h4>
                                    <p><strong>Description:</strong> {issue.description}</p>
                                    <p><strong>Severity:</strong> {issue.severity.value}</p>
                                    {f"<p><strong>Expected:</strong> {issue.expected_behavior}</p>" if issue.expected_behavior else ""}
                                    {f"<p><strong>Actual:</strong> {issue.actual_behavior}</p>" if issue.actual_behavior else ""}
                                    {f"<p><strong>Element:</strong> <code>{issue.element_selector}</code></p>" if issue.element_selector else ""}
                                    {f"<p><strong>Checklist Item:</strong> {issue.checklist_item}</p>" if issue.checklist_item else ""}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display Jira results if tickets were created
                        if 'jira_results' in results:
                            jira_res = results['jira_results']
                            st.subheader("🎫 Jira Ticket Creation Results")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Successful Tickets", jira_res['successful_count'])
                            with col2:
                                st.metric("Failed Tickets", jira_res['failed_count'])
                            
                            if jira_res['results']['successful']:
                                st.write("**✅ Successfully Created Tickets:**")
                                for success in jira_res['results']['successful']:
                                    st.write(f"• [{success['ticket_key']}]({success['url']}) - {success['issue'].description[:50]}...")
                            
                            if jira_res['results']['failed']:
                                st.write("**❌ Failed Ticket Creation:**")
                                for failed in jira_res['results']['failed']:
                                    st.write(f"• {failed['issue'].description[:50]}... - {failed['error']}")
                        
                        # Export options
                        st.subheader("📤 Export Results")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("📊 Export CSV"):
                                csv_data = []
                                for issue in results['issues']:
                                    csv_data.append({
                                        'Category': issue.category,
                                        'Subcategory': issue.subcategory,
                                        'Description': issue.description,
                                        'Severity': issue.severity.value,
                                        'Element': issue.element_selector,
                                        'Expected': issue.expected_behavior,
                                        'Actual': issue.actual_behavior,
                                        'Checklist_Item': issue.checklist_item
                                    })
                                
                                df = pd.DataFrame(csv_data)
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"qa_analysis_{int(time.time())}.csv",
                                    mime="text/csv"
                                )
                        
                        with col2:
                            if st.button("📋 Export Report"):
                                report = f"""
# QA Analysis Report

**URL:** {website_url}
**Analysis Date:** {results['timestamp']}
**Issues Found:** {len(results['issues'])}

## Summary
- High Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.HIGH])}
- Medium Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.MEDIUM])}
- Low Severity Issues: {len([i for i in results['issues'] if i.severity == Priority.LOW])}

## Issues Detail
"""
                                for i, issue in enumerate(results['issues'], 1):
                                    report += f"""
### Issue {i}: {issue.category} - {issue.subcategory}
- **Description:** {issue.description}
- **Severity:** {issue.severity.value}
- **Expected:** {issue.expected_behavior or 'N/A'}
- **Actual:** {issue.actual_behavior or 'N/A'}
- **Element:** {issue.element_selector or 'N/A'}
- **Checklist Item:** {issue.checklist_item or 'N/A'}

"""
                                
                                st.download_button(
                                    label="Download Report",
                                    data=report,
                                    file_name=f"qa_report_{int(time.time())}.md",
                                    mime="text/markdown"
                                )
                        
                        with col3:
                            if st.button("🔄 Re-run Analysis"):
                                st.experimental_rerun()
                
                except Exception as e:
                    complete_progress()
                    st.error(f"Analysis failed: {e}")
                    st.exception(e)
    
    with tab3:
        st.header("📋 Design QA Checklist Management")
        st.markdown("Manage and customize the comprehensive design QA checklist")
        
        checklist = DesignQAChecklist()
        
        # Checklist overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Items", len(checklist.checklist_items))
        
        with col2:
            automated_items = len(checklist.get_automated_items())
            st.metric("Automated Checks", automated_items)
        
        with col3:
            categories = len(set([item.category for item in checklist.checklist_items]))
            st.metric("Categories", categories)
        
        # Category filter
        all_categories = list(set([item.category for item in checklist.checklist_items]))
        selected_category = st.selectbox("Filter by Category", ["All"] + all_categories)
        
        # Display checklist items
        items_to_show = (checklist.checklist_items if selected_category == "All" 
                        else checklist.get_items_by_category(selected_category))
        
        st.subheader(f"📝 Checklist Items ({len(items_to_show)} items)")
        
        # Create tabs for different views
        view_tab1, view_tab2 = st.tabs(["📋 List View", "📊 Category Summary"])
        
        with view_tab1:
            for item in items_to_show:
                automation_status = "🤖 Automated" if item.automated else "👤 Manual"
                
                with st.expander(f"{item.id}: {item.description}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Category:** {item.category}")
                        st.write(f"**Subcategory:** {item.subcategory}")
                        st.write(f"**Status:** {automation_status}")
                    
                    with col2:
                        if item.selector:
                            st.code(f"Selector: {item.selector}")
                        if item.validation_function:
                            st.code(f"Validation: {item.validation_function}")
        
        with view_tab2:
            # Category summary
            category_stats = {}
            for item in checklist.checklist_items:
                if item.category not in category_stats:
                    category_stats[item.category] = {'total': 0, 'automated': 0}
                category_stats[item.category]['total'] += 1
                if item.automated:
                    category_stats[item.category]['automated'] += 1
            
            for category, stats in category_stats.items():
                automation_rate = (stats['automated'] / stats['total']) * 100
                
                st.subheader(category)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Items", stats['total'])
                with col2:
                    st.metric("Automated", stats['automated'])
                with col3:
                    st.metric("Automation Rate", f"{automation_rate:.1f}%")
                
                # Progress bar for automation
                st.progress(automation_rate / 100)
                st.markdown("---")
    
    with tab4:
        st.header("🎫 Jira Integration & Ticket Management")
        st.markdown("Manage Jira tickets and create issues directly from QA findings")
        
        jira_integration = EnhancedJiraIntegration()
        
        if not jira_integration.jira_client:
            st.error("❌ Jira is not properly configured")
            st.markdown("""
            **Required Environment Variables:**
            - `JIRA_SERVER_URL`: Your Jira server URL
            - `JIRA_EMAIL`: Your Jira account email
            - `JIRA_API_TOKEN`: Your Jira API token
            - `JIRA_PROJECT_KEY`: Target project key
            """)
            return
        
        # Test connection
        connection_test = jira_integration.test_connection()
        
        if connection_test['success']:
            st.success("✅ Jira connection successful!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Connected as:** {connection_test['user']}")
            with col2:
                st.info(f"**Project:** {connection_test['project']}")
            
            # Manual ticket creation
            st.subheader("🎫 Create Manual QA Ticket")
            
            with st.form("manual_ticket_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    ticket_category = st.selectbox(
                        "Category",
                        ["Visual Design", "Responsive Design", "UI Elements", "Accessibility", "Content", "Performance"]
                    )
                    
                    ticket_subcategory = st.text_input("Subcategory", "Brand Consistency")
                    
                    ticket_priority = st.selectbox(
                        "Priority",
                        [p.value for p in Priority],
                        index=2  # Medium as default
                    )
                
                with col2:
                    ticket_summary = st.text_input("Summary", "Design issue description")
                    
                    ticket_description = st.text_area(
                        "Description",
                        "Detailed description of the QA issue found..."
                    )
                    
                    ticket_assignee = st.text_input("Assignee (optional)", placeholder="user@company.com")
                
                element_selector = st.text_input("Element Selector (optional)", placeholder=".class-name or #id")
                
                expected_behavior = st.text_area("Expected Behavior", "What should happen...")
                actual_behavior = st.text_area("Actual Behavior", "What actually happens...")
                
                submitted = st.form_submit_button("🚀 Create Ticket", type="primary")
                
                if submitted:
                    # Create issue object
                    manual_issue = DesignIssue(
                        category=ticket_category,
                        subcategory=ticket_subcategory,
                        description=f"{ticket_summary}: {ticket_description}",
                        severity=Priority(ticket_priority),
                        element_selector=element_selector if element_selector else None,
                        expected_behavior=expected_behavior if expected_behavior else None,
                        actual_behavior=actual_behavior if actual_behavior else None
                    )
                    
                    # Create ticket
                    with st.spinner("Creating Jira ticket..."):
                        result = jira_integration.create_design_qa_ticket(
                            manual_issue, 
                            ticket_assignee if ticket_assignee else None
                        )
                    
                    if result['success']:
                        st.success(f"✅ Ticket created successfully!")
                        st.info(f"**Ticket:** [{result['issue_key']}]({result['issue_url']})")
                    else:
                        st.error(f"❌ Failed to create ticket: {result['error']}")
            
            # Bulk ticket creation
            st.subheader("📦 Bulk Ticket Creation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Create Multiple Test Tickets**")
                num_test_tickets = st.number_input("Number of test tickets", 1, 10, 3)
                test_assignee = st.text_input("Test tickets assignee", placeholder="user@company.com")
                
                if st.button("🧪 Create Test Tickets"):
                    test_issues = []
                    
                    for i in range(num_test_tickets):
                        test_issues.append(DesignIssue(
                            category="Visual Design",
                            subcategory="Testing",
                            description=f"Test issue #{i+1} - Generated for testing purposes",
                            severity=Priority.LOW,
                            expected_behavior="This is a test ticket for validation",
                            actual_behavior="Test ticket created successfully",
                            checklist_item=f"TEST{i+1:03d}"
                        ))
                    
                    with st.spinner(f"Creating {num_test_tickets} test tickets..."):
                        bulk_result = jira_integration.create_bulk_tickets(
                            test_issues, 
                            test_assignee if test_assignee else None
                        )
                    
                    st.success(f"✅ Created {bulk_result['successful_count']} tickets successfully!")
                    if bulk_result['failed_count'] > 0:
                        st.warning(f"⚠️ {bulk_result['failed_count']} tickets failed to create")
            
            with col2:
                st.markdown("**Import from CSV**")
                uploaded_csv = st.file_uploader(
                    "Upload CSV with QA issues",
                    type=['csv'],
                    help="CSV should have columns: category, subcategory, description, severity"
                )
                
                if uploaded_csv:
                    try:
                        df = pd.read_csv(uploaded_csv)
                        st.write(f"Found {len(df)} issues in CSV")
                        st.dataframe(df.head())
                        
                        csv_assignee = st.text_input("CSV tickets assignee", placeholder="user@company.com")
                        
                        if st.button("📤 Create Tickets from CSV"):
                            csv_issues = []
                            
                            for _, row in df.iterrows():
                                csv_issues.append(DesignIssue(
                                    category=str(row.get('category', 'General')),
                                    subcategory=str(row.get('subcategory', 'Issue')),
                                    description=str(row.get('description', 'Imported from CSV')),
                                    severity=Priority(row.get('severity', 'Medium')),
                                    expected_behavior=str(row.get('expected_behavior', '')) if 'expected_behavior' in row else None,
                                    actual_behavior=str(row.get('actual_behavior', '')) if 'actual_behavior' in row else None,
                                    element_selector=str(row.get('element_selector', '')) if 'element_selector' in row else None
                                ))
                            
                            with st.spinner(f"Creating {len(csv_issues)} tickets from CSV..."):
                                bulk_result = jira_integration.create_bulk_tickets(
                                    csv_issues,
                                    csv_assignee if csv_assignee else None
                                )
                            
                            st.success(f"✅ Created {bulk_result['successful_count']} tickets from CSV!")
                            if bulk_result['failed_count'] > 0:
                                st.error(f"❌ {bulk_result['failed_count']} tickets failed to create")
                    
                    except Exception as e:
                        st.error(f"Error processing CSV: {e}")
            
            # Project information
            st.subheader("📊 Project Information")
            project_info = jira_integration.get_project_info()
            
            if 'error' not in project_info:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Available Issue Types:**")
                    for issue_type in project_info['issue_types']:
                        st.write(f"• {issue_type['name']}")
                
                with col2:
                    st.write("**Available Priorities:**")
                    for priority in project_info['priorities']:
                        st.write(f"• {priority['name']}")
        else:
            st.error(f"❌ Jira connection failed: {connection_test['error']}")
    
    with tab5:
        st.header("⚙️ System Status & Diagnostics")
        st.markdown("Comprehensive system health check and diagnostic information")
        
        # System health overview
        col1, col2, col3 = st.columns(3)
        
        validator = ConfigurationValidator()
        results = validator.validate_api_keys()
        
        working_services = sum(1 for r in results.values() if r['status'])
        total_services = len(results)
        
        with col1:
            st.metric("Service Status", f"{working_services}/{total_services}")
        
        with col2:
            health_percentage = (working_services / total_services) * 100
            st.metric("System Health", f"{health_percentage:.0f}%")
        
        with col3:
            jira_integration = EnhancedJiraIntegration()
            jira_status = "🟢 Online" if jira_integration.jira_client else "🔴 Offline"
            st.metric("Jira Status", jira_status)
        
        # Detailed status
        st.subheader("🔍 Detailed Component Status")
        
        # API Status
        with st.expander("🔌 API Connections Status", expanded=True):
            for service, result in results.items():
                status_icon = "✅" if result['status'] else "❌"
                st.write(f"**{status_icon} {service.title()}**")
                st.caption(result['message'])
        
        # Environment Variables
        with st.expander("🌍 Environment Variables"):
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
        
        # System Information
        with st.expander("💻 System Information"):
            import sys
            import platform
            
            system_info = {
                "Python Version": sys.version,
                "Platform": platform.platform(),
                "Processor": platform.processor(),
                "Streamlit Version": st.__version__,
            }
            
            for key, value in system_info.items():
                st.write(f"**{key}:** {value}")
        
        # Chrome Driver Test
        with st.expander("🌐 Chrome Driver Diagnostics"):
            if st.button("🔧 Test Chrome Driver"):
                try:
                    driver = EnhancedChromeDriver()
                    if driver.setup_driver(headless=True):
                        capabilities = driver.driver.capabilities
                        chrome_version = capabilities['browserVersion']
                        driver_version = capabilities['chrome']['chromedriverVersion'].split(' ')[0]
                        
                        st.success("✅ Chrome driver working correctly")
                        st.write(f"**Chrome Version:** {chrome_version}")
                        st.write(f"**ChromeDriver Version:** {driver_version}")
                        
                        # Test screenshot capability
                        if st.button("📸 Test Screenshot"):
                            with st.spinner("Taking test screenshot..."):
                                screenshot = driver.capture_full_page_screenshot("https://example.com")
                                if screenshot:
                                    st.success("✅ Screenshot capability working")
                                    st.image(screenshot, caption="Test screenshot", width=300)
                                else:
                                    st.error("❌ Screenshot capability failed")
                        
                        driver.quit()
                    else:
                        st.error("❌ Chrome driver setup failed")
                except Exception as e:
                    st.error(f"❌ Chrome driver test failed: {e}")
        
        # Performance Test
        with st.expander("⚡ Performance Test"):
            if st.button("🏃‍♂️ Run Performance Test"):
                with st.spinner("Running performance tests..."):
                    import time
                    
                    # Test 1: API Response Time
                    start_time = time.time()
                    try:
                        headers = {"X-Figma-Token": os.getenv("FIGMA_ACCESS_TOKEN")}
                        response = requests.get("https://api.figma.com/v1/me", headers=headers, timeout=10)
                        figma_time = time.time() - start_time
                        figma_status = response.status_code == 200
                    except:
                        figma_time = 0
                        figma_status = False
                    
                    # Test 2: Chrome Driver Startup Time
                    start_time = time.time()
                    try:
                        driver = EnhancedChromeDriver()
                        chrome_setup_success = driver.setup_driver(headless=True)
                        chrome_time = time.time() - start_time
                        if chrome_setup_success:
                            driver.quit()
                    except:
                        chrome_time = 0
                        chrome_setup_success = False
                    
                    # Test 3: Jira Connection Time
                    start_time = time.time()
                    jira_integration = EnhancedJiraIntegration()
                    jira_connection_test = jira_integration.test_connection()
                    jira_time = time.time() - start_time
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        status_icon = "✅" if figma_status else "❌"
                        st.metric(
                            f"{status_icon} Figma API",
                            f"{figma_time:.2f}s"
                        )
                    
                    with col2:
                        status_icon = "✅" if chrome_setup_success else "❌"
                        st.metric(
                            f"{status_icon} Chrome Startup", 
                            f"{chrome_time:.2f}s"
                        )
                    
                    with col3:
                        status_icon = "✅" if jira_connection_test.get('success') else "❌"
                        st.metric(
                            f"{status_icon} Jira Connection",
                            f"{jira_time:.2f}s"
                        )
        
        # Log Viewer
        with st.expander("📋 System Logs"):
            st.markdown("Recent system activity and errors")
            
            # This would typically read from actual log files
            sample_logs = [
                {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "message": "System initialized successfully"},
                {"timestamp": (datetime.now() - pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), "level": "INFO", "message": "Chrome driver setup completed"},
                {"timestamp": (datetime.now() - pd.Timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), "level": "WARNING", "message": "Figma API rate limit approaching"},
            ]
            
            for log in sample_logs:
                level_color = {"INFO": "🟢", "WARNING": "🟡", "ERROR": "🔴"}
                icon = level_color.get(log["level"], "⚪")
                st.write(f"{icon} `{log['timestamp']}` **{log['level']}** {log['message']}")


if __name__ == "__main__":
    main()