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
import tempfile
import shutil

# Load environment variables from .env file
load_dotenv()

class ReportGenerator:
    """Generate comprehensive HTML reports with screenshots and comparisons"""
    
    def __init__(self, base_path="reports"):
        self.base_path = base_path
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_folder = os.path.join(base_path, f"test_report_{self.timestamp}")
        self.screenshots_folder = os.path.join(self.report_folder, "screenshots")
        self.comparisons_folder = os.path.join(self.report_folder, "comparisons")
        
        # Create directories
        os.makedirs(self.screenshots_folder, exist_ok=True)
        os.makedirs(self.comparisons_folder, exist_ok=True)
    
    def save_screenshot(self, image_data, filename, subfolder=""):
        """Save screenshot with proper naming and organization"""
        if subfolder:
            folder_path = os.path.join(self.screenshots_folder, subfolder)
            os.makedirs(folder_path, exist_ok=True)
        else:
            folder_path = self.screenshots_folder
            
        filepath = os.path.join(folder_path, filename)
        
        if isinstance(image_data, bytes):
            with open(filepath, 'wb') as f:
                f.write(image_data)
        else:
            image_data.save(filepath)
        
        return filepath
    
    def generate_comparison_report(self, comparison_results):
        """Generate detailed HTML comparison report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Design Comparison Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; text-align: center; }}
        .page-comparison {{ border: 1px solid #ddd; margin-bottom: 30px; padding: 20px; border-radius: 5px; }}
        .images-container {{ display: flex; gap: 20px; margin: 20px 0; }}
        .image-section {{ flex: 1; text-align: center; }}
        .image-section img {{ max-width: 100%; border: 1px solid #ccc; }}
        .differences {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .discrepancy {{ background: #f8d7da; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Figma vs Website Design Comparison Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Overall Similarity:</strong> <span class="{'pass' if comparison_results['overall_score'] > 0.8 else 'fail'}">{comparison_results['overall_score']:.1%}</span></p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Pages Compared</h3>
            <p>{comparison_results['pages_compared']}</p>
        </div>
        <div class="metric">
            <h3>Issues Found</h3>
            <p>{len(comparison_results['issues_found'])}</p>
        </div>
        <div class="metric">
            <h3>Status</h3>
            <p class="{'pass' if comparison_results['overall_score'] > 0.8 else 'fail'}">
                {'PASS' if comparison_results['overall_score'] > 0.8 else 'FAIL'}
            </p>
        </div>
    </div>
"""
        
        # Add detailed page comparisons
        for detail in comparison_results['comparison_details']:
            figma_path = self.save_screenshot(
                base64.b64decode(detail['figma_image']), 
                f"figma_{detail['page_name'].replace(' ', '_')}.png",
                "figma"
            )
            website_path = self.save_screenshot(
                base64.b64decode(detail['website_image']), 
                f"website_{detail['page_name'].replace(' ', '_')}.png",
                "website"
            )
            
            rel_figma_path = os.path.relpath(figma_path, self.report_folder)
            rel_website_path = os.path.relpath(website_path, self.report_folder)
            
            status_class = "pass" if detail['similarity_score'] > 0.8 else "fail"
            
            html_content += f"""
    <div class="page-comparison">
        <h2>{detail['page_name']} - <span class="{status_class}">{detail['similarity_score']:.1%} Similarity</span></h2>
        
        <div class="images-container">
            <div class="image-section">
                <h3>Figma Design</h3>
                <img src="{rel_figma_path}" alt="Figma design for {detail['page_name']}">
            </div>
            <div class="image-section">
                <h3>Website Screenshot</h3>
                <img src="{rel_website_path}" alt="Website screenshot for {detail['page_name']}">
            </div>
        </div>
"""
            
            if detail['differences']:
                html_content += '<div class="differences"><h3>Discrepancies Found:</h3>'
                for diff in detail['differences']:
                    severity_color = "red" if diff['severity'] == 'high' else "orange"
                    html_content += f'''
                    <div class="discrepancy">
                        <strong style="color: {severity_color};">{diff['severity'].upper()} - {diff['type'].replace('_', ' ').title()}</strong><br>
                        {diff['description']}
                    </div>
                    '''
                html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += """
</body>
</html>
"""
        
        # Save HTML report
        report_path = os.path.join(self.report_folder, "comparison_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path


class DocumentProcessor:
    """Process uploaded documents and extract requirements"""
    
    @staticmethod
    def extract_text_from_pdf(file_content):
        """Extract text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return None
    
    @staticmethod
    def extract_text_from_docx(file_content):
        """Extract text from Word document"""
        try:
            doc = docx.Document(BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {e}")
            return None
    
    @staticmethod
    def extract_text_from_txt(file_content):
        """Extract text from plain text file"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            st.error(f"Error reading TXT: {e}")
            return None
    
    def process_document(self, uploaded_file):
        """Process uploaded document and extract text"""
        file_content = uploaded_file.read()
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file_content)
        elif file_extension == 'docx':
            return self.extract_text_from_docx(file_content)
        elif file_extension == 'txt':
            return self.extract_text_from_txt(file_content)
        else:
            st.error(f"Unsupported file type: {file_extension}")
            return None


