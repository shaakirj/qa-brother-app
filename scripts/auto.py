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
from PIL import Image, ImageDraw, ImageChops
import base64
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
import re

# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Advanced AI QA Automation with Figma",
    page_icon="🚀",
    layout="wide"
)

class JiraIntegration:
    """Base Jira integration class"""
    
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
            # Test connection
            self.jira.myself()
            return True
        except Exception as e:
            st.error(f"Failed to connect to Jira: {e}")
            return False
    
    def create_bug(self, summary, description, steps_to_reproduce="", expected_result="", actual_result=""):
        """Create a basic bug in Jira"""
        if not self.jira:
            return None
        
        try:
            bug_description = f"""
*Description:* {description}

*Steps to Reproduce:*
{steps_to_reproduce}

*Expected Result:* {expected_result}
*Actual Result:* {actual_result}

*Detected by:* AI QA Automation System
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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


class FigmaIntegration:
    """Figma API integration for design comparison testing"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": access_token}
    
    def extract_file_id(self, file_id_or_url):
        """Extract file ID from Figma URL or return as-is if already an ID"""
        # If it's already a clean file ID (no slashes/protocols), return it
        if not ('/' in file_id_or_url or 'figma.com' in file_id_or_url):
            return file_id_or_url
        
        # Extract file ID from various Figma URL formats
        patterns = [
            r'figma\.com/design/([a-zA-Z0-9]+)',
            r'figma\.com/file/([a-zA-Z0-9]+)',
            r'figma\.com/proto/([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, file_id_or_url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume it's already a file ID
        return file_id_or_url
    
    def get_file_info(self, file_id_or_url):
        """Get Figma file information and structure"""
        try:
            # Extract clean file ID
            file_id = self.extract_file_id(file_id_or_url)
            
            # Validate file ID format (should be alphanumeric, typically 22-23 characters)
            if not re.match(r'^[a-zA-Z0-9]{15,25}$', file_id):
                st.error(f"Invalid Figma File ID format: {file_id}")
                st.info("File ID should be alphanumeric, 15-25 characters long. Extract it from your Figma URL.")
                return None
            
            url = f"{self.base_url}/files/{file_id}"
            st.info(f"Requesting Figma API: {url}")  # Debug info
            
            response = requests.get(url, headers=self.headers)
            
            # Enhanced error handling with debugging
            if response.status_code == 404:
                st.error(f"File not found (404). This usually means:")
                st.error(f"1. File ID '{file_id}' is incorrect")
                st.error(f"2. You don't have access to this file")
                st.error(f"3. File has been moved or deleted")
                st.info(f"Debug: Full API URL attempted: {url}")
                return None
            elif response.status_code == 403:
                st.error("Access denied (403). This means:")
                st.error("1. Your Figma access token is invalid or expired")
                st.error("2. Token doesn't have permission to access this file")
                st.error("3. You're not signed in to the correct Figma account")
                return None
            elif response.status_code == 401:
                st.error("Authentication failed (401). Your access token is invalid.")
                return None
            elif response.status_code != 200:
                st.error(f"Figma API error {response.status_code}: {response.text}")
                return None
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Network error connecting to Figma API: {e}")
            return None
        except Exception as e:
            st.error(f"Failed to fetch Figma file info: {e}")
            return None
    
    def get_file_images(self, file_id_or_url, node_ids=None, scale=1, format='png'):
        """Get rendered images of Figma nodes"""
        try:
            file_id = self.extract_file_id(file_id_or_url)
            
            url = f"{self.base_url}/images/{file_id}"
            params = {
                'format': format,
                'scale': scale
            }
            if node_ids:
                params['ids'] = ','.join(node_ids)
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 404:
                st.error(f"File or nodes not found (404) when requesting images")
                st.error(f"File ID: {file_id}")
                if node_ids:
                    st.error(f"Node IDs: {node_ids}")
                return None
            elif response.status_code == 403:
                st.error("Access denied (403) when requesting images")
                return None
            elif response.status_code != 200:
                st.error(f"Figma images API error {response.status_code}: {response.text}")
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get Figma images: {e}")
            return None
    
    def extract_design_elements(self, file_data):
        """Extract design elements from Figma file data"""
        design_elements = {
            'pages': [],
            'components': [],
            'text_styles': [],
            'color_styles': [],
            'layout_grids': []
        }
        
        if not file_data or 'document' not in file_data:
            return design_elements
        
        def traverse_nodes(node, parent_name=""):
            if node.get('type') == 'CANVAS':
                # This is a page
                page_info = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'children': [],
                    'background_color': node.get('backgroundColor', {})
                }
                
                # Process child nodes
                for child in node.get('children', []):
                    child_info = traverse_nodes(child, node.get('name'))
                    if child_info:
                        page_info['children'].append(child_info)
                
                design_elements['pages'].append(page_info)
                return page_info
            
            elif node.get('type') == 'FRAME':
                # This is a frame/container
                frame_info = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'type': 'FRAME',
                    'x': node.get('absoluteBoundingBox', {}).get('x', 0),
                    'y': node.get('absoluteBoundingBox', {}).get('y', 0),
                    'width': node.get('absoluteBoundingBox', {}).get('width', 0),
                    'height': node.get('absoluteBoundingBox', {}).get('height', 0),
                    'fills': node.get('fills', []),
                    'strokes': node.get('strokes', []),
                    'children': []
                }
                
                # Process child nodes
                for child in node.get('children', []):
                    child_info = traverse_nodes(child, node.get('name'))
                    if child_info:
                        frame_info['children'].append(child_info)
                
                return frame_info
            
            elif node.get('type') == 'TEXT':
                # Text element
                text_info = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'type': 'TEXT',
                    'x': node.get('absoluteBoundingBox', {}).get('x', 0),
                    'y': node.get('absoluteBoundingBox', {}).get('y', 0),
                    'width': node.get('absoluteBoundingBox', {}).get('width', 0),
                    'height': node.get('absoluteBoundingBox', {}).get('height', 0),
                    'characters': node.get('characters', ''),
                    'style': node.get('style', {}),
                    'fills': node.get('fills', [])
                }
                return text_info
            
            elif node.get('type') in ['RECTANGLE', 'ELLIPSE', 'POLYGON', 'STAR', 'VECTOR']:
                # Shape elements
                shape_info = {
                    'id': node.get('id'),
                    'name': node.get('name'),
                    'type': node.get('type'),
                    'x': node.get('absoluteBoundingBox', {}).get('x', 0),
                    'y': node.get('absoluteBoundingBox', {}).get('y', 0),
                    'width': node.get('absoluteBoundingBox', {}).get('width', 0),
                    'height': node.get('absoluteBoundingBox', {}).get('height', 0),
                    'fills': node.get('fills', []),
                    'strokes': node.get('strokes', []),
                    'corner_radius': node.get('cornerRadius', 0)
                }
                return shape_info
            
            elif node.get('children'):
                # Process children for other node types
                for child in node.get('children', []):
                    traverse_nodes(child, parent_name)
        
        # Start traversing from document root
        for child in file_data['document'].get('children', []):
            traverse_nodes(child)
        
        return design_elements
    
    def test_token_and_file_access(self, file_id_or_url):
        """Test token validity and file access - debug method"""
        try:
            file_id = self.extract_file_id(file_id_or_url)
            
            st.info("Debugging Figma Access")
            st.write(f"**File ID extracted:** `{file_id}`")
            st.write(f"**Token length:** {len(self.access_token) if self.access_token else 0} characters")
            st.write(f"**Token starts with:** `{self.access_token[:10]}...` (showing first 10 chars only)")
            
            # Test 1: Check token validity with /me endpoint
            st.write("\n**Test 1: Token validity**")
            me_response = requests.get(f"{self.base_url}/me", headers=self.headers)
            if me_response.status_code == 200:
                user_info = me_response.json()
                st.success(f"Token valid - User: {user_info.get('email', 'Unknown')}")
            else:
                st.error(f"Token invalid - Status: {me_response.status_code}")
                st.code(me_response.text)
                return False
            
            # Test 2: Check file access
            st.write("\n**Test 2: File access**")
            file_url = f"{self.base_url}/files/{file_id}"
            file_response = requests.get(file_url, headers=self.headers)
            
            st.write(f"**API URL:** `{file_url}`")
            st.write(f"**Response Status:** {file_response.status_code}")
            
            if file_response.status_code == 200:
                st.success("File accessible!")
                return True
            else:
                st.error(f"File access failed")
                st.code(file_response.text[:500])  # Show first 500 chars of error
                
                # Provide specific guidance
                if file_response.status_code == 404:
                    st.error("**Possible solutions:**")
                    st.write("1. Verify the file ID is correct")
                    st.write("2. Ensure you have 'can view' access to this file")
                    st.write("3. Check if the file still exists")
                    st.write("4. Try accessing the file in your browser first")
                elif file_response.status_code == 403:
                    st.error("**Token/Permission issue:**")
                    st.write("1. Regenerate your personal access token in Figma")
                    st.write("2. Ensure the token has file access permissions")
                    st.write("3. Check you're using the token from the correct account")
                
                return False
            
        except Exception as e:
            st.error(f"Debug test failed: {e}")
            return False


