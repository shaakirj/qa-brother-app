"""
Streamlit UI for Enhanced Functional Testing - Phase 2
Interactive recording interface with visual step-by-step feedback
"""

import streamlit as st
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
import tempfile
from PIL import Image
import base64
import io
from typing import Dict, List, Optional, Any

try:
    from enhanced_functional_testing import (
        FunctionalTestingAgent, 
        PlaywrightRecorder, 
        TestStep, 
        TestSession
    )
    FUNCTIONAL_TESTING_AVAILABLE = True
except ImportError as e:
    st.error(f"Enhanced functional testing not available: {e}")
    FUNCTIONAL_TESTING_AVAILABLE = False

def render_functional_testing_ui():
    """Main UI for enhanced functional testing"""
    
    if not FUNCTIONAL_TESTING_AVAILABLE:
        st.error("Enhanced functional testing is not available. Please check dependencies.")
        return
    
    st.header("🎯 Enhanced Functional Testing - Phase 2")
    st.markdown("""
    **Advanced QA automation with interactive recording, multi-device testing, and AI-powered insights**
    
    🎬 **Interactive Recording** - Click, fill, inspect elements with visual feedback  
    📱 **Multi-Device Testing** - Desktop, mobile, tablet validation  
    🐛 **Console Error Monitoring** - Capture and analyze JavaScript errors  
    🎫 **Smart Jira Integration** - AI-generated tickets with comprehensive summaries  
    """)
    
    # Initialize session state
    if 'functional_agent' not in st.session_state:
        st.session_state.functional_agent = None
    if 'recording_session' not in st.session_state:
        st.session_state.recording_session = None
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎬 Interactive Recording", 
        "📋 Test Scenarios", 
        "🚀 Run Tests", 
        "📊 Results & Analysis"
    ])
    
    with tab1:
        render_interactive_recording_tab()
    
    with tab2:
        render_test_scenarios_tab()
    
    with tab3:
        render_run_tests_tab()
    
    with tab4:
        render_results_analysis_tab()

