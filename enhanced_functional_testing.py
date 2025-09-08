"""
Enhanced Functional Testing Agent - Phase 2
Advanced Playwright automation with recording, mobile/desktop testing, and console monitoring
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import base64
from dataclasses import dataclass, asdict

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import streamlit as st
from PIL import Image
import io

logger = logging.getLogger(__name__)

@dataclass
class TestStep:
    """Represents a single test step with all metadata"""
    step_number: int
    action_type: str  # 'click', 'fill', 'navigate', 'wait', 'assert', 'screenshot'
    selector: str
    value: str = ""
    description: str = ""
    screenshot_path: str = ""
    timestamp: str = ""
    element_text: str = ""
    element_attributes: Dict = None
    console_errors: List[str] = None
    performance_metrics: Dict = None
    
    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()
        if self.element_attributes is None:
            self.element_attributes = {}
        if self.console_errors is None:
            self.console_errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}

@dataclass
class TestSession:
    """Complete test session with all steps and metadata"""
    session_id: str
    url: str
    device_type: str  # 'desktop', 'mobile', 'tablet'
    browser_type: str
    viewport_size: Dict[str, int]
    steps: List[TestStep]
    console_errors: List[str]
    performance_summary: Dict
    start_time: str
    end_time: str = ""
    status: str = "running"  # 'running', 'completed', 'failed'
    
    def __post_init__(self):
        if not self.steps:
            self.steps = []
        if not self.console_errors:
            self.console_errors = []
        if not self.performance_summary:
            self.performance_summary = {}

class PlaywrightRecorder:
    """Advanced Playwright recorder with visual feedback and mobile/desktop testing"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.current_session: Optional[TestSession] = None
        self.console_messages = []
        self.screenshots_dir = None
        self.is_recording = False
        
    async def start_session(self, url: str, device_type: str = "desktop", browser_type: str = "chromium") -> TestSession:
        """Start a new recording session"""
        # Create screenshots directory
        self.screenshots_dir = Path(tempfile.mkdtemp(prefix="quali_recording_"))
        
        # Device configurations
        device_configs = {
            "desktop": {"width": 1920, "height": 1080},
            "mobile": {"width": 375, "height": 667},  # iPhone SE
            "tablet": {"width": 768, "height": 1024}   # iPad
        }
        
        viewport = device_configs.get(device_type, device_configs["desktop"])
        
        # Create session
        session_id = f"session_{int(time.time())}"
        self.current_session = TestSession(
            session_id=session_id,
            url=url,
            device_type=device_type,
            browser_type=browser_type,
            viewport_size=viewport,
            steps=[],
            console_errors=[],
            performance_summary={},
            start_time=datetime.now().isoformat()
        )
        
        # Launch browser
        playwright = async_playwright()
        await playwright.start()
        
        if browser_type.lower() == "firefox":
            self.browser = await playwright.firefox.launch(headless=False)
        elif browser_type.lower() == "webkit":
            self.browser = await playwright.webkit.launch(headless=False)
        else:
            self.browser = await playwright.chromium.launch(headless=False)
            
        # Create context with device emulation
        context_options = {
            "viewport": viewport,
            "record_video_dir": str(self.screenshots_dir / "videos"),
        }
        
        # Add mobile user agent if mobile device
        if device_type == "mobile":
            context_options["user_agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        
        # Set up console monitoring
        self.page.on("console", self._handle_console_message)
        self.page.on("pageerror", self._handle_page_error)
        
        # Navigate to initial URL
        await self.page.goto(url)
        
        # Take initial screenshot
        initial_screenshot = await self._take_screenshot("initial_load")
        
        # Add initial step
        initial_step = TestStep(
            step_number=1,
            action_type="navigate",
            selector="",
            value=url,
            description=f"Navigate to {url} on {device_type}",
            screenshot_path=initial_screenshot
        )
        
        self.current_session.steps.append(initial_step)
        self.is_recording = True
        
        return self.current_session
    
    async def record_click(self, selector: str, description: str = "") -> TestStep:
        """Record a click action with visual feedback"""
        if not self.is_recording or not self.page:
            raise Exception("Recording session not active")
            
        step_number = len(self.current_session.steps) + 1
        
        # Wait for element and get info
        element = await self.page.wait_for_selector(selector)
        element_text = await element.text_content()
        element_attributes = await element.evaluate("el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))")
        
        # Highlight element before click (visual feedback)
        await self.page.evaluate(f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.style.outline = '3px solid #22d3ee';
                element.style.outlineOffset = '2px';
                setTimeout(() => element.style.outline = '', 2000);
            }}
        """)
        
        # Take before screenshot
        before_screenshot = await self._take_screenshot(f"step_{step_number}_before")
        
        # Perform click
        await element.click()
        
        # Wait a bit for page changes
        await self.page.wait_for_timeout(1000)
        
        # Take after screenshot
        after_screenshot = await self._take_screenshot(f"step_{step_number}_after")
        
        # Capture console errors that occurred during this step
        step_console_errors = list(self.console_messages[-5:])  # Last 5 messages
        
        # Create step record
        step = TestStep(
            step_number=step_number,
            action_type="click",
            selector=selector,
            description=description or f"Click on element: {element_text[:50]}",
            screenshot_path=after_screenshot,
            element_text=element_text,
            element_attributes=element_attributes,
            console_errors=step_console_errors
        )
        
        self.current_session.steps.append(step)
        return step
    
    async def record_fill(self, selector: str, value: str, description: str = "") -> TestStep:
        """Record a form fill action"""
        if not self.is_recording or not self.page:
            raise Exception("Recording session not active")
            
        step_number = len(self.current_session.steps) + 1
        
        # Wait for element
        element = await self.page.wait_for_selector(selector)
        element_attributes = await element.evaluate("el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))")
        
        # Highlight field
        await self.page.evaluate(f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                element.style.outline = '3px solid #8b5cf6';
                element.style.outlineOffset = '2px';
                setTimeout(() => element.style.outline = '', 2000);
            }}
        """)
        
        # Clear and fill
        await element.clear()
        await element.fill(value)
        
        # Take screenshot
        screenshot_path = await self._take_screenshot(f"step_{step_number}_fill")
        
        step = TestStep(
            step_number=step_number,
            action_type="fill",
            selector=selector,
            value=value,
            description=description or f"Fill field with: {value}",
            screenshot_path=screenshot_path,
            element_attributes=element_attributes
        )
        
        self.current_session.steps.append(step)
        return step
    
    async def inspect_element(self, selector: str) -> Dict[str, Any]:
        """Inspect an element and return detailed information"""
        if not self.page:
            return {}
            
        element = await self.page.wait_for_selector(selector)
        
        # Get comprehensive element info
        element_info = await element.evaluate("""
            el => {
                const rect = el.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(el);
                
                return {
                    tagName: el.tagName,
                    id: el.id,
                    className: el.className,
                    textContent: el.textContent?.trim(),
                    innerHTML: el.innerHTML,
                    attributes: Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value])),
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    styles: {
                        display: computedStyle.display,
                        visibility: computedStyle.visibility,
                        opacity: computedStyle.opacity,
                        backgroundColor: computedStyle.backgroundColor,
                        color: computedStyle.color,
                        fontSize: computedStyle.fontSize,
                        fontFamily: computedStyle.fontFamily
                    },
                    isVisible: el.offsetParent !== null,
                    isEnabled: !el.disabled
                }
            }
        """)
        
        return element_info
    
    async def capture_console_errors(self) -> List[str]:
        """Get all console errors from current session"""
        return list(self.console_messages)
    
    async def capture_performance_metrics(self) -> Dict[str, Any]:
        """Capture performance metrics"""
        if not self.page:
            return {}
            
        metrics = await self.page.evaluate("""
            () => {
                const perfEntries = performance.getEntriesByType('navigation')[0];
                const paintEntries = performance.getEntriesByType('paint');
                
                return {
                    loadTime: perfEntries ? perfEntries.loadEventEnd - perfEntries.fetchStart : 0,
                    domContentLoaded: perfEntries ? perfEntries.domContentLoadedEventEnd - perfEntries.fetchStart : 0,
                    firstPaint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
                    resourcesCount: performance.getEntriesByType('resource').length,
                    memoryUsage: performance.memory ? {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize
                    } : null
                }
            }
        """)
        
        return metrics
    
    async def end_session(self) -> TestSession:
        """End recording session and generate summary"""
        if not self.current_session:
            return None
            
        # Capture final performance metrics
        self.current_session.performance_summary = await self.capture_performance_metrics()
        
        # Capture all console errors
        self.current_session.console_errors = list(self.console_messages)
        
        # Set end time and status
        self.current_session.end_time = datetime.now().isoformat()
        self.current_session.status = "completed"
        
        # Close browser
        if self.browser:
            await self.browser.close()
            
        self.is_recording = False
        
        return self.current_session
    
    async def _take_screenshot(self, name: str) -> str:
        """Take screenshot and return path"""
        if not self.page or not self.screenshots_dir:
            return ""
            
        screenshot_path = self.screenshots_dir / f"{name}.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    
    def _handle_console_message(self, msg):
        """Handle console messages"""
        if msg.type in ['error', 'warning']:
            error_info = {
                'type': msg.type,
                'text': msg.text,
                'url': msg.location.get('url', ''),
                'line': msg.location.get('lineNumber', 0),
                'column': msg.location.get('columnNumber', 0),
                'timestamp': datetime.now().isoformat()
            }
            self.console_messages.append(error_info)
    
    def _handle_page_error(self, error):
        """Handle page errors"""
        error_info = {
            'type': 'pageerror',
            'text': str(error),
            'timestamp': datetime.now().isoformat()
        }
        self.console_messages.append(error_info)