class EnhancedTestGenerator:
    """Enhanced test case generation with better parsing and Jira integration"""
    
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.model = model
    
    def generate_from_requirements(self, requirements_text):
        """Generate test cases from requirements document"""
        prompt = f"""
Analyze the following requirements document and generate comprehensive test cases in JSON format.

Requirements:
{requirements_text}

Generate test cases in this EXACT JSON structure:
{{
    "test_suites": [
        {{
            "suite_name": "Functional Tests",
            "description": "Test core functionality",
            "test_cases": [
                {{
                    "id": "TC001",
                    "name": "Test case name",
                    "priority": "High|Medium|Low",
                    "type": "Functional|UI|Integration|Negative",
                    "description": "Detailed description",
                    "preconditions": "What needs to be set up",
                    "test_steps": [
                        "Step 1: Action to perform",
                        "Step 2: Next action",
                        "Step 3: Verification step"
                    ],
                    "expected_result": "What should happen",
                    "test_data": "Any required test data",
                    "automation_priority": "High|Medium|Low"
                }}
            ]
        }}
    ]
}}

Focus on:
1. Happy path scenarios
2. Error handling and edge cases
3. Input validation
4. User interface interactions
5. Integration points
6. Performance considerations
7. Security aspects
8. Accessibility requirements

Make sure the JSON is properly formatted and complete.
"""
        return self.simple_AI_Function_Agent(prompt)
    
    def generate_from_crawl_data(self, crawled_data):
        """Generate test cases from crawled website data"""
        # Create summary of crawled data
        pages_summary = []
        for page in crawled_data['pages']:
            summary = f"""
Page: {page['title']} ({page['url']})
Forms: {len(page['forms'])}
Buttons: {len(page['buttons'])}
Navigation: {len(page['navigation'])}

Form Details:
"""
            for form in page['forms']:
                summary += f"  Action: {form['action']}, Method: {form['method']}\n"
                for inp in form['inputs']:
                    summary += f"    Input: {inp['type']} - {inp['name']} ({'required' if inp['required'] else 'optional'})\n"
            
            summary += f"\nButton Details:\n"
            for button in page['buttons']:
                summary += f"  {button['text']} ({button['type']})\n"
            
            pages_summary.append(summary)
        
        prompt = f"""
Based on the following website crawl data, generate comprehensive test cases in JSON format:

{chr(10).join(pages_summary)}

Generate test cases using this EXACT JSON structure:
{{
    "test_suites": [
        {{
            "suite_name": "Navigation Tests",
            "description": "Test website navigation functionality",
            "test_cases": [
                {{
                    "id": "TC001",
                    "name": "Verify homepage navigation",
                    "priority": "High",
                    "type": "UI",
                    "description": "Verify user can navigate to homepage",
                    "preconditions": "Browser is open",
                    "test_steps": [
                        "Navigate to website URL",
                        "Verify page loads successfully",
                        "Check page title and main elements"
                    ],
                    "expected_result": "Homepage loads with correct title and elements",
                    "test_data": "N/A",
                    "automation_priority": "High"
                }}
            ]
        }}
    ]
}}

Focus on:
1. Form validation tests (positive and negative)
2. Navigation functionality
3. Button click interactions
4. Page load verification
5. Error handling scenarios
6. Cross-browser compatibility
7. Mobile responsiveness
8. Accessibility compliance

Ensure JSON is properly formatted and complete.
"""
        return self.simple_AI_Function_Agent(prompt)
    
    def simple_AI_Function_Agent(self, prompt):
        """Interface with Groq API"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return "Error: GROQ_API_KEY not found in environment variables"
                
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
            )
            response = chat_completion.choices[0].message.content
            return response
        except Exception as e:
            return f"An unexpected error occurred: {e}"


class EnhancedJiraIntegration:
    """Enhanced Jira integration with proper test case and bug creation"""
    
    def __init__(self, server_url, email, api_token, project_key):
        self.server_url = server_url
        self.email = email
        self.api_token = api_token
        self.project_key = project_key
        self.jira = None
    
    def connect(self):
        """Connect to Jira and verify connection"""
        try:
            self.jira = JIRA(
                server=self.server_url,
                basic_auth=(self.email, self.api_token)
            )
            # Test connection
            user = self.jira.myself()
            st.success(f"Connected to Jira as: {user['displayName']}")
            return True
        except Exception as e:
            st.error(f"Failed to connect to Jira: {e}")
            return False
    
    def create_test_cases_from_json(self, test_cases_json):
        """Create test cases in Jira from JSON structure"""
        if not self.jira:
            st.error("Not connected to Jira")
            return []
        
        created_issues = []
        
        try:
            # Parse JSON
            if isinstance(test_cases_json, str):
                # Try to extract JSON from AI response
                json_start = test_cases_json.find('{')
                json_end = test_cases_json.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = test_cases_json[json_start:json_end]
                    test_data = json.loads(json_str)
                else:
                    st.error("Could not extract JSON from response")
                    return []
            else:
                test_data = test_cases_json
            
            # Create test cases
            for suite in test_data.get('test_suites', []):
                for test_case in suite.get('test_cases', []):
                    
                    # Format test steps
                    steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(test_case.get('test_steps', []))])
                    
                    description = f"""