def render_interactive_recording_tab():
    """Interactive recording interface"""
    st.subheader("🎬 Interactive Test Recording")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Record user interactions in real-time:**
        - Visual element highlighting during recording
        - Automatic screenshots for each step
        - Console error monitoring
        - DOM inspection capabilities
        """)
        
        # Recording configuration
        url = st.text_input("🌐 Website URL", 
                           value="https://scans.staging2.liquidpreview2.net/",
                           help="URL to test")
        
        col_device, col_browser = st.columns(2)
        with col_device:
            device_type = st.selectbox("📱 Device Type", 
                                     ["desktop", "mobile", "tablet"],
                                     help="Device to emulate")
        
        with col_browser:
            browser_type = st.selectbox("🌐 Browser", 
                                      ["chromium", "firefox", "webkit"],
                                      help="Browser engine to use")
        
        # Recording controls
        col_start, col_stop, col_status = st.columns(3)
        
        with col_start:
            if st.button("🔴 Start Recording", type="primary", 
                        disabled=st.session_state.recording_session is not None):
                start_recording_session(url, device_type, browser_type)
        
        with col_stop:
            if st.button("⏹️ Stop Recording", 
                        disabled=st.session_state.recording_session is None):
                stop_recording_session()
        
        with col_status:
            if st.session_state.recording_session:
                st.success("🟢 Recording Active")
            else:
                st.info("⚪ Ready to Record")
    
    with col2:
        # Recording status and quick actions
        if st.session_state.recording_session:
            st.markdown("### 🎯 Quick Actions")
            
            # Element inspector
            with st.expander("🔍 Inspect Element", expanded=True):
                selector = st.text_input("CSS Selector", 
                                        placeholder="e.g., button.login-btn",
                                        key="inspect_selector")
                if st.button("🔍 Inspect"):
                    inspect_element(selector)
            
            # Manual step recording
            with st.expander("➕ Record Step"):
                action_type = st.selectbox("Action", ["click", "fill", "wait", "screenshot"])
                step_selector = st.text_input("Selector", key="step_selector")
                step_value = st.text_input("Value (for fill)", key="step_value")
                step_desc = st.text_input("Description", key="step_desc")
                
                if st.button("➕ Add Step"):
                    record_manual_step(action_type, step_selector, step_value, step_desc)
            
            # Console monitor
            with st.expander("🐛 Console Monitor"):
                if st.button("🔄 Refresh Console"):
                    refresh_console_errors()
                
                if st.session_state.get('console_errors'):
                    for error in st.session_state.console_errors[-5:]:
                        st.error(f"**{error.get('type', 'error')}**: {error.get('text', '')}")
        else:
            st.markdown("""
            ### 📋 Recording Tips
            
            **Before Recording:**
            - Ensure the website is accessible
            - Plan your user journey
            - Consider different device types
            
            **During Recording:**
            - Use element inspector for complex selectors
            - Add meaningful descriptions to steps
            - Monitor console for errors
            
            **After Recording:**
            - Review captured steps
            - Analyze performance metrics
            - Generate test scenarios
            """)
    
    # Display current session steps
    if st.session_state.recording_session and st.session_state.recording_session.steps:
        st.markdown("### 📝 Recorded Steps")
        
        for step in st.session_state.recording_session.steps:
            with st.expander(f"Step {step.step_number}: {step.action_type.title()} - {step.description}"):
                col_info, col_screenshot = st.columns([1, 1])
                
                with col_info:
                    st.json({
                        "Action": step.action_type,
                        "Selector": step.selector,
                        "Value": step.value,
                        "Element Text": step.element_text,
                        "Timestamp": step.timestamp
                    })
                    
                    if step.console_errors:
                        st.warning(f"Console errors: {len(step.console_errors)}")
                
                with col_screenshot:
                    if step.screenshot_path and os.path.exists(step.screenshot_path):
                        try:
                            img = Image.open(step.screenshot_path)
                            st.image(img, caption=f"Step {step.step_number} Screenshot", use_column_width=True)
                        except Exception as e:
                            st.error(f"Cannot display screenshot: {e}")

def render_test_scenarios_tab():
    """Test scenarios management"""
    st.subheader("📋 Test Scenarios Management")
    
    # Scenario builder
    st.markdown("### ➕ Create Test Scenario")
    
    scenario_name = st.text_input("Scenario Name", placeholder="e.g., User Login Flow")
    scenario_desc = st.text_area("Description", placeholder="Describe what this scenario tests...")
    
    # Steps builder
    st.markdown("#### 🔧 Build Steps")
    
    if 'scenario_steps' not in st.session_state:
        st.session_state.scenario_steps = []
    
    # Add step form
    with st.form("add_step_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            step_action = st.selectbox("Action", ["click", "fill", "wait", "screenshot", "assert"])
        
        with col2:
            step_selector = st.text_input("CSS Selector")
        
        with col3:
            step_value = st.text_input("Value/Text")
        
        step_description = st.text_input("Step Description")
        
        if st.form_submit_button("➕ Add Step"):
            new_step = {
                "action": step_action,
                "selector": step_selector,
                "value": step_value,
                "description": step_description
            }
            st.session_state.scenario_steps.append(new_step)
            st.rerun()
    
    # Display current steps
    if st.session_state.scenario_steps:
        st.markdown("#### 📝 Current Steps")
        for i, step in enumerate(st.session_state.scenario_steps):
            col_step, col_remove = st.columns([4, 1])
            
            with col_step:
                st.code(f"{i+1}. {step['action'].upper()}: {step['selector']} - {step['description']}")
            
            with col_remove:
                if st.button("🗑️", key=f"remove_step_{i}"):
                    st.session_state.scenario_steps.pop(i)
                    st.rerun()
    
    # Save scenario
    if st.button("💾 Save Scenario", type="primary", 
                disabled=not scenario_name or not st.session_state.scenario_steps):
        save_test_scenario(scenario_name, scenario_desc, st.session_state.scenario_steps)
    
    # Load saved scenarios
    st.markdown("### 📚 Saved Scenarios")
    
    saved_scenarios = load_saved_scenarios()
    if saved_scenarios:
        for name, scenario in saved_scenarios.items():
            with st.expander(f"📋 {name}"):
                st.markdown(f"**Description:** {scenario.get('description', 'No description')}")
                st.markdown(f"**Steps:** {len(scenario.get('steps', []))}")
                
                col_load, col_delete = st.columns([1, 1])
                with col_load:
                    if st.button("📥 Load", key=f"load_{name}"):
                        st.session_state.scenario_steps = scenario['steps']
                        st.rerun()
                
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{name}"):
                        delete_scenario(name)
                        st.rerun()
    else:
        st.info("No saved scenarios yet. Create your first scenario above!")

def render_run_tests_tab():
    """Run comprehensive tests"""
    st.subheader("🚀 Run Comprehensive Tests")
    
    # Test configuration
    st.markdown("### ⚙️ Test Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_url = st.text_input("🌐 Website URL", 
                                value="https://scans.staging2.liquidpreview2.net/")
        
        devices_to_test = st.multiselect("📱 Devices to Test", 
                                       ["desktop", "mobile", "tablet"],
                                       default=["desktop", "mobile"])
    
    with col2:
        scenarios_to_run = st.multiselect("📋 Test Scenarios", 
                                        options=list(load_saved_scenarios().keys()),
                                        default=list(load_saved_scenarios().keys())[:3])
        
        include_performance = st.checkbox("📊 Include Performance Analysis", value=True)
        include_console = st.checkbox("🐛 Monitor Console Errors", value=True)
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        create_jira_ticket = st.checkbox("🎫 Auto-create Jira ticket for issues", value=True)
        max_test_time = st.slider("⏱️ Max test time per scenario (seconds)", 30, 300, 60)
        screenshot_frequency = st.selectbox("📸 Screenshot frequency", 
                                          ["On errors only", "Key steps", "All steps"],
                                          index=1)
    
    # Run tests
    if st.button("🚀 Run Comprehensive Tests", type="primary", 
                disabled=not test_url or not devices_to_test or not scenarios_to_run):
        run_comprehensive_tests(
            test_url, scenarios_to_run, devices_to_test,
            include_performance, include_console, create_jira_ticket
        )

def render_results_analysis_tab():
    """Results and analysis"""
    st.subheader("📊 Test Results & Analysis")
    
    if not st.session_state.test_results:
        st.info("No test results yet. Run some tests to see analysis here!")
        return
    
    results = st.session_state.test_results
    
    # Test summary
    st.markdown("### 📋 Test Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Total Scenarios", results['test_summary']['total_scenarios'])
    
    with col2:
        st.metric("📱 Devices Tested", len(results['test_summary']['devices_tested']))
    
    with col3:
        st.metric("🐛 Issues Found", results['test_summary']['total_issues'])
    
    with col4:
        jira_ticket = results.get('jira_ticket')
        if jira_ticket:
            st.metric("🎫 Jira Ticket", "Created")
            st.markdown(f"[View Ticket]({jira_ticket['ticket_url']})")
        else:
            st.metric("🎫 Jira Ticket", "N/A")
    
    # Device comparison
    st.markdown("### 📱 Device Comparison")
    
    device_tabs = st.tabs([f"📱 {device.title()}" for device in results['device_results'].keys()])
    
    for i, (device, device_results) in enumerate(results['device_results'].items()):
        with device_tabs[i]:
            display_device_results(device, device_results)
    
    # Issues analysis
    if results['test_summary']['total_issues'] > 0:
        st.markdown("### 🐛 Issues Analysis")
        
        all_issues = []
        for device_results in results['device_results'].values():
            all_issues.extend(device_results['issues'])
        
        # Group issues by type
        issue_types = {}
        for issue in all_issues:
            issue_type = issue['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        for issue_type, issues in issue_types.items():
            with st.expander(f"🐛 {issue_type.replace('_', ' ').title()} ({len(issues)} issues)"):
                for issue in issues:
                    severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    st.markdown(f"{severity_color.get(issue['severity'], '⚪')} **{issue['description']}**")
                    if 'location' in issue:
                        st.caption(f"Location: {issue['location']}")
                    if 'device' in issue:
                        st.caption(f"Device: {issue['device']}")
    
    # Jira ticket preview
    if jira_ticket:
        st.markdown("### 🎫 Generated Jira Ticket")
        
        st.success(f"**Ticket Created:** {jira_ticket['ticket_key']}")
        st.markdown(f"**Issues Summarized:** {jira_ticket['issues_count']}")
        
        with st.expander("📝 AI-Generated Summary"):
            st.markdown(jira_ticket['ai_summary'])
        
        st.markdown(f"[🔗 Open in Jira]({jira_ticket['ticket_url']})")

def display_device_results(device: str, device_results: Dict):
    """Display results for a specific device"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("✅ Sessions Completed", len(device_results['sessions']))
        st.metric("🐛 Issues Found", len(device_results['issues']))
    
    with col2:
        st.metric("⚠️ Console Errors", len(device_results['console_errors']))
        # Add performance metrics if available
        if device_results.get('performance_metrics'):
            perf = device_results['performance_metrics']
            if 'loadTime' in perf:
                st.metric("⏱️ Avg Load Time", f"{perf['loadTime']:.2f}ms")
    
    # Session details
    if device_results['sessions']:
        st.markdown("#### 📝 Session Details")
        for i, session in enumerate(device_results['sessions']):
            with st.expander(f"Session {i+1} - {len(session.steps)} steps"):
                st.json({
                    "Device": session.device_type,
                    "Browser": session.browser_type,
                    "Steps": len(session.steps),
                    "Console Errors": len(session.console_errors),
                    "Status": session.status,
                    "Duration": f"{session.start_time} - {session.end_time}"
                })