class FunctionalTestingAgent:
    """Enhanced functional testing with AI integration and Jira reporting"""
    
    def __init__(self):
        self.recorder = PlaywrightRecorder()
        self.openai_client = None
        self.jira_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize OpenAI and Jira clients"""
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
            
        try:
            from jira import JIRA
            jira_server = os.getenv("JIRA_SERVER_URL")
            jira_email = os.getenv("JIRA_EMAIL")
            jira_token = os.getenv("JIRA_API_TOKEN")
            
            if all([jira_server, jira_email, jira_token]):
                self.jira_client = JIRA(
                    server=jira_server,
                    basic_auth=(jira_email, jira_token)
                )
        except Exception as e:
            logger.warning(f"Jira client initialization failed: {e}")
    
    async def run_comprehensive_test(self, url: str, test_scenarios: List[Dict], 
                                   devices: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive functional tests across multiple devices"""
        if devices is None:
            devices = ["desktop", "mobile"]
            
        results = {
            "test_summary": {
                "url": url,
                "total_scenarios": len(test_scenarios),
                "devices_tested": devices,
                "start_time": datetime.now().isoformat()
            },
            "device_results": {},
            "issues_found": [],
            "performance_comparison": {},
            "console_errors_summary": [],
            "jira_ticket": None
        }
        
        # Test on each device type
        for device in devices:
            logger.info(f"Starting {device} testing for {url}")
            
            device_results = {
                "device_type": device,
                "sessions": [],
                "issues": [],
                "performance_metrics": {},
                "console_errors": []
            }
            
            # Run each test scenario on this device
            for scenario in test_scenarios:
                try:
                    session = await self._run_scenario_on_device(url, scenario, device)
                    device_results["sessions"].append(session)
                    
                    # Analyze session for issues
                    issues = await self._analyze_session_for_issues(session)
                    device_results["issues"].extend(issues)
                    
                    # Collect console errors
                    device_results["console_errors"].extend(session.console_errors)
                    
                except Exception as e:
                    logger.error(f"Scenario failed on {device}: {e}")
                    device_results["issues"].append({
                        "type": "test_failure",
                        "description": f"Scenario '{scenario.get('name', 'Unknown')}' failed: {str(e)}",
                        "severity": "high"
                    })
            
            results["device_results"][device] = device_results
        
        # Generate AI-powered summary and Jira ticket
        results["jira_ticket"] = await self._generate_jira_ticket(results)
        
        # Update summary
        results["test_summary"]["end_time"] = datetime.now().isoformat()
        results["test_summary"]["total_issues"] = sum(len(dr["issues"]) for dr in results["device_results"].values())
        
        return results
    
    async def _run_scenario_on_device(self, url: str, scenario: Dict, device: str) -> TestSession:
        """Run a single test scenario on a specific device"""
        session = await self.recorder.start_session(url, device)
        
        try:
            # Execute scenario steps
            for step in scenario.get("steps", []):
                if step["action"] == "click":
                    await self.recorder.record_click(step["selector"], step.get("description", ""))
                elif step["action"] == "fill":
                    await self.recorder.record_fill(step["selector"], step["value"], step.get("description", ""))
                elif step["action"] == "wait":
                    await asyncio.sleep(step.get("duration", 1))
                elif step["action"] == "screenshot":
                    await self.recorder._take_screenshot(f"scenario_{step.get('name', 'step')}")
                    
        except Exception as e:
            logger.error(f"Error executing scenario: {e}")
            raise
        finally:
            session = await self.recorder.end_session()
            
        return session
    
    async def _analyze_session_for_issues(self, session: TestSession) -> List[Dict]:
        """Analyze a test session and identify issues"""
        issues = []
        
        # Check for console errors
        if session.console_errors:
            for error in session.console_errors:
                if error.get('type') == 'error':
                    issues.append({
                        "type": "javascript_error",
                        "description": f"Console error: {error.get('text', '')}",
                        "location": f"{error.get('url', '')}:{error.get('line', 0)}",
                        "severity": "medium",
                        "device": session.device_type
                    })
        
        # Check performance issues
        perf = session.performance_summary
        if perf.get('loadTime', 0) > 3000:  # 3 seconds
            issues.append({
                "type": "performance_issue",
                "description": f"Slow page load time: {perf['loadTime']:.2f}ms",
                "severity": "medium",
                "device": session.device_type
            })
        
        # Check for failed steps (if any step took too long or failed)
        for step in session.steps:
            if len(step.console_errors) > 0:
                issues.append({
                    "type": "step_error",
                    "description": f"Errors during step: {step.description}",
                    "step_number": step.step_number,
                    "severity": "low",
                    "device": session.device_type
                })
        
        return issues
    
    async def _generate_jira_ticket(self, test_results: Dict) -> Optional[Dict]:
        """Generate AI-powered Jira ticket from test results"""
        if not self.openai_client or not self.jira_client:
            logger.warning("OpenAI or Jira client not available")
            return None
            
        try:
            # Prepare test data for AI analysis
            all_issues = []
            for device_result in test_results["device_results"].values():
                all_issues.extend(device_result["issues"])
            
            if not all_issues:
                logger.info("No issues found, skipping Jira ticket creation")
                return None
            
            # Generate AI summary
            prompt = f"""
            Analyze these QA test results and create a comprehensive Jira ticket summary:
            
            URL Tested: {test_results['test_summary']['url']}
            Devices: {', '.join(test_results['test_summary']['devices_tested'])}
            Total Issues Found: {len(all_issues)}
            
            Issues Details:
            {json.dumps(all_issues, indent=2)}
            
            Please provide:
            1. A clear, professional title
            2. Executive summary of findings
            3. Detailed breakdown by issue type and severity
            4. Device-specific issues if any
            5. Recommended actions
            6. Priority assessment
            
            Format as a Jira ticket with proper sections.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            ai_summary = response.choices[0].message.content
            
            # Create Jira ticket
            issue_dict = {
                'project': {'key': os.getenv('JIRA_PROJECT_KEY', 'QA')},
                'summary': f"Functional Testing Issues - {test_results['test_summary']['url']}",
                'description': ai_summary,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': 'Medium'},
                'labels': ['automated-testing', 'functional-qa', 'quali-generated']
            }
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            
            return {
                "ticket_key": new_issue.key,
                "ticket_url": f"{self.jira_client.server_url}/browse/{new_issue.key}",
                "ai_summary": ai_summary,
                "issues_count": len(all_issues)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate Jira ticket: {e}")
            return None

# Export for use in main app
__all__ = ['FunctionalTestingAgent', 'PlaywrightRecorder', 'TestStep', 'TestSession']