class DesignComparisonTester:
    """Compare Figma designs with live website screenshots"""
    
    def __init__(self, figma_integration):
        self.figma = figma_integration
        self.driver = None
        self.comparison_results = []
    
    def setup_driver(self):
        """Setup Chrome driver for screenshot capture"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--force-device-scale-factor=1")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            st.error(f"Failed to setup driver for design comparison: {e}")
            return False
    
    def capture_website_screenshot(self, url, element_selector=None):
        """Capture screenshot of website or specific element"""
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            if element_selector:
                element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                return element.screenshot_as_png
            else:
                return self.driver.get_screenshot_as_png()
        except Exception as e:
            st.error(f"Failed to capture screenshot: {e}")
            return None
    
    def download_figma_image(self, image_url):
        """Download image from Figma API"""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            st.error(f"Failed to download Figma image: {e}")
            return None
    
    def compare_images(self, figma_image_data, website_image_data, comparison_type="structural"):
        """Compare Figma design with website screenshot"""
        try:
            figma_img = Image.open(BytesIO(figma_image_data))
            website_img = Image.open(BytesIO(website_image_data))
            
            min_width = min(figma_img.width, website_img.width)
            min_height = min(figma_img.height, website_img.height)
            
            figma_resized = figma_img.resize((min_width, min_height), Image.Resampling.LANCZOS)
            website_resized = website_img.resize((min_width, min_height), Image.Resampling.LANCZOS)
            
            figma_array = np.array(figma_resized.convert('RGB'))
            website_array = np.array(website_resized.convert('RGB'))
            
            comparison_result = {
                'similarity_score': 0,
                'differences_found': [],
                'comparison_image': None,
                'figma_dimensions': (figma_img.width, figma_img.height),
                'website_dimensions': (website_img.width, website_img.height)
            }
            
            if comparison_type == "structural":
                gray_figma = cv2.cvtColor(figma_array, cv2.COLOR_RGB2GRAY)
                gray_website = cv2.cvtColor(website_array, cv2.COLOR_RGB2GRAY)
                
                score, diff = ssim(gray_figma, gray_website, full=True)
                comparison_result['similarity_score'] = score
                
                diff = (diff * 255).astype("uint8")
                comparison_result['comparison_image'] = diff
                
                if score < 0.9:
                    comparison_result['differences_found'].append({
                        'type': 'structural_difference',
                        'severity': 'high' if score < 0.7 else 'medium',
                        'description': f'Structural similarity: {score:.2%}'
                    })
            
            elif comparison_type == "pixel_perfect":
                diff = ImageChops.difference(figma_resized.convert('RGB'), website_resized.convert('RGB'))
                diff_array = np.array(diff)
                
                different_pixels = np.count_nonzero(diff_array.sum(axis=2))
                total_pixels = diff_array.shape[0] * diff_array.shape[1]
                difference_percentage = (different_pixels / total_pixels) * 100
                
                comparison_result['similarity_score'] = 1 - (difference_percentage / 100)
                comparison_result['comparison_image'] = np.array(diff)
                
                if difference_percentage > 5:
                    comparison_result['differences_found'].append({
                        'type': 'pixel_difference',
                        'severity': 'high' if difference_percentage > 20 else 'medium',
                        'description': f'Pixel difference: {difference_percentage:.1f}%'
                    })
            
            return comparison_result
            
        except Exception as e:
            st.error(f"Image comparison failed: {e}")
            return None
    
    def perform_design_comparison(self, figma_file_id, website_url, pages_to_compare=None):
        """Perform complete design comparison between Figma and website"""
        if not self.setup_driver():
            return None

        results = {
            'overall_score': 0,
            'pages_compared': 0,
            'issues_found': [],
            'comparison_details': []
        }

        try:
            st.info("Fetching Figma file data...")
            file_data = self.figma.get_file_info(figma_file_id)
            if not file_data:
                return None

            design_elements = self.figma.extract_design_elements(file_data)

            page_node_ids = [page['id'] for page in design_elements['pages']]
            if pages_to_compare:
                page_node_ids = [
                    pid for pid in page_node_ids
                    if any(page['name'].lower() in pages_to_compare for page in design_elements['pages'] if page['id'] == pid)
                ]

            # Adaptive batching logic for Figma API calls
            batch_size = 3  # Conservative batch size
            scale = 2  # Image scale
            
            st.info(f"Generating Figma design images in batches (batch_size={batch_size}, scale={scale})...")
            batched_images = {}

            def fetch_with_retry(node_ids, scale, batch_label=""):
                """Try fetching node images, progressively reducing batch size if needed"""
                if not node_ids:
                    return {}

                # Try full batch first
                response = self.figma.get_file_images(figma_file_id, node_ids, scale=scale)
                if response and 'images' in response:
                    return response['images']

                # If batch failed, reduce batch size
                if len(node_ids) > 1:
                    mid = len(node_ids) // 2
                    st.warning(f"Batch {batch_label} failed at scale {scale}, splitting into smaller batches...")
                    left = fetch_with_retry(node_ids[:mid], scale, batch_label + "L")
                    right = fetch_with_retry(node_ids[mid:], scale, batch_label + "R")
                    return {**left, **right}
                else:
                    # Single node request failed, retry with scale=1 if not already
                    if scale != 1:
                        st.warning(f"Node {node_ids[0]} failed at scale {scale}, retrying at scale=1...")
                        return fetch_with_retry(node_ids, 1, batch_label)
                    else:
                        st.error(f"Node {node_ids[0]} failed even at scale=1. Skipping...")
                        return {}

            # Process in top-level batches
            for i in range(0, len(page_node_ids), batch_size):
                batch = page_node_ids[i:i + batch_size]
                images = fetch_with_retry(batch, scale, f"{i//batch_size+1}")
                batched_images.update(images)

            if not batched_images:
                st.error("Failed to get any Figma images")
                return None

            total_score = 0
            pages_processed = 0

            for page in design_elements['pages']:
                if page['id'] not in batched_images:
                    continue

                st.info(f"Comparing page: {page['name']}")

                figma_image_url = batched_images[page['id']]
                figma_image_data = self.download_figma_image(figma_image_url)
                if not figma_image_data:
                    continue

                website_image_data = self.capture_website_screenshot(website_url)
                if not website_image_data:
                    continue

                comparison = self.compare_images(figma_image_data, website_image_data, "structural")

                if comparison:
                    page_result = {
                        'page_name': page['name'],
                        'page_id': page['id'],
                        'similarity_score': comparison['similarity_score'],
                        'differences': comparison['differences_found'],
                        'figma_image': base64.b64encode(figma_image_data).decode(),
                        'website_image': base64.b64encode(website_image_data).decode(),
                        'comparison_image': base64.b64encode(
                            cv2.imencode('.png', comparison['comparison_image'])[1]
                        ).decode() if comparison['comparison_image'] is not None else None
                    }

                    results['comparison_details'].append(page_result)
                    total_score += comparison['similarity_score']
                    pages_processed += 1

                    for diff in comparison['differences_found']:
                        issue = {
                            'page': page['name'],
                            'type': diff['type'],
                            'severity': diff['severity'],
                            'description': diff['description'],
                            'figma_image': figma_image_data,
                            'website_image': website_image_data
                        }
                        results['issues_found'].append(issue)

            results['overall_score'] = total_score / pages_processed if pages_processed > 0 else 0
            results['pages_compared'] = pages_processed
            return results

        except Exception as e:
            st.error(f"Design comparison failed: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()


class EnhancedJiraIntegration(JiraIntegration):
    """Enhanced Jira integration with design comparison bug reporting"""
    
    def create_design_bug(self, page_name, issue_details, figma_image=None, website_image=None):
        """Create design-specific bug in Jira with images"""
        if not self.jira:
            return None
        
        try:
            bug_description = f"""
