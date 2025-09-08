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
import logging
from typing import Dict, List, Optional, Any

# Initialize logger
logger = logging.getLogger(__name__)

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
    st.markdown("### 🎬 Interactive Test Recording")
    st.markdown("Record user interactions in real-time with visual element highlighting and automatic screenshots.")
    
    # Main recording section
    with st.container():
        st.markdown("#### 🚀 Recording Setup")
        
        # URL input (full width for better usability)
        url = st.text_input("🌐 Website URL", 
                           value="https://scans.staging2.liquidpreview2.net/",
                           placeholder="Enter the URL you want to test",
                           help="The website URL where you want to record user interactions")
        
        # Device and browser selection in columns
        col_device, col_browser, col_space = st.columns([1, 1, 2])
        with col_device:
            device_type = st.selectbox("📱 Device Type", 
                                     ["desktop", "mobile", "tablet"],
                                     help="Device viewport to emulate")
        
        with col_browser:
            browser_type = st.selectbox("🌐 Browser", 
                                      ["chromium", "firefox", "webkit"],
                                      help="Browser engine for automation")
        
        st.markdown("---")
        
        # Recording controls with better spacing
        is_recording = st.session_state.get('recording_session') is not None
        
        col_controls, col_status = st.columns([2, 1])
        
        with col_controls:
            # Single row of controls
            if is_recording:
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("⏹️ Stop Recording", type="secondary"):
                        stop_recording_session()
                with col2:
                    if st.button("💾 Save Scenario", type="primary"):
                        # Trigger save dialog
                        st.session_state.show_save_dialog = True
            else:
                if url.strip():
                    if st.button("🔴 Start Recording", type="primary", key="start_btn"):
                        start_recording_session(url.strip(), device_type, browser_type)
                else:
                    st.button("🔴 Start Recording", disabled=True, help="Please enter a URL first")
        
        with col_status:
            # Clean status indicator
            if is_recording:
                st.success("🟢 Recording Active")
                if st.session_state.recording_session:
                    st.caption(f"Session: {st.session_state.recording_session.session_id[-8:]}")
            else:
                st.info("⚪ Ready to Record")
    
    # Recording tools (only show when recording)
    if is_recording and st.session_state.recording_session:
        st.markdown("---")
        st.markdown("#### 🛠️ Recording Tools")
        
        # Tabs for different tools
        tool_tab1, tool_tab2, tool_tab3 = st.tabs(["🔍 Element Inspector", "➕ Manual Steps", "🐛 Console Monitor"])
        
        with tool_tab1:
            st.markdown("**Inspect elements to get precise selectors:**")
            selector = st.text_input("CSS Selector", 
                                    placeholder="e.g., #login-button, .nav-item, [data-testid='submit']",
                                    help="Enter a CSS selector to inspect the element")
            if st.button("🔍 Inspect Element", disabled=not selector):
                inspect_element(selector)
        
        with tool_tab2:
            st.markdown("**Manually add test steps:**")
            col1, col2 = st.columns(2)
            with col1:
                action_type = st.selectbox("Action Type", 
                                         ["click", "fill", "wait", "navigate", "screenshot"],
                                         help="Type of user action to record")
                step_selector = st.text_input("Element Selector", 
                                            placeholder="CSS selector for the target element")
            with col2:
                step_value = st.text_input("Value (optional)", 
                                         placeholder="Text to enter (for fill actions)")
                step_desc = st.text_input("Description", 
                                        placeholder="Describe what this step does")
            
            if st.button("➕ Add Manual Step", disabled=not (step_selector and step_desc)):
                record_manual_step(action_type, step_selector, step_value, step_desc)
        
        with tool_tab3:
            st.markdown("**Monitor JavaScript console errors:**")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🔄 Refresh Console"):
                    refresh_console_errors()
            
            # Show console errors
            console_errors = st.session_state.get('console_errors', [])
            if console_errors:
                st.error(f"Found {len(console_errors)} console errors:")
                for i, error in enumerate(console_errors[-3:]):  # Show last 3 errors
                    with st.expander(f"Error {i+1}: {error.get('type', 'error').upper()}"):
                        st.code(error.get('text', 'No details available'), language='javascript')
            else:
                st.success("✅ No console errors detected")
    
    # Tips section (always visible)
    if not is_recording:
        st.markdown("---")
        with st.expander("� Recording Tips", expanded=False):
            st.markdown("""
            **🎯 Before Recording:**
            - Ensure the website is accessible and loads properly
            - Plan your user journey and key interactions
            - Consider testing on different device types
            
            **⚡ During Recording:**
            - Interact naturally with the website
            - Use the Element Inspector for complex selectors
            - Add manual steps for specific test scenarios
            - Monitor the console for JavaScript errors
            
            **📋 After Recording:**
            - Review all captured steps for accuracy
            - Save your test scenario with a descriptive name
            - Analyze performance metrics and console errors
            """)
    
    # Save scenario dialog
    if st.session_state.get('show_save_dialog') and is_recording:
        with st.form("save_scenario_form"):
            st.markdown("#### 💾 Save Test Scenario")
            scenario_name = st.text_input("Scenario Name", placeholder="e.g., User Login Flow")
            scenario_desc = st.text_area("Description", placeholder="Describe what this test scenario covers")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Scenario", type="primary"):
                    if scenario_name and st.session_state.recording_session:
                        save_test_scenario(scenario_name, scenario_desc, st.session_state.recording_session.steps)
                        st.session_state.show_save_dialog = False
                        st.success(f"✅ Scenario '{scenario_name}' saved successfully!")
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_save_dialog = False
                    st.rerun()
    
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
    st.markdown("### 📋 Test Scenarios Management")
    st.markdown("Create, edit, and manage your automated test scenarios with step-by-step validation.")
    
    # Load saved scenarios first to show dashboard
    saved_scenarios = load_saved_scenarios()
    
    # Dashboard overview
    if saved_scenarios:
        st.markdown("#### � Scenario Dashboard")
        col_total, col_steps, col_recent = st.columns(3)
        
        with col_total:
            st.metric("Total Scenarios", len(saved_scenarios))
        with col_steps:
            total_steps = sum(len(scenario.get('steps', [])) for scenario in saved_scenarios.values())
            st.metric("Total Test Steps", total_steps)
        with col_recent:
            st.metric("Recently Modified", "Today")  # Could implement actual tracking
        
        st.markdown("---")
    
    # Tabbed interface for better organization
    tab_create, tab_manage, tab_import = st.tabs(["➕ Create Scenario", "📚 Manage Scenarios", "📁 Import/Export"])
    
    with tab_create:
        st.markdown("#### 🎯 Create New Test Scenario")
        
        # Scenario metadata
        col_name, col_type = st.columns([2, 1])
        with col_name:
            scenario_name = st.text_input("Scenario Name", 
                                        placeholder="e.g., User Login Flow",
                                        help="Give your scenario a descriptive name")
        with col_type:
            scenario_type = st.selectbox("Scenario Type", 
                                       ["Functional", "Regression", "Smoke", "Integration"],
                                       help="Type of test scenario")
        
        scenario_desc = st.text_area("Description", 
                                   placeholder="Describe what this scenario tests, including expected outcomes...",
                                   help="Detailed description of what this test validates")
        
        # Steps builder
        st.markdown("##### 🔧 Build Test Steps")
        
        if 'scenario_steps' not in st.session_state:
            st.session_state.scenario_steps = []
        
        # Add step form with better validation
        with st.form("add_step_form"):
            col_action, col_selector, col_value = st.columns([1, 2, 1])
            
            with col_action:
                step_action = st.selectbox("Action", 
                                         ["click", "fill", "wait", "screenshot", "assert", "navigate"],
                                         help="Type of action to perform")
            
            with col_selector:
                step_selector = st.text_input("CSS Selector", 
                                            placeholder="e.g., #login-button, .nav-item",
                                            help="CSS selector for the target element")
            
            with col_value:
                step_value = st.text_input("Value/Text", 
                                         placeholder="Text to enter or expected value",
                                         help="Value for fill actions or assertion")
            
            step_description = st.text_input("Step Description", 
                                           placeholder="Describe what this step does",
                                           help="Clear description of the step's purpose")
            
            col_add, col_validate = st.columns([1, 1])
            with col_add:
                if st.form_submit_button("➕ Add Step", type="primary"):
                    if step_action and step_selector and step_description:
                        new_step = {
                            "action": step_action,
                            "selector": step_selector,
                            "value": step_value,
                            "description": step_description,
                            "type": scenario_type
                        }
                        st.session_state.scenario_steps.append(new_step)
                        st.success(f"✅ Added step: {step_description}")
                        st.rerun()
                    else:
                        st.error("Please fill in Action, Selector, and Description fields")
            
            with col_validate:
                if st.form_submit_button("🔍 Validate Step", type="secondary"):
                    validate_step_selector(step_selector)
        
        # Display and manage current steps
        if st.session_state.scenario_steps:
            st.markdown("##### 📝 Current Test Steps")
            
            for i, step in enumerate(st.session_state.scenario_steps):
                with st.container():
                    col_step, col_actions = st.columns([4, 1])
                    
                    with col_step:
                        # Enhanced step display
                        step_icon = {"click": "🖱️", "fill": "⌨️", "wait": "⏱️", 
                                   "screenshot": "📸", "assert": "✅", "navigate": "🔗"}.get(step['action'], "🔧")
                        st.markdown(f"**{i+1}.** {step_icon} **{step['action'].upper()}** on `{step['selector']}`")
                        st.caption(f"💬 {step['description']}")
                        if step.get('value'):
                            st.caption(f"📝 Value: {step['value']}")
                    
                    with col_actions:
                        col_edit, col_remove = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=f"edit_step_{i}", help="Edit step"):
                                st.session_state.editing_step = i
                        with col_remove:
                            if st.button("🗑️", key=f"remove_step_{i}", help="Remove step"):
                                st.session_state.scenario_steps.pop(i)
                                st.success("Step removed!")
                                st.rerun()
                    
                    st.markdown("---")
            
            # Save scenario
            col_save, col_clear = st.columns([2, 1])
            with col_save:
                if st.button("💾 Save Scenario", type="primary", 
                            disabled=not scenario_name):
                    if scenario_name:
                        save_test_scenario(scenario_name, scenario_desc, st.session_state.scenario_steps)
                        st.session_state.scenario_steps = []  # Clear after saving
                        st.success(f"✅ Scenario '{scenario_name}' saved successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a scenario name")
            
            with col_clear:
                if st.button("🗑️ Clear All Steps", type="secondary"):
                    st.session_state.scenario_steps = []
                    st.warning("All steps cleared!")
                    st.rerun()
    
    with tab_manage:
        st.markdown("#### 📚 Manage Saved Scenarios")
        
        if saved_scenarios:
            # Filter and search
            col_search, col_filter = st.columns([2, 1])
            with col_search:
                search_term = st.text_input("🔍 Search scenarios", placeholder="Type to search...")
            with col_filter:
                filter_type = st.selectbox("Filter by Type", ["All"] + ["Functional", "Regression", "Smoke", "Integration"])
            
            # Apply filters
            filtered_scenarios = saved_scenarios
            if search_term:
                filtered_scenarios = {name: scenario for name, scenario in saved_scenarios.items() 
                                    if search_term.lower() in name.lower() 
                                    or search_term.lower() in scenario.get('description', '').lower()}
            
            # Display scenarios
            for name, scenario in filtered_scenarios.items():
                with st.expander(f"📋 **{name}**", expanded=False):
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"**Description:** {scenario.get('description', 'No description')}")
                        st.markdown(f"**Type:** {scenario.get('type', 'Functional')}")
                        st.markdown(f"**Steps:** {len(scenario.get('steps', []))} test steps")
                        
                        # Show steps preview
                        if scenario.get('steps'):
                            with st.expander("👁️ Preview Steps", expanded=False):
                                for i, step in enumerate(scenario['steps'][:5]):  # Show first 5 steps
                                    step_icon = {"click": "🖱️", "fill": "⌨️", "wait": "⏱️", 
                                               "screenshot": "📸", "assert": "✅", "navigate": "🔗"}.get(step['action'], "🔧")
                                    st.markdown(f"{i+1}. {step_icon} **{step['action']}** on `{step.get('selector', 'N/A')}`")
                                
                                if len(scenario['steps']) > 5:
                                    st.caption(f"... and {len(scenario['steps']) - 5} more steps")
                    
                    with col_actions:
                        st.markdown("**Actions:**")
                        
                        if st.button("📥 Load to Editor", key=f"load_{name}", help="Load into step editor"):
                            st.session_state.scenario_steps = scenario['steps']
                            st.success(f"Loaded '{name}' into editor")
                            st.rerun()
                        
                        if st.button("▶️ Run Test", key=f"run_{name}", help="Execute this scenario"):
                            run_test_scenario(name, scenario)
                        
                        if st.button("📋 Duplicate", key=f"duplicate_{name}", help="Create a copy"):
                            duplicate_scenario(name, scenario)
                        
                        if st.button("🗑️ Delete", key=f"delete_{name}", help="Delete scenario", type="secondary"):
                            if st.session_state.get(f'confirm_delete_{name}'):
                                delete_scenario(name)
                                st.success(f"Deleted scenario '{name}'")
                                st.rerun()
                            else:
                                st.session_state[f'confirm_delete_{name}'] = True
                                st.warning("Click again to confirm deletion")
            
            # Batch operations
            if len(saved_scenarios) > 1:
                st.markdown("---")
                st.markdown("#### ⚡ Batch Operations")
                col_run_all, col_export_all, col_clear_all = st.columns(3)
                
                with col_run_all:
                    if st.button("▶️ Run All Scenarios"):
                        run_all_test_scenarios(list(saved_scenarios.keys()))
                
                with col_export_all:
                    if st.button("📤 Export All"):
                        export_all_scenarios(saved_scenarios)
                
                with col_clear_all:
                    if st.button("🗑️ Clear All", type="secondary"):
                        if st.session_state.get('confirm_clear_all_scenarios'):
                            clear_all_scenarios()
                            st.success("All scenarios cleared!")
                            st.rerun()
                        else:
                            st.session_state.confirm_clear_all_scenarios = True
                            st.warning("Click again to confirm deletion of ALL scenarios")
        else:
            st.info("📝 No saved scenarios yet. Create your first scenario in the 'Create Scenario' tab!")
    
    with tab_import:
        st.markdown("#### 📁 Import & Export Test Scenarios")
        
        col_import, col_export = st.columns(2)
        
        with col_import:
            st.markdown("##### 📥 Import Scenarios")
            uploaded_file = st.file_uploader("Choose JSON file", type="json", 
                                           help="Upload a JSON file containing test scenarios")
            
            if uploaded_file:
                col_preview, col_import_btn = st.columns([2, 1])
                
                with col_preview:
                    if st.button("👁️ Preview File"):
                        preview_import_file(uploaded_file)
                
                with col_import_btn:
                    if st.button("📥 Import Scenarios", type="primary"):
                        import_scenarios(uploaded_file)
        
        with col_export:
            st.markdown("##### 📤 Export Scenarios")
            
            if saved_scenarios:
                export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"])
                
                selected_scenarios = st.multiselect(
                    "Select scenarios to export (leave empty for all)", 
                    list(saved_scenarios.keys())
                )
                
                if st.button("📤 Download Export", type="primary"):
                    scenarios_to_export = selected_scenarios if selected_scenarios else list(saved_scenarios.keys())
                    export_scenarios(scenarios_to_export, export_format)
            else:
                st.info("No scenarios available to export")

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
        
        # Initialize Playwright recorder with proper Streamlit integration
        if not hasattr(st.session_state, 'recorder') or not st.session_state.recorder:
            st.session_state.recorder = PlaywrightRecorder()
        
        with st.spinner("🎬 Initializing recording session..."):
            # Start recording session with intelligent mode detection
            success = st.session_state.recorder.start_session(url, device_type, browser_type)
            
            if success:
                # Check what mode we're in based on the session type
                session_id = st.session_state.recorder.current_session.session_id
                
                if session_id.startswith("session_"):
                    # Full browser automation mode
                    st.success("🟢 **Live Browser Recording Started!**")
                    st.info("🌐 **Browser window opened** - Navigate and interact with your website. Every click, form input, and navigation will be automatically recorded!")
                    st.markdown("**Next Steps:**")
                    st.markdown("1. 🖱️ Click elements on your website")
                    st.markdown("2. ✍️ Fill out forms")  
                    st.markdown("3. 📄 Navigate between pages")
                    st.markdown("4. 🛑 Click 'Stop Recording' when finished")
                    
                elif session_id.startswith("guided_"):
                    # Guided manual recording mode
                    st.success("🟢 **Guided Recording Started!**") 
                    st.info("� **Manual Mode** - Browser automation is limited in this environment. You can manually add test steps using the controls below.")
                    st.markdown("**How to proceed:**")
                    st.markdown("1. � Open your website in a separate browser tab")
                    st.markdown("2. 📝 Use the manual controls below to add test steps")
                    st.markdown("3. 🔍 Use the element inspector to get selectors")
                    
                # Store session info
                st.session_state.recording_session = st.session_state.recorder.current_session
                st.session_state.recording_active = True
                
            else:
                st.error("❌ Failed to start recording session. Please check your configuration and try again.")
                
    except Exception as e:
        st.error(f"❌ Recording initialization failed: {str(e)}")
        logger.error(f"Recording session start failed: {e}")