*Test Suite:* {suite['suite_name']}
*Priority:* {test_case.get('priority', 'Medium')}
*Type:* {test_case.get('type', 'Functional')}

*Description:*
{test_case.get('description', '')}

*Preconditions:*
{test_case.get('preconditions', '')}

*Test Steps:*
{steps_text}

*Expected Result:*
{test_case.get('expected_result', '')}

*Test Data:*
{test_case.get('test_data', 'N/A')}

*Automation Priority:* {test_case.get('automation_priority', 'Medium')}
*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    
                    issue_dict = {
                        'project': {'key': self.project_key},
                        'summary': f"[{test_case.get('id', 'TC')}] {test_case['name']}",
                        'description': description,
                        'issuetype': {'name': 'Test'},  # Adjust based on your Jira configuration
                        'priority': {'name': test_case.get('priority', 'Medium')},
                        'labels': ['automated-test', 'ai-generated', suite['suite_name'].lower().replace(' ', '-')]
                    }
                    
                    try:
                        issue = self.jira.create_issue(fields=issue_dict)
                        created_issues.append({
                            'key': issue.key,
                            'name': test_case['name'],
                            'suite': suite['suite_name']
                        })
                        st.success(f"Created test case: {issue.key}")
                    except Exception as e:
                        st.error(f"Failed to create test case '{test_case['name']}': {e}")
            
            return created_issues
            
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {e}")
            st.code(test_cases_json)
            return []
        except Exception as e:
            st.error(f"Error creating test cases: {e}")
            return []
    
    def create_design_comparison_bug(self, page_name, issue_details, figma_image_path=None, website_image_path=None):
        """Create design comparison bug with image attachments"""
        if not self.jira:
            return None
        
        try:
            bug_description = f"""
*Design Comparison Issue*

*Page:* {page_name}
*Issue Type:* {issue_details.get('type', 'Design Mismatch')}
*Severity:* {issue_details.get('severity', 'Medium')}
*Similarity Score:* {issue_details.get('similarity_score', 'N/A')}

*Description:*
{issue_details.get('description', 'Design discrepancy detected between Figma design and website implementation')}

*Detection Method:* Automated Figma vs Website Comparison
*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Expected Result:* Website design should match Figma specifications
*Actual Result:* Design discrepancies detected in automated comparison

*Environment:* Chrome Browser, Automated Design Testing
            """
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': f"Design Issue: {page_name} - {issue_details.get('type', 'Design Mismatch')}",
                'description': bug_description,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'High' if issue_details.get('severity') == 'high' else 'Medium'},
                'labels': ['design-comparison', 'automated-testing', 'figma-integration', 'ui-bug']
            }
            
            bug = self.jira.create_issue(fields=issue_dict)
            
            # Attach images if provided
            if figma_image_path and os.path.exists(figma_image_path):
                try:
                    self.jira.add_attachment(issue=bug, attachment=figma_image_path, filename=f"Figma_Design_{page_name}.png")
                except Exception as e:
                    st.warning(f"Failed to attach Figma image: {e}")
            
            if website_image_path and os.path.exists(website_image_path):
                try:
                    self.jira.add_attachment(issue=bug, attachment=website_image_path, filename=f"Website_Screenshot_{page_name}.png")
                except Exception as e:
                    st.warning(f"Failed to attach website screenshot: {e}")
            
            return bug.key
            
        except Exception as e:
            st.error(f"Failed to create design bug: {e}")
            return None