*Design Comparison Issue*

*Page:* {page_name}
*Issue Type:* {issue_details.get('type', 'Unknown')}
*Severity:* {issue_details.get('severity', 'Medium')}
*Description:* {issue_details.get('description', '')}

*Detected by:* AI Design Comparison System
*Comparison Method:* Automated Figma vs Website Analysis
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Expected Result:* Website design should match Figma specifications
*Actual Result:* Design discrepancies detected in automated comparison

*Environment:* Chrome Browser, Design Comparison Testing
            """
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': f"Design Issue: {page_name} - {issue_details.get('type', 'Design Mismatch')}",
                'description': bug_description,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'High' if issue_details.get('severity') == 'high' else 'Medium'},
                'labels': ['design-comparison', 'automated-testing', 'figma-integration']
            }
            
            bug = self.jira.create_issue(fields=issue_dict)
            
            # Attach images if provided
            if figma_image and bug:
                try:
                    # Create temporary file for Figma design
                    figma_filename = f"figma_design_{page_name}_{bug.key}.png"
                    with open(figma_filename, 'wb') as f:
                        f.write(figma_image)
                    
                    self.jira.add_attachment(issue=bug, attachment=figma_filename, filename=f"Figma_Design_{page_name}.png")
                    os.remove(figma_filename)  # Clean up
                except Exception as e:
                    st.warning(f"Failed to attach Figma image: {e}")
            
            if website_image and bug:
                try:
                    # Create temporary file for website screenshot
                    website_filename = f"website_screenshot_{page_name}_{bug.key}.png"
                    with open(website_filename, 'wb') as f:
                        f.write(website_image)
                    
                    self.jira.add_attachment(issue=bug, attachment=website_filename, filename=f"Website_Screenshot_{page_name}.png")
                    os.remove(website_filename)  # Clean up
                except Exception as e:
                    st.warning(f"Failed to attach website screenshot: {e}")
            
            return bug.key
            
        except Exception as e:
            st.error(f"Failed to create design bug: {e}")
            return None


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


def generate_test_cases_from_crawl(crawled_data, model):
    """Generate test cases from crawled website data"""
    if not crawled_data or not crawled_data['pages']:
        return "No crawled data available"
    
    # Create summary of crawled data for prompt
    pages_summary = []
    for page in crawled_data['pages']:
        summary = f"Page: {page['title']} ({page['url']})\n"
        summary += f"Forms: {len(page['forms'])}, Buttons: {len(page['buttons'])}\n"
        if page['forms']:
            summary += "Form details:\n"
            for form in page['forms']:
                summary += f"  - Action: {form['action']}, Method: {form['method']}\n"
                for inp in form['inputs']:
                    summary += f"    Input: {inp['type']} - {inp['name']}\n"
        pages_summary.append(summary)
    
    prompt = f"""