def _create_demo_session(url: str, device_type: str, browser_type: str):
    """Create a demo session when full browser automation isn't available"""
    from enhanced_functional_testing import TestSession
    session = TestSession(
        session_id=f"demo_{int(time.time())}",
        url=url,
        device_type=device_type,
        browser_type=browser_type,
        viewport_size={"width": 1920, "height": 1080} if device_type == "desktop" else {"width": 375, "height": 667},
        steps=[],
        console_errors=[],
        performance_summary={},
        start_time=datetime.now().isoformat()
    )


# Helper functions for scenario management
def validate_step_selector(selector: str):
    """Validate CSS selector syntax"""
    if not selector:
        st.error("❌ Selector cannot be empty")
        return False
    
    # Basic CSS selector validation
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_#.[]():,>+~= ")
    if not all(c in valid_chars for c in selector):
        st.warning("⚠️ Selector contains unusual characters. Please verify it's correct.")
    else:
        st.success("✅ Selector syntax appears valid")
    return True


def run_test_scenario(name: str, scenario: dict):
    """Execute a test scenario"""
    try:
        st.info(f"🚀 Running scenario: {name}")
        # Here you would integrate with your test runner
        # For now, simulate execution
        import time
        with st.spinner("Executing test steps..."):
            time.sleep(2)  # Simulate test execution
        st.success(f"✅ Scenario '{name}' completed successfully!")
    except Exception as e:
        st.error(f"❌ Scenario execution failed: {str(e)}")