# Helper functions for session management
def start_recording_session(url: str, device_type: str, browser_type: str):
    """Start a new recording session"""
    try:
        if not st.session_state.functional_agent:
            st.session_state.functional_agent = FunctionalTestingAgent()
        
        # This would need to be implemented with async support in Streamlit
        st.info("🎬 Recording session starting... (This is a demo - full async support needed)")
        
        # For demo purposes, create a mock session
        from enhanced_functional_testing import TestSession
        session = TestSession(
            session_id=f"demo_{int(time.time())}",
            url=url,
            device_type=device_type,
            browser_type=browser_type,
            viewport_size={"width": 1920, "height": 1080},
            steps=[],
            console_errors=[],
            performance_summary={},
            start_time=datetime.now().isoformat()
        )
        
        st.session_state.recording_session = session
        st.success("🟢 Recording session started!")
        
    except Exception as e:
        st.error(f"Failed to start recording: {e}")

def stop_recording_session():
    """Stop the current recording session"""
    if st.session_state.recording_session:
        st.session_state.recording_session.end_time = datetime.now().isoformat()
        st.session_state.recording_session.status = "completed"
        st.success("⏹️ Recording session stopped!")
        
        # Clear the active session
        st.session_state.recording_session = None

def save_test_scenario(name: str, description: str, steps: list):
    """Save a test scenario"""
    scenarios_file = Path("test_scenarios.json")
    
    scenarios = {}
    if scenarios_file.exists():
        try:
            with open(scenarios_file, 'r') as f:
                scenarios = json.load(f)
        except:
            pass
    
    scenarios[name] = {
        "description": description,
        "steps": steps,
        "created_at": datetime.now().isoformat()
    }
    
    with open(scenarios_file, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    st.success(f"✅ Scenario '{name}' saved!")
    st.session_state.scenario_steps = []  # Clear current steps

def load_saved_scenarios() -> Dict:
    """Load saved test scenarios"""
    scenarios_file = Path("test_scenarios.json")
    
    if scenarios_file.exists():
        try:
            with open(scenarios_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    return {}

def delete_scenario(name: str):
    """Delete a saved scenario"""
    scenarios = load_saved_scenarios()
    if name in scenarios:
        del scenarios[name]
        
        with open("test_scenarios.json", 'w') as f:
            json.dump(scenarios, f, indent=2)
        
        st.success(f"✅ Scenario '{name}' deleted!")

def run_comprehensive_tests(url: str, scenarios: list, devices: list, 
                           include_performance: bool, include_console: bool, 
                           create_jira_ticket: bool):
    """Run comprehensive tests"""
    with st.spinner("🚀 Running comprehensive tests..."):
        # This is a demo implementation
        # In reality, this would use the FunctionalTestingAgent
        
        # Mock results for demo
        mock_results = {
            "test_summary": {
                "url": url,
                "total_scenarios": len(scenarios),
                "devices_tested": devices,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_issues": 3
            },
            "device_results": {},
            "jira_ticket": {
                "ticket_key": "QA-123",
                "ticket_url": "https://liquidthought.atlassian.net/browse/QA-123",
                "ai_summary": "Automated testing found 3 issues across desktop and mobile devices.",
                "issues_count": 3
            } if create_jira_ticket else None
        }
        
        for device in devices:
            mock_results["device_results"][device] = {
                "device_type": device,
                "sessions": [],
                "issues": [
                    {
                        "type": "javascript_error",
                        "description": f"Console error on {device}",
                        "severity": "medium",
                        "device": device
                    }
                ],
                "performance_metrics": {"loadTime": 2500.0},
                "console_errors": [{"type": "error", "text": "Sample error"}]
            }
        
        st.session_state.test_results = mock_results
        st.success("✅ Tests completed! Check the Results & Analysis tab.")


# Helper functions for interactive recording
def inspect_element(selector: str):
    """Inspect element and show details"""
    if 'recorder' in st.session_state and st.session_state.recorder:
        try:
            element_info = {
                "selector": selector,
                "tagName": "div",  # Mock data
                "textContent": "Sample element text",
                "attributes": {"class": "sample-class", "id": "sample-id"}
            }
            st.code(json.dumps(element_info, indent=2), language="json")
            return element_info
        except Exception as e:
            st.error(f"Failed to inspect element: {e}")
    else:
        st.warning("No active recording session")
    return None


def record_manual_step(action_type: str, selector: str, value: str, description: str):
    """Record a manual test step"""
    if 'current_session' not in st.session_state:
        st.session_state.current_session = TestSession(
            session_id="manual_session",
            url="",
            device_type="desktop",
            browser_type="chromium",
            steps=[],
            console_errors=[],
            performance_metrics={},
            screenshots=[]
        )
    
    # Create new test step
    step = TestStep(
        step_id=f"manual_{len(st.session_state.current_session.steps)}",
        action_type=action_type,
        selector=selector,
        value=value,
        screenshot_path="",
        description=description,
        timestamp=datetime.now(),
        element_info={}
    )
    
    st.session_state.current_session.steps.append(step)
    st.success(f"✅ Recorded: {description}")


def refresh_console_errors():
    """Refresh and display console errors"""
    if 'current_session' in st.session_state and st.session_state.current_session:
        # Mock console errors for demo
        console_errors = [
            {"type": "error", "text": "Sample JavaScript error", "timestamp": datetime.now().isoformat()},
            {"type": "warning", "text": "Deprecated API usage", "timestamp": datetime.now().isoformat()}
        ]
        
        st.session_state.current_session.console_errors = console_errors
        
        if console_errors:
            st.error(f"🐛 Found {len(console_errors)} console errors")
            for error in console_errors:
                with st.expander(f"{error['type'].upper()}: {error['text'][:50]}..."):
                    st.code(error['text'], language="javascript")
        else:
            st.success("✅ No console errors found")
    else:
        st.warning("No active session to check for errors")


# Export the main function
__all__ = ['render_functional_testing_ui']