Based on the following website crawl data, generate comprehensive test cases in JSON format:

{chr(10).join(pages_summary)}

Generate test cases that cover:
1. Navigation testing
2. Form functionality
3. Button interactions
4. Page loading and content verification
5. Error handling scenarios

Format as JSON with test suites and individual test cases.
"""
    
    return simple_AI_Function_Agent(prompt, model)


# Streamlit UI
st.title("Advanced AI QA Automation with Figma Integration")
st.markdown("**Web Crawling • Design Comparison • Test Generation • Jira Integration • Automated Execution**")

# Sidebar configuration
st.sidebar.header("Configuration")

# Check for environment variables
env_status = st.sidebar.expander("Environment Status")
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
        st.error("⚠️ FIGMA_ACCESS_TOKEN not found in .env file")
    
    if not jira_configured:
        st.warning("⚠️ Jira credentials incomplete in .env file")

# Override options (for testing/development only)
with st.sidebar.expander("Development Override (Not Recommended)"):
    st.warning("⚠️ Only use for testing. Use .env file for production!")
    
    override_groq = st.text_input("Override Groq API Key", type="password", help="Temporary override - use .env instead", key="override_groq")
    if override_groq:
        os.environ["GROQ_API_KEY"] = override_groq
        st.success("Groq API key temporarily overridden")
    
    override_figma = st.text_input("Override Figma Access Token", type="password", help="Get from Figma > Settings > Personal access tokens", key="override_figma")
    if override_figma:
        os.environ["FIGMA_ACCESS_TOKEN"] = override_figma
        st.success("Figma token temporarily overridden")
    
    st.subheader("Jira Override")
    override_jira_server = st.text_input("Override Jira Server", placeholder="https://yourcompany.atlassian.net", key="override_jira_server")
    override_jira_email = st.text_input("Override Jira Email", placeholder="your-email@company.com", key="override_jira_email")
    override_jira_token = st.text_input("Override Jira Token", type="password", key="override_jira_token")
    override_jira_project = st.text_input("Override Project Key", placeholder="TEST", key="override_jira_project")
    
    if all([override_jira_server, override_jira_email, override_jira_token, override_jira_project]):
        os.environ["JIRA_SERVER_URL"] = override_jira_server
        os.environ["JIRA_EMAIL"] = override_jira_email
        os.environ["JIRA_API_TOKEN"] = override_jira_token
        os.environ["JIRA_PROJECT_KEY"] = override_jira_project
        st.success("Jira settings temporarily overridden")

# Model and workflow selection
st.sidebar.subheader("AI Configuration")
models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
selected_model = st.sidebar.selectbox("AI Model", models, key="ai_model_selection")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Web Crawling", 
    "Design Comparison", 
    "Test Generation", 
    "Test Execution", 
    "Bug Management",
    "Results Dashboard"
])

with tab1:
    st.header("Website Crawler & Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        website_url = st.text_input("Website URL to Crawl", placeholder="https://example.com", key="crawl_website_url")
        
        col_a, col_b = st.columns(2)
        with col_a:
            max_pages = st.number_input("Max Pages to Crawl", min_value=1, max_value=20, value=5, key="crawl_max_pages")
        with col_b:
            crawl_depth = st.number_input("Crawling Depth", min_value=1, max_value=3, value=2, key="crawl_depth")
    
    with col2:
        st.info("""
        **Crawling Options:**
        - Max Pages: Limit crawled pages
        - Depth: How deep to follow links
        - Extracts: Forms, buttons, navigation, content
        """)
    
    if st.button("Start Web Crawling", type="primary"):
        if not website_url:
            st.error("Please enter a website URL!")
        else:
            with st.spinner("Crawling website... This may take a few minutes."):
                crawler = WebCrawler()
                crawled_data = crawler.crawl_website(website_url, max_pages, crawl_depth)
                
                if crawled_data and crawled_data['pages']:
                    st.session_state['crawled_data'] = crawled_data
                    st.success(f"Successfully crawled {len(crawled_data['pages'])} pages!")
                    
                    # Display crawl results
                    for i, page in enumerate(crawled_data['pages']):
                        with st.expander(f"Page {i+1}: {page['title']}"):
                            st.write(f"**URL:** {page['url']}")
                            st.write(f"**Forms Found:** {len(page['forms'])}")
                            st.write(f"**Buttons Found:** {len(page['buttons'])}")
                            st.write(f"**Content Preview:** {page['content'][:300]}...")
                else:
                    st.error("Failed to crawl website. Please check the URL and try again.")

with tab2:
    st.header("Figma Design Comparison Testing")
    
    # Check if Figma is configured
    figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
    
    if not figma_token:
        st.error("Figma Access Token not configured. Please add FIGMA_ACCESS_TOKEN to your .env file.")
        st.info("""
        **How to get Figma Access Token:**
        1. Go to Figma.com and log in
        2. Navigate to Settings > Personal access tokens
        3. Generate a new token with appropriate permissions
        4. Add it to your .env file as FIGMA_ACCESS_TOKEN=your_token_here
        """)
    else:
        st.success("Figma integration configured!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            figma_file_id = st.text_input(
                "Figma File ID", 
                placeholder="e.g., ABC123DEF456 (from Figma URL)",
                help="Get this from your Figma file URL: figma.com/file/FILE_ID/...",
                key="figma_file_id"
            )
            if st.button("Test Figma Access (Debug)", type="secondary"):
                figma = FigmaIntegration(figma_token)
                figma.test_token_and_file_access(figma_file_id)
            
            website_url = st.text_input(
                "Website URL to Compare",
                placeholder="https://example.com",
                key="figma_website_url"
            )
            
            comparison_pages = st.text_area(
                "Specific Pages to Compare (optional)",
                placeholder="Leave empty to compare all pages, or enter page names separated by commas",
                help="e.g., Homepage, About Us, Contact",
                key="figma_comparison_pages"
            )
        
        with col2:
            st.info("""
            **Design Comparison Features:**
            - Structural similarity analysis
            - Pixel-perfect comparison
            - Color palette validation
            - Layout spacing verification
            - Typography consistency check
            """)
        
        comparison_settings = st.expander("Advanced Comparison Settings")
        with comparison_settings:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                comparison_threshold = st.slider("Similarity Threshold", 0.5, 1.0, 0.85, 0.05, key="comparison_threshold")
            with col_b:
                screenshot_scale = st.selectbox("Screenshot Scale", [1, 2, 3], index=1, key="screenshot_scale")
            with col_c:
                comparison_method = st.selectbox("Comparison Method", ["structural", "pixel_perfect"], key="comparison_method")
        
        if st.button("Start Design Comparison", type="primary"):
            if not figma_file_id or not website_url:
                st.error("Please provide both Figma File ID and Website URL!")
            else:
                with st.spinner("Performing design comparison... This may take several minutes."):
                    try:
                        # Initialize Figma integration
                        figma = FigmaIntegration(figma_token)
                        
                        # Initialize design comparison tester
                        comparison_tester = DesignComparisonTester(figma)
                        
                        # Parse pages to compare
                        pages_filter = None
                        if comparison_pages.strip():
                            pages_filter = [page.strip().lower() for page in comparison_pages.split(',')]
                        
                        # Perform comparison
                        results = comparison_tester.perform_design_comparison(
                            figma_file_id, 
                            website_url, 
                            pages_filter
                        )
                        
                        if results:
                            st.session_state['design_comparison_results'] = results
                            
                            # Display summary
                            st.success(f"Design comparison completed!")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Overall Similarity", f"{results['overall_score']:.1%}")
                            with col2:
                                st.metric("Pages Compared", results['pages_compared'])
                            with col3:
                                st.metric("Issues Found", len(results['issues_found']))
                            with col4:
                                status = "Pass" if results['overall_score'] >= comparison_threshold else "Fail"
                                st.metric("Status", status)
                            
                            # Display detailed results
                            st.subheader("Comparison Details")
                            
                            for detail in results['comparison_details']:
                                with st.expander(f"{detail['page_name']} (Similarity: {detail['similarity_score']:.1%})"):
                                    
                                    # Show images side by side
                                    img_col1, img_col2, img_col3 = st.columns(3)
                                    
                                    with img_col1:
                                        st.subheader("Figma Design")
                                        figma_img_data = base64.b64decode(detail['figma_image'])
                                        st.image(figma_img_data, use_container_width=True)
                                    
                                    with img_col2:
                                        st.subheader("Website Screenshot")
                                        website_img_data = base64.b64decode(detail['website_image'])
                                        st.image(website_img_data, use_container_width=True)
                                    
                                    with img_col3:
                                        if detail['comparison_image']:
                                            st.subheader("Difference Map")
                                            comparison_img_data = base64.b64decode(detail['comparison_image'])
                                            st.image(comparison_img_data, use_container_width=True)
                                    
                                    # Show differences found
                                    if detail['differences']:
                                        st.subheader("Issues Detected")
                                        for diff in detail['differences']:
                                            severity_color = "High" if diff['severity'] == 'high' else "Medium"
                                            st.write(f"**{severity_color} - {diff['type'].title()}**: {diff['description']}")
                            
                            # Auto-create Jira tickets option
                            if results['issues_found'] and all([
                                os.getenv("JIRA_SERVER_URL"),
                                os.getenv("JIRA_EMAIL"),
                                os.getenv("JIRA_API_TOKEN"),
                                os.getenv("JIRA_PROJECT_KEY")
                            ]):
                                st.subheader("Jira Integration")
                                if st.button("Create Jira Tickets for Issues Found", type="secondary"):
                                    with st.spinner("Creating Jira tickets..."):
                                        jira_client = EnhancedJiraIntegration(
                                            os.getenv("JIRA_SERVER_URL"),
                                            os.getenv("JIRA_EMAIL"),
                                            os.getenv("JIRA_API_TOKEN"),
                                            os.getenv("JIRA_PROJECT_KEY")
                                        )
                                        
                                        if jira_client.connect():
                                            tickets_created = []
                                            for issue in results['issues_found']:
                                                ticket_key = jira_client.create_design_bug(
                                                    issue['page'],
                                                    issue,
                                                    issue.get('figma_image'),
                                                    issue.get('website_image')
                                                )
                                                if ticket_key:
                                                    tickets_created.append(ticket_key)
                                            
                                            if tickets_created:
                                                st.success(f"Created {len(tickets_created)} Jira tickets!")
                                                for ticket in tickets_created:
                                                    st.write(f"- {ticket}")
                                            else:
                                                st.error("Failed to create Jira tickets")
                                        else:
                                            st.error("Failed to connect to Jira")
                        else:
                            st.error("Design comparison failed. Please check your Figma File ID and try again.")
                    
                    except Exception as e:
                        st.error(f"Design comparison error: {e}")
                        st.exception(e)