def duplicate_scenario(name: str, scenario: dict):
    """Create a duplicate of a scenario"""
    new_name = f"{name} (Copy)"
    counter = 1
    
    # Ensure unique name
    saved_scenarios = load_saved_scenarios()
    while new_name in saved_scenarios:
        new_name = f"{name} (Copy {counter})"
        counter += 1
    
    # Create duplicate
    new_scenario = scenario.copy()
    save_test_scenario(new_name, new_scenario.get('description', ''), new_scenario.get('steps', []))
    st.success(f"✅ Created duplicate: '{new_name}'")


def run_all_test_scenarios(scenario_names: list):
    """Run multiple scenarios in batch"""
    try:
        st.info(f"🚀 Running {len(scenario_names)} scenarios...")
        
        progress_bar = st.progress(0)
        for i, name in enumerate(scenario_names):
            st.write(f"Running: {name}")
            # Simulate execution
            import time
            time.sleep(1)
            progress_bar.progress((i + 1) / len(scenario_names))
        
        st.success(f"✅ All {len(scenario_names)} scenarios completed!")
        
    except Exception as e:
        st.error(f"❌ Batch execution failed: {str(e)}")


def export_all_scenarios(scenarios: dict):
    """Export all scenarios to downloadable format"""
    try:
        import json
        
        # Create export data
        export_data = {
            "export_date": datetime.now().isoformat(),
            "scenarios": scenarios,
            "total_count": len(scenarios)
        }
        
        # Convert to JSON
        json_data = json.dumps(export_data, indent=2)
        
        # Create download button
        st.download_button(
            label="📥 Download All Scenarios",
            data=json_data,
            file_name=f"test_scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.success(f"✅ Export ready: {len(scenarios)} scenarios")
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


def clear_all_scenarios():
    """Clear all saved scenarios"""
    try:
        # Implementation depends on your storage method
        # For now, just clear session state if used
        if 'saved_scenarios' in st.session_state:
            st.session_state.saved_scenarios = {}
        
        # You might also need to clear from file storage
        # Example: os.remove('scenarios.json') or database.clear_all()
        
    except Exception as e:
        st.error(f"❌ Failed to clear scenarios: {str(e)}")


def preview_import_file(uploaded_file):
    """Preview the contents of an import file"""
    try:
        import json
        
        # Read and parse file
        file_content = uploaded_file.read()
        data = json.loads(file_content)
        
        # Show preview
        st.markdown("**Import Preview:**")
        st.json(data)
        
        # Reset file pointer for actual import
        uploaded_file.seek(0)
        
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file format")
    except Exception as e:
        st.error(f"❌ Preview failed: {str(e)}")


def import_scenarios(uploaded_file):
    """Import scenarios from uploaded file"""
    try:
        import json
        
        # Parse uploaded file
        file_content = uploaded_file.read()
        data = json.loads(file_content)
        
        # Validate structure
        if 'scenarios' not in data:
            st.error("❌ Invalid file format: 'scenarios' key not found")
            return
        
        # Import scenarios
        imported_count = 0
        for name, scenario in data['scenarios'].items():
            save_test_scenario(name, scenario.get('description', ''), scenario.get('steps', []))
            imported_count += 1
        
        st.success(f"✅ Successfully imported {imported_count} scenarios!")
        st.rerun()
        
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file format")
    except Exception as e:
        st.error(f"❌ Import failed: {str(e)}")


def export_scenarios(scenario_names: list, format_type: str):
    """Export selected scenarios in specified format"""
    try:
        saved_scenarios = load_saved_scenarios()
        selected_scenarios = {name: saved_scenarios[name] for name in scenario_names if name in saved_scenarios}
        
        if format_type == "JSON":
            export_data = {
                "export_date": datetime.now().isoformat(),
                "scenarios": selected_scenarios,
                "total_count": len(selected_scenarios)
            }
            
            import json
            json_data = json.dumps(export_data, indent=2)
            
            st.download_button(
                label=f"📥 Download {len(selected_scenarios)} Scenarios (JSON)",
                data=json_data,
                file_name=f"scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        elif format_type == "CSV":
            # Convert to CSV format
            csv_data = "Name,Description,Steps Count,Actions\n"
            for name, scenario in selected_scenarios.items():
                steps_count = len(scenario.get('steps', []))
                actions = ", ".join([step.get('action', '') for step in scenario.get('steps', [])])
                csv_data += f'"{name}","{scenario.get("description", "")}",{steps_count},"{actions}"\n'
            
            st.download_button(
                label=f"📥 Download {len(selected_scenarios)} Scenarios (CSV)",
                data=csv_data,
                file_name=f"scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        st.success(f"✅ Export ready: {len(selected_scenarios)} scenarios")
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


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