# Continue with the enhanced Streamlit UI code that addresses the issues...
# [The rest of the code would include the enhanced UI with proper file handling, 
# better error handling, and integration of the new classes]

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Enhanced AI QA Automation",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Enhanced AI QA Automation System")
    st.markdown("**Web Crawling • Document Processing • Test Generation • Design Comparison • Jira Integration**")
    
    # Initialize session state for reports
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = ReportGenerator()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Environment status
        with st.expander("🔍 Environment Status"):
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
        
        # AI Model selection
        st.subheader("🤖 AI Configuration")
        models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
        selected_model = st.selectbox("AI Model", models)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Document Processing", 
        "🌐 Web Crawling", 
        "📝 Test Generation",
        "🎨 Design Comparison",
        "🐛 Jira Integration"
    ])
    
    with tab1:
        st.header("📄 Requirements Document Processing")
        
        uploaded_file = st.file_uploader(
            "Upload Requirements Document", 
            type=['txt', 'pdf', 'docx'],
            help="Upload RFP, acceptance criteria, or requirements document"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            if st.button("📋 Process Document & Generate Test Cases", type="primary"):
                with st.spinner("Processing document and generating test cases..."):
                    # Process document
                    processor = DocumentProcessor()
                    document_text = processor.process_document(uploaded_file)
                    
                    if document_text:
                        st.success("Document processed successfully!")
                        
                        with st.expander("📄 Extracted Text Preview"):
                            st.text_area("Document Content", document_text[:2000] + "...", height=300)
                        
                        # Generate test cases
                        test_generator = EnhancedTestGenerator(selected_model)
                        test_cases = test_generator.generate_from_requirements(document_text)
                        
                        if test_cases and "Error:" not in test_cases:
                            st.session_state['generated_test_cases'] = test_cases
                            st.success("✅ Test cases generated successfully!")
                            
                            with st.expander("📝 Generated Test Cases"):
                                st.code(test_cases, language="json")
                            
                            # Option to create in Jira
                            if st.button("📤 Create Test Cases in Jira"):
                                if all([
                                    os.getenv("JIRA_SERVER_URL"),
                                    os.getenv("JIRA_EMAIL"),
                                    os.getenv("JIRA_API_TOKEN"),
                                    os.getenv("JIRA_PROJECT_KEY")
                                ]):
                                    with st.spinner("Creating test cases in Jira..."):
                                        jira_client = EnhancedJiraIntegration(
                                            os.getenv("JIRA_SERVER_URL"),
                                            os.getenv("JIRA_EMAIL"),
                                            os.getenv("JIRA_API_TOKEN"),
                                            os.getenv("JIRA_PROJECT_KEY")
                                        )
                                        
                                        if jira_client.connect():
                                            created_issues = jira_client.create_test_cases_from_json(test_cases)
                                            
                                            if created_issues:
                                                st.success(f"✅ Created {len(created_issues)} test cases in Jira!")
                                                for issue in created_issues:
                                                    st.write(f"- {issue['key']}: {issue['name']}")
                                            else:
                                                st.error("Failed to create test cases in Jira")
                                else:
                                    st.error("Jira not configured. Please set up your .env file.")
                        else:
                            st.error("Failed to generate test cases. Please check your document and try again.")
                    else:
                        st.error("Failed to extract text from document.")

if __name__ == "__main__":
    main()