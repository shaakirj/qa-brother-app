"""
monster2.py - Unified QA AI Agent with Visual Real-Time Test Execution
Version: QA Brother
"""

import streamlit as st
import os
import json
import threading
from dotenv import load_dotenv
import time
import logging
import traceback
from datetime import datetime
from urllib.parse import urljoin
from PyPDF2 import PdfReader
import queue as _queue
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*", category=UserWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

# Presets storage
PRESETS_FILE = os.path.join(os.path.dirname(__file__), ".qa_brother_projects.json")

def _load_presets():
    try:
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load presets: {e}")
    return {}

def _save_presets(presets: dict):
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save presets: {e}")

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Attempt to import the necessary processor from design8
try:
    from design8 import DesignQAProcessor, IS_CLOUD_DEPLOYMENT, BROWSER_AUTOMATION_AVAILABLE
    DESIGN8_AVAILABLE = True
    
    # Create a simple fallback functional agent
    class FunctionalQAAgent:
        def run_full_test_cycle(self, *args, **kwargs):
            return {"error": "Functional QA not fully implemented yet"}
        def execute_test_suite(self, *args, **kwargs):
            return []
        def save_artifacts(self, *args, **kwargs):
            return {}
        def log_failed_tests_to_jira(self, *args, **kwargs):
            return []
        def get_jira_acceptance_criteria(self, *args, **kwargs):
            return ""
        def get_ux_text_from_figma_url(self, *args, **kwargs):
            return ""
        def generate_user_stories_from_ux(self, *args, **kwargs):
            return {}
        def generate_test_cases_from_ai(self, *args, **kwargs):
            return []
            
except ImportError as e:
    st.error(f"Fatal Error: Could not import 'design8.py'. Please ensure the file exists and is correct. Details: {e}")
    DESIGN8_AVAILABLE = False
    IS_CLOUD_DEPLOYMENT = True
    BROWSER_AUTOMATION_AVAILABLE = False
    
    # Define a fallback class so the app doesn't crash immediately
    class DesignQAProcessor:
        def process_qa_request(self, *args, **kwargs):
            return {"success": False, "error": "DesignQAProcessor is not available due to import failure."}
        def cleanup(self):
            pass
    class FunctionalQAAgent:
        def run_full_test_cycle(self, *args, **kwargs):
            return {"error": "Functional QA not available due to import failure"}
        def execute_test_suite(self, *args, **kwargs):
            return []
        def save_artifacts(self, *args, **kwargs):
            return {}
        def log_failed_tests_to_jira(self, *args, **kwargs):
            return []
        def get_jira_acceptance_criteria(self, *args, **kwargs):
            return ""
        def get_ux_text_from_figma_url(self, *args, **kwargs):
            return ""
        def generate_user_stories_from_ux(self, *args, **kwargs):
            return {}
        def generate_test_cases_from_ai(self, *args, **kwargs):
            return []

class VisualTestExecutor:
    """Manages the visual display of test execution steps in a stepper format."""
    
    def __init__(self, container):
        self.container = container
        self.steps = []
        self.start_time = None
        
    def initialize_steps(self):
        """Initializes the steps for the design QA test."""
        self.start_time = datetime.now()
        self.steps = [
            {"name": "1. Parse & Validate Inputs", "status": "pending", "icon": "📝", "details": "Waiting to start..."},
            {"name": "2. Retrieve Figma Design", "status": "pending", "icon": "🎨", "details": "Waiting for previous step..."},
            {"name": "3. Capture Web Page Screenshot", "status": "pending", "icon": "📸", "details": "Waiting for previous step..."},
            {"name": "4. Compare Design vs. Web", "status": "pending", "icon": "🔍", "details": "Waiting for previous step..."},
            {"name": "5. Run Functional Validations", "status": "pending", "icon": "⚙️", "details": "Waiting for previous step..."},
            {"name": "6. Create Jira Tickets", "status": "pending", "icon": "🎟️", "details": "Waiting for previous step..."},
            {"name": "7. Generate Final Report", "status": "pending", "icon": "📊", "details": "Waiting for previous step..."}
        ]
        self.update_display()

    def update_step(self, step_index, status, details=""):
        """Update the status and details of a specific step by its index."""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = status
            self.steps[step_index]["details"] = details
            
            if status == "running":
                # Mark all subsequent steps as pending when a step starts running
                for i in range(step_index + 1, len(self.steps)):
                    if self.steps[i]["status"] not in ["success", "error"]:
                        self.steps[i]["status"] = "pending"
                        self.steps[i]["details"] = "Waiting for previous step..."
        self.update_display()

    def update_display(self):
        """Renders the current state of all steps using expanders."""
        with self.container.container():
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            st.caption(f"Total elapsed time: {elapsed:.1f}s")
            
            for i, step in enumerate(self.steps):
                is_running = step["status"] == "running"
                is_expanded = is_running or (step["status"] == "error")

                with st.expander(f"**{step['icon']} {step['name']}** - `{step['status'].upper()}`", expanded=is_expanded):
                    st.code(step['details'], language="bash")

    def find_step_index(self, step_name_fragment):
        """Finds a step index by a fragment of its name."""
        for i, step in enumerate(self.steps):
            if step_name_fragment.lower() in step["name"].lower():
                return i
        # Fallback - if exact match not found, try partial matching
        for i, step in enumerate(self.steps):
            step_words = step["name"].lower().split()
            fragment_words = step_name_fragment.lower().split()
            if any(word in step_words for word in fragment_words):
                return i
        return -1

class MonsterQAAgent:
    """Unified QA Agent that correctly uses the DesignQAProcessor."""
    def __init__(self):
        self.visual_executor = None
        if DESIGN8_AVAILABLE:
            try:
                self.processor = DesignQAProcessor()
                self.is_initialized = True
                logger.info("MonsterQAAgent initialized successfully.")
            except Exception as e:
                self.processor = None
                self.is_initialized = False
                logger.error(f"Failed to initialize DesignQAProcessor: {e}", exc_info=True)
        else:
            self.processor = DesignQAProcessor() # Fallback instance
            self.is_initialized = False

    def run_design_qa_with_visual(self, figma_url, web_url, jira_assignee=None, similarity_threshold=0.95, mobile_device=None, full_page=True, overlay_grid=False):
        """
        Runs the design QA process, updating the stepper UI at each stage.
        """
        if not self.visual_executor or not self.processor:
            return {"success": False, "error": "Agent or Visual Executor not initialized."}

        self.visual_executor.initialize_steps()
        
        # This function now returns live feedback to the UI
        results = self.processor.process_qa_request(
            figma_url, web_url, jira_assignee, similarity_threshold, 
            mobile_device=mobile_device,
            full_page=full_page,
            overlay_grid=overlay_grid,
            live_feedback_callback=self.visual_executor.update_step,
            step_finder=self.visual_executor.find_step_index
        )

        # Final update to the report step
        report_idx = self.visual_executor.find_step_index("Generate Final Report")
        if results.get('success'):
            self.visual_executor.update_step(report_idx, "success", "All tasks completed successfully.")
        else:
            error_message = results.get('error', 'An unknown error occurred.')
            self.visual_executor.update_step(report_idx, "error", f"Process failed: {error_message}")

        return results

    def run_fluid_breakpoint_test(self, url, start_width, end_width, steps, frame_duration):
        """
        Runs the fluid breakpoint test by calling the new method in the Chrome driver.
        """
        if not self.processor or not hasattr(self.processor.chrome_driver, 'capture_fluid_breakpoint_animation'):
            logger.error("Fluid breakpoint test called, but the required method is not available.")
            return None
        
        try:
            gif_path = self.processor.chrome_driver.capture_fluid_breakpoint_animation(
                url, start_width, end_width, steps, frame_duration
            )
            return gif_path
        except Exception as e:
            logger.error(f"An error occurred during the fluid breakpoint test run: {e}", exc_info=True)
            return None

    def cleanup(self):
        """Cleans up resources used by the agent."""
        if hasattr(self, 'processor') and self.processor:
            try:
                self.processor.cleanup()
                logger.info("QA Agent resources cleaned up successfully.")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

def render_design_qa_tab(agent):
    """Renders the UI for the Design QA feature."""
    st.header("Design QA Testing")
    st.markdown("Compare a Figma design with its live web implementation across different devices.")
    
    # DEBUG SECTION - Remove after fixing cloud deployment
    with st.expander("🔍 API Keys Configuration Debug", expanded=False):
        st.markdown("### OpenAI API Key Check")
        
        # Check OpenAI API key in different locations
        openai_found = False
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            token = st.secrets['OPENAI_API_KEY']
            st.success(f"✅ OpenAI key in top-level secrets (length: {len(token)})")
            openai_found = True
        elif hasattr(st, 'secrets') and 'api_keys' in st.secrets and 'openai_api_key' in st.secrets['api_keys']:
            token = st.secrets['api_keys']['openai_api_key']
            st.success(f"✅ OpenAI key in api_keys.openai_api_key (length: {len(token)})")
            openai_found = True
        elif 'OPENAI_API_KEY' in os.environ:
            token = os.environ['OPENAI_API_KEY']
            st.success(f"✅ OpenAI key in environment (length: {len(token)})")
            openai_found = True
        else:
            st.error("❌ OpenAI API key not found in any location")
        
        if openai_found:
            masked_token = token[:8] + "*" * max(0, len(token) - 12) + token[-4:] if len(token) > 12 else token[:4] + "*" * max(0, len(token) - 4)
            st.code(f"OpenAI Token: {masked_token}")
        
        st.markdown("### Figma API Token Check")
        figma_token_env = os.getenv("FIGMA_ACCESS_TOKEN")
        if figma_token_env:
            st.success(f"✅ FIGMA_ACCESS_TOKEN in environment (length: {len(figma_token_env)})")
            masked_token = figma_token_env[:8] + "*" * max(0, len(figma_token_env) - 12) + figma_token_env[-4:] if len(figma_token_env) > 12 else figma_token_env[:4] + "*" * max(0, len(figma_token_env) - 4)
            st.code(f"Figma Token: {masked_token}")
        else:
            st.error("❌ FIGMA_ACCESS_TOKEN not found in environment")
        
        st.markdown("**Streamlit Secrets Structure:**")
        try:
            if hasattr(st, 'secrets'):
                # Check direct access
                if 'FIGMA_ACCESS_TOKEN' in st.secrets:
                    token = st.secrets['FIGMA_ACCESS_TOKEN']
                    st.success(f"✅ Figma in top-level secrets (length: {len(token)})")
                elif 'api_keys' in st.secrets:
                    st.info("📋 Found api_keys section")
                    if 'figma_token' in st.secrets['api_keys']:
                        token = st.secrets['api_keys']['figma_token']
                        st.success(f"✅ Found in api_keys.figma_token (length: {len(token)})")
                    else:
                        st.warning("⚠️ No figma_token in api_keys section")
                        st.json(list(st.secrets['api_keys'].keys()))
                else:
                    st.warning("⚠️ No FIGMA_ACCESS_TOKEN or api_keys in secrets")
                    st.json(list(st.secrets.keys()))
            else:
                st.error("❌ st.secrets not available")
        except Exception as e:
            st.error(f"❌ Error accessing secrets: {e}")
        
        st.markdown("**Test URLs:**")
        st.info("📋 Your problematic URL:")
        st.code("https://www.figma.com/design/SjpnyFLxV6cCgAtRtpbpTc/Cross-Switch-Branding-and-Website?node-id=3039-12414&m=dev")
        st.info(f"📄 Configured test URL:")
        st.code(f"{os.getenv('FIGMA_TEST_URL', 'Not configured')}")
        
        # Quick test button
        if st.button("🧪 Test Token Access", key="figma_token_test"):
            try:
                from design8 import FigmaDesignComparator
                comparator = FigmaDesignComparator()
                if comparator.figma_token:
                    st.success(f"✅ FigmaDesignComparator loaded token (length: {len(comparator.figma_token)})")
                else:
                    st.error("❌ FigmaDesignComparator could not load token")
            except Exception as e:
                st.error(f"❌ Error testing: {e}")
    
    
    # Initialize defaults in session state to avoid conflicts between widget default values and programmatic state updates
    if 'figma_url_input' not in st.session_state:
        st.session_state.figma_url_input = os.getenv("FIGMA_TEST_URL", "")
    if 'base_web_url_input' not in st.session_state:
        st.session_state.base_web_url_input = os.getenv("WEB_TEST_URL", "")
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = "Full page"
    
    # Initialize loading state session variables
    if 'processing_phase' not in st.session_state:
        st.session_state.processing_phase = ""
    if 'show_processing' not in st.session_state:
        st.session_state.show_processing = False
    with st.expander("Design Presets", expanded=True):
        presets = _load_presets()
        project_names = sorted(presets.keys())
        colp1, colp2 = st.columns([2,1])
        with colp1:
            selected_project = st.selectbox("Load existing project", [""] + project_names, index=0, key="design_preset_select")
        with colp2:
            if st.button("Delete Selected", key="design_preset_delete_btn", use_container_width=True, disabled=(selected_project == "")):
                if selected_project in presets:
                    presets.pop(selected_project, None)
                    _save_presets(presets)
                    st.success(f"Deleted preset '{selected_project}'.")
                    st.rerun()
        colp3, colp4 = st.columns([2,1])
        with colp3:
            new_project_name = st.text_input("Project Name", value=st.session_state.get("design_preset_name", ""), key="design_preset_name_input", placeholder="My Project")
        with colp4:
            if st.button("Save / Update Preset", key="design_preset_save_btn", use_container_width=True):
                if not new_project_name.strip():
                    st.warning("Enter a Project Name to save.")
                else:
                    data = presets.get(new_project_name.strip(), {})
                    data.update({
                        "design_figma_url": st.session_state.get("figma_url_input", ""),
                        "design_base_web_url": st.session_state.get("base_web_url_input", ""),
                        "design_specific_path": st.session_state.get("specific_path_input", ""),
                        "design_similarity_threshold": st.session_state.get("similarity_slider", 0.95),
                        "design_device_type": st.session_state.get("device_type_select", "Desktop"),
                        "design_mobile_device": st.session_state.get("mobile_device_select", ""),
                        "design_tablet_device": st.session_state.get("tablet_device_select", ""),
                        "design_full_page": st.session_state.get("full_page_checkbox", True),
                        "design_overlay_grid": st.session_state.get("overlay_grid_checkbox", False),
                        "design_comparison_mode": st.session_state.get("comparison_mode", "Full page"),
                        # Section-based controls
                        "design_section_max_sections": int(st.session_state.get("section_max_sections", 12)),
                        "design_section_min_height": int(st.session_state.get("section_min_height", 280)),
                        "design_section_min_width": int(st.session_state.get("section_min_width", 400)),
                        "design_section_custom_selectors": st.session_state.get("section_custom_selectors", ""),
                        "design_section_root_selector": st.session_state.get("section_root_selector", ""),
                        "design_jira_assignee": st.session_state.get("jira_assignee_input", ""),
                        "design_enable_video_recording": st.session_state.get("enable_video_recording", False),
                        "design_enable_live_preview": st.session_state.get("enable_live_preview", False),
                    })
                    presets[new_project_name.strip()] = data
                    _save_presets(presets)
                    st.success(f"Saved preset '{new_project_name}'.")
        if selected_project and selected_project in presets and st.button("Load Selected", key="design_preset_load_btn"):
            data = presets[selected_project]
            st.session_state.figma_url_input = data.get("design_figma_url", "")
            st.session_state.base_web_url_input = data.get("design_base_web_url", "")
            st.session_state.specific_path_input = data.get("design_specific_path", "")
            st.session_state.similarity_slider = data.get("design_similarity_threshold", 0.95)
            st.session_state.device_type_select = data.get("design_device_type", "Desktop")
            if st.session_state.device_type_select == "Mobile":
                st.session_state.mobile_device_select = data.get("design_mobile_device", "iPhone 12 Pro")
            if st.session_state.device_type_select == "Tablet":
                st.session_state.tablet_device_select = data.get("design_tablet_device", "iPad Pro")
            st.session_state.full_page_checkbox = data.get("design_full_page", True)
            st.session_state.overlay_grid_checkbox = data.get("design_overlay_grid", False)
            st.session_state.comparison_mode = data.get("design_comparison_mode", "Full page")
            # Section-based controls
            st.session_state.section_max_sections = int(data.get("design_section_max_sections", 12))
            st.session_state.section_min_height = int(data.get("design_section_min_height", 280))
            st.session_state.section_min_width = int(data.get("design_section_min_width", 400))
            st.session_state.section_custom_selectors = data.get("design_section_custom_selectors", "")
            st.session_state.section_root_selector = data.get("design_section_root_selector", "")
            st.session_state.jira_assignee_input = data.get("design_jira_assignee", "")
            st.session_state.enable_video_recording = data.get("design_enable_video_recording", False)
            st.session_state.enable_live_preview = data.get("design_enable_live_preview", False)
            st.session_state.design_preset_name = selected_project
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        figma_url = st.text_input("Figma Design URL", help="URL must contain a `node-id`.", key="figma_url_input")
        base_web_url = st.text_input("Base Web URL", placeholder="https://example.com", key="base_web_url_input")

    with col2:
        st.info("The agent will test the specific Figma node against the web URL provided.")

    with st.expander("Advanced Options"):
        specific_path = st.text_input("Specific Page Path (Optional)", placeholder="/about-us", help="e.g., /contact or /products/new-item", key="specific_path_input")
        similarity_threshold = st.slider("Similarity Threshold", 0.5, 1.0, 0.95, 0.05, key="similarity_slider")
        jira_assignee = st.text_input("Jira Assignee (Email or Name)", help="Optional: Assign created tickets to this user.", key="jira_assignee_input")
        
        st.markdown("---")
        st.subheader("Capture & Comparison Settings")
        comparison_mode = st.radio(
            "Comparison Mode",
            ["Full page", "Section-based"],
            index=0,
            key="comparison_mode",
            help="Full page shows traditional side-by-side with video recording. Section-based provides per-section SSIM heatmaps.")
        
        # Section-based advanced controls
        if comparison_mode == "Section-based":
            st.markdown("##### Section detection controls")
            st.number_input("Max sections to compare", min_value=1, max_value=50, value=st.session_state.get("section_max_sections", 12), step=1, key="section_max_sections")
            colA, colB = st.columns(2)
            with colA:
                st.number_input("Min section height (px)", min_value=100, max_value=3000, value=st.session_state.get("section_min_height", 280), step=20, key="section_min_height")
            with colB:
                st.number_input("Min section width (px)", min_value=200, max_value=5000, value=st.session_state.get("section_min_width", 400), step=20, key="section_min_width")
            st.text_input(
                "Custom section selectors (comma-separated)",
                value=st.session_state.get("section_custom_selectors", ""),
                key="section_custom_selectors",
                help="Optional. Example: section.hero, div.section, [data-section]"
            )
            st.text_input(
                "Root selector override (optional)",
                value=st.session_state.get("section_root_selector", ""),
                key="section_root_selector",
                help="Defaults to main → [role=main] → body"
            )
        
        # New options for enhanced functionality
        full_page_screenshot = st.checkbox("Capture Full Page Screenshot", value=True, key="full_page_checkbox", help="If unchecked, captures only the visible viewport.")
        overlay_grid = st.checkbox("Overlay 12-Column Grid", value=False, key="overlay_grid_checkbox", help="Adds a grid to images to help spot alignment issues.")
        enable_video_recording = st.checkbox("Enable Video Recording", value=True, key="enable_video_recording", help="Record the test execution process as a video.")
        enable_live_preview = st.checkbox("Enable Live Preview (Experimental)", value=False, key="enable_live_preview", help="Show real-time screenshots during test execution. May cause threading issues.")
        
        st.markdown("---")
        st.subheader("Device & Browser Emulation")
        
        # Browser selection
        browser_type = st.selectbox("Select Browser", [
            "Chromium", "Firefox", "Safari (WebKit)"
        ], key="browser_type_select", help="Choose the browser engine for testing")
        
        device_type = st.selectbox("Select Device Type", ["Desktop", "Mobile", "Tablet"], key="device_type_select")
        
        device_to_test = None
        if device_type == "Desktop":
            desktop_resolution = st.selectbox("Desktop Resolution", [
                "1920x1080 (Full HD)",
                "1366x768 (HD)",
                "1440x900 (MacBook Pro 15\")",
                "2560x1440 (QHD)",
                "3840x2160 (4K)"
            ], key="desktop_resolution_select")
            device_to_test = None
        elif device_type == "Mobile":
            mobile_device = st.selectbox("Select Mobile Device", [
                "iPhone 14 Pro",
                "iPhone 14",
                "iPhone 12 Pro",
                "iPhone SE",
                "Samsung Galaxy S22",
                "Samsung Galaxy S21",
                "Google Pixel 7",
                "Google Pixel 5",
                "OnePlus 9"
            ], key="mobile_device_select")
            device_to_test = mobile_device
        elif device_type == "Tablet":
            tablet_device = st.selectbox("Select Tablet Device", [
                "iPad Pro 12.9\"",
                "iPad Pro 11\"", 
                "iPad Air",
                "iPad Mini",
                "Samsung Galaxy Tab S8",
                "Samsung Galaxy Tab S7",
                "Microsoft Surface Pro"
            ], key="tablet_device_select")
            device_to_test = tablet_device

    # Reports & Jira attachments for Design QA
    with st.expander("Artifacts & Reporting"):
        default_reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        st.text_input("Reports Base Folder", value=default_reports_dir, key="design_reports_base_dir")
        st.checkbox("Save HTML/PDF Design QA report", value=True, key="design_save_artifacts_toggle")
        st.checkbox("Attach report to Visual Regression Jira ticket", value=True, key="design_attach_report_toggle")

    # Background run state for Design QA
    if 'design_running' not in st.session_state:
        st.session_state.design_running = False
    if 'design_stop' not in st.session_state:
        st.session_state.design_stop = False
    if 'design_stop_event' not in st.session_state:
        st.session_state.design_stop_event = threading.Event()
    if 'design_logs' not in st.session_state:
        st.session_state.design_logs = []
    if 'design_results' not in st.session_state:
        st.session_state.design_results = None

    def _design_should_stop():
        # Use thread-safe event instead of session_state in worker threads
        ev = st.session_state.get('design_stop_event')
        return ev.is_set() if ev else bool(st.session_state.get('design_stop'))

    if st.button("Run Design QA Analysis", type="primary", use_container_width=True, key="design_qa_button") and not st.session_state.design_running:
        final_web_url = urljoin(base_web_url, specific_path) if specific_path else base_web_url
        
        if not figma_url or not final_web_url:
            st.warning("Please provide both a Figma URL and a Web URL.")
        elif "figma.com" not in figma_url or "node-id" not in figma_url:
            st.error("Invalid Figma URL. It must be a valid `figma.com` URL containing a `node-id`.")
        else:
            # Set processing state
            st.session_state.show_processing = True
            st.session_state.processing_phase = "Initializing Design QA Analysis..."
            
            # Start background run
            st.session_state.design_stop = False
            if st.session_state.get('design_stop_event'):
                st.session_state.design_stop_event.clear()
            st.session_state.design_running = True
            st.session_state.design_logs = []
            st.session_state.design_results = None

            # Live stepper UI (rendered from main thread)
            st.subheader("Test Execution Progress")
            execution_container = st.empty()
            agent.visual_executor = VisualTestExecutor(execution_container)
            # Initialize stepper on main thread before starting background work
            try:
                agent.visual_executor.initialize_steps()
            except Exception:
                pass
            updates_queue = _queue.Queue()
            st.session_state.design_updates_queue = updates_queue
            results_queue = _queue.Queue()
            st.session_state.design_results_queue = results_queue
            phase_updates_queue = _queue.Queue()
            st.session_state.design_phase_queue = phase_updates_queue
            # Precompute config to avoid accessing st.session_state in worker thread
            _save_reports_dir = st.session_state.get("design_reports_base_dir") if st.session_state.get("design_save_artifacts_toggle") else None
            _attach_report_flag = bool(st.session_state.get("design_attach_report_toggle"))
            _enable_video_recording = bool(st.session_state.get("enable_video_recording"))
            _enable_live_preview = bool(st.session_state.get("enable_live_preview"))
            _comparison_mode = st.session_state.get("comparison_mode", "Full page")
            _stop_event = st.session_state.get('design_stop_event')
            # Precompute section-based advanced controls
            _section_max_sections = int(st.session_state.get("section_max_sections", 12))
            _section_min_height = int(st.session_state.get("section_min_height", 280))
            _section_min_width = int(st.session_state.get("section_min_width", 400))
            _section_custom_selectors = [s.strip() for s in str(st.session_state.get("section_custom_selectors", "")).split(",") if s.strip()]
            _section_root_selector = st.session_state.get("section_root_selector", "").strip() or None

            def _bg():
                try:
                    def _safe_feedback(step_index, status, details=""):
                        # Push update into queue; no Streamlit calls here
                        try:
                            updates_queue.put((step_index, status, details))
                        except Exception:
                            pass
                    
                    def _live_preview_callback(screenshot_data):
                        # Handle live preview screenshots
                        try:
                            if screenshot_data:
                                # Store in session state for the Live Preview tab
                                st.session_state.live_preview_image = screenshot_data
                                st.session_state.live_preview_timestamp = datetime.now().strftime("%H:%M:%S")
                        except Exception:
                            pass
                    
                    def _phase_update_callback(phase_name):
                        # Push phase update into queue instead of direct session state access
                        try:
                            phase_updates_queue.put(phase_name)
                        except Exception:
                            pass
                    
                    # Setup live preview callback if enabled
                    live_preview_callback = _live_preview_callback if _enable_live_preview else None

                    def _section_progress(current:int, total:int, msg:str):
                        try:
                            idx = agent.visual_executor.find_step_index("Compare Design vs. Web")
                            updates_queue.put((idx, "running", f"{msg} ({current}/{total})"))
                        except Exception:
                            pass

                    if _comparison_mode == "Section-based":
                        # Full stepper progress updates for section mode
                        _safe_feedback(agent.visual_executor.find_step_index("Parse & Validate Inputs"), "running", "Starting section-based comparison...")
                        _safe_feedback(agent.visual_executor.find_step_index("Parse & Validate Inputs"), "success", "URLs validated successfully.")
                        
                        _safe_feedback(agent.visual_executor.find_step_index("Retrieve Figma Design"), "running", "Fetching Figma design...")
                        _safe_feedback(agent.visual_executor.find_step_index("Retrieve Figma Design"), "success", "Figma design retrieved.")
                        
                        _safe_feedback(agent.visual_executor.find_step_index("Capture Web Page Screenshot"), "running", "Capturing web page sections...")
                        _safe_feedback(agent.visual_executor.find_step_index("Capture Web Page Screenshot"), "success", "Web page sections captured.")
                        
                        _safe_feedback(agent.visual_executor.find_step_index("Compare Design vs. Web"), "running", "Analyzing sections with SSIM heatmaps...")
                        
                        results = agent.processor.process_qa_sections(
                            figma_url=figma_url,
                            web_url=final_web_url,
                            device=device_to_test,
                            save_reports_dir=_save_reports_dir,
                            max_sections=_section_max_sections,
                            min_section_height=_section_min_height,
                            min_section_width=_section_min_width,
                            custom_section_selectors=_section_custom_selectors if _section_custom_selectors else None,
                            root_selector=_section_root_selector,
                            progress_callback=_section_progress,
                        )
                        
                        _safe_feedback(agent.visual_executor.find_step_index("Compare Design vs. Web"), "success", f"Section analysis complete. {results.get('sections_reviewed', 0)} sections reviewed.")
                        _safe_feedback(agent.visual_executor.find_step_index("Run Functional Validations"), "running", "Running functional validations...")
                        _safe_feedback(agent.visual_executor.find_step_index("Run Functional Validations"), "success", "Functional validations complete.")
                        _safe_feedback(agent.visual_executor.find_step_index("Create Jira Tickets"), "running", "Checking Jira ticket requirements...")
                        _safe_feedback(agent.visual_executor.find_step_index("Create Jira Tickets"), "success", "Jira ticket check complete.")
                        _safe_feedback(agent.visual_executor.find_step_index("Generate Final Report"), "success" if results.get('success') else "error", "Section-based analysis completed.")
                    else:
                        # Use the full stepper process for Full page mode
                        results = agent.processor.process_qa_request(
                            figma_url, final_web_url, jira_assignee, similarity_threshold,
                            mobile_device=device_to_test,
                            browser_type=st.session_state.get("browser_type_select", "Chromium"),
                            full_page=full_page_screenshot,
                            overlay_grid=overlay_grid,
                            live_feedback_callback=_safe_feedback,
                            step_finder=agent.visual_executor.find_step_index,
                            should_stop_callback=(_stop_event.is_set if _stop_event else _design_should_stop),
                            save_reports_dir=_save_reports_dir,
                            attach_report_to_jira=_attach_report_flag,
                            enable_video_recording=_enable_video_recording,
                            live_preview_callback=live_preview_callback,
                            phase_update_callback=_phase_update_callback,
                        )
                    try:
                        results_queue.put(results)
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        results_queue.put({"success": False, "error": str(e), "trace": traceback.format_exc()})
                    except Exception:
                        pass
                finally:
                    pass

            t = threading.Thread(target=_bg, daemon=True)
            t.start()
            st.session_state.design_thread = t
            st.info("Design QA started. You can stop the run below. The view will update on completion.")
            st.rerun()

    # Running / control UI
    if st.session_state.design_running:
        colz1, colz2 = st.columns([3,1])
        with colz1:
            # Drain any pending step updates and render in main thread
            q = st.session_state.get('design_updates_queue')
            if q is not None:
                try:
                    while True:
                        try:
                            idx, status, details = q.get_nowait()
                        except Exception:
                            break
                        try:
                            agent.visual_executor.update_step(idx, status, details)
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # Drain any pending phase updates and update session state in main thread
            pq = st.session_state.get('design_phase_queue')
            if pq is not None:
                try:
                    while True:
                        try:
                            phase_name = pq.get_nowait()
                            st.session_state.processing_phase = phase_name
                        except Exception:
                            break
                except Exception:
                    pass
            
            # Show loading indicator with current phase
            if st.session_state.get('show_processing') and st.session_state.get('processing_phase'):
                with st.spinner(st.session_state.processing_phase):
                    st.info("Design QA is running...")
            else:
                st.info("Design QA is running...")
        with colz2:
            if st.button("Stop Design QA", type="secondary", use_container_width=True):
                st.session_state.design_stop = True
                if st.session_state.get('design_stop_event'):
                    st.session_state.design_stop_event.set()
                st.warning("Stop requested. Finishing current step...")
        # Auto-refresh when the design thread completes
        t = st.session_state.get('design_thread')
        # Drain results if available
        rq = st.session_state.get('design_results_queue')
        if rq is not None:
            try:
                while True:
                    try:
                        _res = rq.get_nowait()
                    except Exception:
                        break
                    st.session_state.design_results = _res
                    st.session_state.design_running = False
                    # Clear processing state when complete
                    st.session_state.show_processing = False
                    st.session_state.processing_phase = ""
            except Exception:
                pass
        if t and not t.is_alive():
            st.session_state.design_running = False
            st.rerun()
        else:
            # Gentle auto-refresh to render progress updates
            time.sleep(0.7)
            st.rerun()

    # Results UI
    if (not st.session_state.design_running) and st.session_state.get('design_results') is not None:
        results = st.session_state.design_results
        st.subheader("Final Report")
        if not results.get('success'):
            if results.get('stopped'):
                st.warning("Design QA run stopped by user.")
            else:
                st.error(f"Analysis Failed: {results.get('error', 'An unknown error occurred.')}")
                if results.get('trace'):
                    with st.expander("Traceback"):
                        st.code(results['trace'])
        else:
            # Determine which comparison mode was used based on results structure
            is_section_based = bool(results.get('artifacts', {}).get('sections_image'))
            comparison_mode_used = "Section-based" if is_section_based else "Full page"
            
            st.info(f"**Comparison Mode Used**: {comparison_mode_used}")
            
            if is_section_based:
                # Section-based comparison result display
                artifacts = results.get('artifacts') or {}
                sec_img = artifacts.get('sections_image')
                if sec_img and os.path.exists(sec_img):
                    try:
                        with open(sec_img, 'rb') as f:
                            sec_bytes = f.read()
                        st.image(sec_bytes, caption="Section-based: Figma | Web | SSIM Heatmap", width="stretch")
                        st.download_button(
                            label="Download sections comparison",
                            data=sec_bytes,
                            file_name=os.path.basename(sec_img),
                            mime="image/png",
                            key="download_sections_image",
                        )
                    except Exception as e:
                        st.warning(f"Sections image available but could not be displayed: {e}")
            else:
                # Full-page comparison result display
                if results.get('comparison_image_path'):
                    try:
                        cmp_path = results['comparison_image_path']
                        img_bytes = None
                        try:
                            with open(cmp_path, 'rb') as _f:
                                img_bytes = _f.read()
                        except Exception:
                            img_bytes = None
                        if img_bytes:
                            st.image(img_bytes, caption="Technical Comparison: Figma vs. Web vs. Diff", width="stretch")
                            st.download_button(
                                label="Download technical comparison",
                                data=img_bytes,
                                file_name=os.path.basename(cmp_path),
                                mime="image/png",
                                key="download_comparison_image",
                            )
                        else:
                            st.image(cmp_path, caption="Technical Comparison: Figma vs. Web vs. Diff", width="stretch")
                        # Clean up temp file if it still exists
                        try:
                            if os.path.exists(cmp_path):
                                os.unlink(cmp_path)
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Could not display comparison image: {e}")
                
                # ENHANCED: Prefer designer-style callouts image if available
                if results.get('designer_callouts_path'):
                    try:
                        c_path = results['designer_callouts_path']
                        with open(c_path, 'rb') as _f:
                            c_bytes = _f.read()
                        st.subheader("📋 Designer QA Callouts")
                        st.image(c_bytes, caption="Designer-Style QA with Callouts", width="stretch")
                        st.download_button(
                            label="Download Designer QA (Callouts)",
                            data=c_bytes,
                            file_name=os.path.basename(c_path),
                            mime="image/png",
                            key="download_designer_callouts",
                        )
                        try:
                            if os.path.exists(c_path):
                                os.unlink(c_path)
                        except Exception:
                            pass
                    except Exception as e:
                        st.warning(f"Could not display designer callouts: {e}")

                # ENHANCED: Display designer-style diff if available
                if results.get('designer_diff_path'):
                    try:
                        designer_path = results['designer_diff_path']
                        designer_bytes = None
                        try:
                            with open(designer_path, 'rb') as _f:
                                designer_bytes = _f.read()
                        except Exception:
                            designer_bytes = None
                        if designer_bytes:
                            st.subheader("📋 Designer QA Report")
                            st.image(designer_bytes, caption="Designer-Style QA Report", width="stretch")
                            st.download_button(
                                label="Download Designer QA Report",
                                data=designer_bytes,
                                file_name=os.path.basename(designer_path),
                                mime="image/png",
                                key="download_designer_diff",
                            )
                        # Clean up temp file
                        try:
                            if os.path.exists(designer_path):
                                os.unlink(designer_path)
                        except Exception:
                            pass
                    except Exception as e:
                        st.warning(f"Could not display designer diff: {e}")
                
                # ENHANCED: Display AI feedback if available  
                if results.get('ai_feedback'):
                    st.subheader("🤖 AI Designer Feedback")
                    st.markdown(results['ai_feedback'])

            # Display video recording if available
            if results.get('video_recording_path'):
                try:
                    video_path = results['video_recording_path']
                    if os.path.exists(video_path):
                        st.subheader("🎥 Test Execution Recording")
                        st.video(video_path)
                        
                        # Offer download for video
                        try:
                            with open(video_path, 'rb') as video_file:
                                video_bytes = video_file.read()
                            st.download_button(
                                label="Download Test Recording",
                                data=video_bytes,
                                file_name=f"test_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm",
                                mime="video/webm",
                                key="download_test_video",
                            )
                        except Exception as e:
                            st.warning(f"Video download not available: {e}")
                    else:
                        st.info("Video recording was enabled but video file not found.")
                except Exception as e:
                    st.error(f"Could not display video recording: {e}")

            # Metrics
            score = results.get('similarity_score', None)
            avg_ssim = results.get('average_ssim', None)
            issues_count = results.get('functional_issues_found', 0)
            if score is not None:
                st.metric("Visual Similarity Score", f"{score:.1%}",
                          delta=f"{(score - similarity_threshold):.1%}",
                          delta_color="inverse" if score < similarity_threshold else "normal")
            if avg_ssim is not None:
                st.metric("Avg Visual Similarity (Sections)", f"{avg_ssim:.1%}")
            if issues_count > 0:
                st.warning(f"Found {issues_count} functional issue(s).")
            if results.get('tickets_created'):
                st.success("Jira tickets were created for the following issues:")
                for ticket in results['tickets_created']:
                    if ticket.get('success'):
                        st.markdown(f"- **{ticket['ticket_key']}**: [View Ticket]({ticket['ticket_url']})")
                    else:
                        st.error(f"- Failed to create ticket: {ticket.get('error')}")
            else:
                # Check if tickets should have been created
                ticket_reasons = []
                if score is not None and score < similarity_threshold:
                    ticket_reasons.append(f"Visual similarity ({score:.1%}) below threshold ({similarity_threshold:.1%})")
                if issues_count > 0:
                    ticket_reasons.append(f"{issues_count} functional issues found")
                
                if ticket_reasons:
                    st.warning(f"Issues detected but no Jira tickets created: {'; '.join(ticket_reasons)}. Check your Jira configuration.")
                else:
                    ok_full = (score is not None) and (score >= similarity_threshold)
                    ok_sections = (avg_ssim is not None) and (avg_ssim >= similarity_threshold)
                    if (ok_full or ok_sections) and issues_count == 0:
                        st.success("✅ All checks passed! No discrepancies found.")

            # Show saved artifacts if any
            artifacts = results.get('artifacts') or {}
            if artifacts:
                st.markdown("#### Saved Artifacts")
                for k, v in artifacts.items():
                    st.write(f"- {k}: {v}")

        colx1, colx2 = st.columns([1,1])
        with colx1:
            if st.button("Refresh View", type="secondary", use_container_width=True, key="design_refresh_btn"):
                st.rerun()
        with colx2:
            if st.button("Clear Results", use_container_width=True, key="design_clear_btn"):
                st.session_state.design_results = None
                st.rerun()

def _list_saved_test_cases(base_dir: str):
    paths = []
    try:
        for root, dirs, files in os.walk(base_dir):
            for fn in files:
                if fn == "test_cases.json":
                    paths.append(os.path.join(root, fn))
    except Exception:
        pass
    # Sort by most recent directory name if it contains timestamp
    try:
        paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    except Exception:
        pass
    return paths

def render_functional_qa_tab(agent):
    """Renders the UI for the new UX-driven Functional QA feature."""
    st.header("UX-Driven Functional Testing (Playwright)")
    st.markdown("Generate and execute Playwright tests from a UX document, Jira ticket, and Figma design.")

    # Initialize defaults in session_state for inputs to avoid conflicts with widget defaults
    if 'func_web_url_input' not in st.session_state:
        st.session_state.func_web_url_input = os.getenv("WEB_TEST_URL", "")
    if 'func_figma_url_input' not in st.session_state:
        st.session_state.func_figma_url_input = os.getenv("FIGMA_TEST_URL", "")
    if 'func_figma_ux_url_input' not in st.session_state:
        st.session_state.func_figma_ux_url_input = os.getenv("FIGMA_UX_URL", "")

    # --- Project Presets ---
    with st.expander("Project Presets", expanded=True):
        presets = _load_presets()
        project_names = sorted(presets.keys())
        colp1, colp2 = st.columns([2,1])
        with colp1:
            selected_project = st.selectbox("Load existing project", [""] + project_names, index=0, key="preset_select")
        with colp2:
            if st.button("Delete Selected", key="preset_delete_btn", use_container_width=True, disabled=(selected_project == "")):
                if selected_project in presets:
                    presets.pop(selected_project, None)
                    _save_presets(presets)
                    st.success(f"Deleted preset '{selected_project}'.")
                    st.rerun()
        colp3, colp4 = st.columns([2,1])
        with colp3:
            new_project_name = st.text_input("Project Name", value=st.session_state.get("preset_name", ""), key="preset_name_input", placeholder="My Project")
        with colp4:
            if st.button("Save / Update Preset", key="preset_save_btn", use_container_width=True):
                if not new_project_name.strip():
                    st.warning("Enter a Project Name to save.")
                else:
                    presets[new_project_name.strip()] = {
                        "jira_ticket_id": st.session_state.get("func_jira_ticket_input", ""),
                        "web_url": st.session_state.get("func_web_url_input", ""),
                        "figma_url": st.session_state.get("func_figma_url_input", ""),
                        "figma_ux_url": st.session_state.get("func_figma_ux_url_input", ""),
                        "jira_assignee": st.session_state.get("func_jira_assignee_input", ""),
                    }
                    _save_presets(presets)
                    st.success(f"Saved preset '{new_project_name}'.")
        if selected_project and selected_project in presets and st.button("Load Selected", key="preset_load_btn"):
            data = presets[selected_project]
            # Populate form state and refresh
            st.session_state.func_jira_ticket_input = data.get("jira_ticket_id", "")
            st.session_state.func_web_url_input = data.get("web_url", "")
            st.session_state.func_figma_url_input = data.get("figma_url", "")
            st.session_state.func_figma_ux_url_input = data.get("figma_ux_url", "")
            st.session_state.func_jira_assignee_input = data.get("jira_assignee", "")
            st.session_state.preset_name = selected_project
            st.rerun()

    # --- Inputs ---
    uploaded_ux_file = st.file_uploader(
        "Upload UX/Business Logic Document",
        type=[".txt", ".md", ".pdf"],
        help="Upload a text/markdown/PDF file with business rules and user flows."
    )

    col1, col2 = st.columns(2)
    with col1:
        jira_ticket_id = st.text_input(
            "Jira Ticket ID",
            placeholder="QA-123",
            help="Enter a valid Jira key like QA-123. If invalid, tests will still run without Jira context.",
            key="func_jira_ticket_input",
        )
        web_url = st.text_input("Web URL to Test", placeholder="https://example.com/feature-page", key="func_web_url_input")
    with col2:
        figma_url = st.text_input("Figma Design URL", help="The Figma design related to the Jira ticket.", key="func_figma_url_input")
        figma_ux_url = st.text_input("Optional: Figma UX URL for Content", help="Provide a Figma node URL to extract UX copy from the design.", key="func_figma_ux_url_input")
        jira_assignee = st.text_input("Jira Assignee for Failures", help="Optional: Assign created bug tickets to this user.", key="func_jira_assignee_input")

    # --- Execution ---
    # Initialize state
    if 'func_running' not in st.session_state:
        st.session_state.func_running = False
    if 'func_stop' not in st.session_state:
        st.session_state.func_stop = False
    if 'func_logs' not in st.session_state:
        st.session_state.func_logs = []
    if 'func_logs_queue' not in st.session_state:
        st.session_state.func_logs_queue = _queue.Queue()
    if 'func_results' not in st.session_state:
        st.session_state.func_results = None
    if 'func_auto_refresh' not in st.session_state:
        st.session_state.func_auto_refresh = True

    # Options for saving and Jira attachments
    with st.expander("Artifacts & Reporting"):
        default_reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        reports_dir = st.text_input("Reports Base Folder", value=default_reports_dir, help="Where to save generated test cases and results.", key="reports_base_dir")
        save_artifacts = st.checkbox("Save generated artifacts (HTML/PDF) to disk", value=True, key="save_artifacts_toggle")
        attach_report = st.checkbox("Attach saved HTML/PDF report and JSON to Jira failure tickets", value=True, key="attach_report_toggle")

    # Start combined generate+run
    if not st.session_state.func_running and st.button("Generate and Run Functional Tests", type="primary", use_container_width=True, key="functional_qa_button"):
        # Accept UX content from either an uploaded file OR a Figma UX URL
        if not (jira_ticket_id and web_url and figma_url and (uploaded_ux_file or figma_ux_url)):
            st.warning("Please provide a Jira Ticket ID, Web URL, Figma Design URL, and either upload a UX document or provide a Figma UX URL.")
        else:
            # Read UX content from txt/md/pdf
            ux_content = ""
            if uploaded_ux_file is not None:
                name = (uploaded_ux_file.name or "").lower()
                if name.endswith(".pdf"):
                    try:
                        reader = PdfReader(uploaded_ux_file)
                        pages_text = []
                        for page in reader.pages:
                            try:
                                pages_text.append(page.extract_text() or "")
                            except Exception:
                                pages_text.append("")
                        ux_content = "\n\n".join(pages_text).strip()
                        if not ux_content:
                            st.warning("The uploaded PDF appears to have no extractable text. If it is scanned images, OCR is not supported here.")
                    except Exception as e:
                        st.error(f"Failed to read PDF: {e}")
                        ux_content = ""
                else:
                    # Treat as plain text/markdown
                    try:
                        ux_content = uploaded_ux_file.read().decode("utf-8", errors="ignore")
                    except Exception as e:
                        st.error(f"Failed to read file: {e}")
                        ux_content = ""

            # Prepare state
            agent.jira_assignee = jira_assignee
            import re as _re
            if jira_ticket_id and not _re.match(r"^[A-Z][A-Z0-9_]+-\d+$", jira_ticket_id.strip(), _re.IGNORECASE):
                st.warning("Jira key format looks invalid (expected like QA-123). Proceeding without Jira details.")

            st.session_state.func_stop = False
            st.session_state.func_logs = []
            st.session_state.func_results = None
            st.session_state.func_running = True

            def _feedback(msg: str):
                # Push messages to a queue; UI reads them from main thread
                try:
                    st.session_state.func_logs_queue.put(msg)
                except Exception:
                    pass

            def _should_stop():
                return bool(st.session_state.get('func_stop'))

            # Precompute toggles to avoid st.* inside thread
            _save_toggle = bool(st.session_state.get("save_artifacts_toggle"))
            _reports_base = st.session_state.get("reports_base_dir")
            _attach_toggle = bool(st.session_state.get("attach_report_toggle"))

            def _worker():
                try:
                    save_dir = None
                    if _save_toggle:
                        stamp = datetime.now().strftime("test_report_%Y%m%d_%H%M%S")
                        save_dir = os.path.join(_reports_base, stamp)
                    results = agent.run_full_test_cycle(
                        figma_url=figma_url,
                        web_url=web_url,
                        jira_ticket_id=jira_ticket_id,
                        figma_ux_url=figma_ux_url or None,
                        ux_file_content=ux_content,
                        live_feedback_callback=_feedback,
                        should_stop_callback=_should_stop,
                        save_dir=save_dir,
                        attach_report_to_jira=_attach_toggle,
                    )
                    st.session_state.func_results = results
                except Exception as e:
                    st.session_state.func_results = {"error": str(e), "trace": traceback.format_exc()}
                finally:
                    st.session_state.func_running = False

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            st.session_state.func_thread = t
            st.info("Run started in background. Use 'Stop Run' to cancel. This view will update when complete.")
            st.rerun()

    # Running view
    if st.session_state.func_running:
        st.subheader("Functional Test Execution")
        colr1, colr2 = st.columns([3,1])
        with colr1:
            # Drain logs from queue into session list (main thread only)
            try:
                q = st.session_state.get('func_logs_queue')
                if q is not None:
                    while True:
                        try:
                            msg = q.get_nowait()
                        except Exception:
                            break
                        st.session_state.func_logs.append(msg)
            except Exception:
                pass
            st.info("\n".join(st.session_state.func_logs[-10:]) or "Waiting for updates...")
        with colr2:
            if st.button("Stop Run", type="secondary", use_container_width=True):
                st.session_state.func_stop = True
                st.warning("Stop requested. Finishing current step...")
        st.checkbox("Auto-refresh on completion", key="func_auto_refresh")

        # If thread ended between reruns, refresh now
        t = st.session_state.get('func_thread')
        if t and not t.is_alive():
            st.session_state.func_running = False
            if st.session_state.get('func_auto_refresh', True):
                st.rerun()

    # Run from saved test cases
    st.markdown("---")
    st.subheader("Run From Saved Test Cases")
    saved_cases = _list_saved_test_cases(st.session_state.get("reports_base_dir", os.path.join(os.path.dirname(__file__), "reports")))
    sel_path = st.selectbox("Select saved test_cases.json", options=[""] + saved_cases, index=0, help="Choose previously generated test cases to execute.")
    if not st.session_state.func_running and st.button("Run Selected Saved Test Cases", use_container_width=True, disabled=(not sel_path)):
        try:
            with open(sel_path, "r", encoding="utf-8") as f:
                saved_test_cases = json.load(f)
        except Exception as e:
            st.error(f"Failed to load test cases: {e}")
            saved_test_cases = None
        if saved_test_cases:
            st.session_state.func_stop = False
            st.session_state.func_logs = []
            st.session_state.func_results = None
            st.session_state.func_running = True

            def _feedback(msg: str):
                try:
                    st.session_state.func_logs_queue.put(msg)
                except Exception:
                    pass

            def _should_stop():
                return bool(st.session_state.get('func_stop'))

            # Precompute config to avoid st.* inside thread
            _save_toggle2 = bool(st.session_state.get("save_artifacts_toggle"))
            _reports_base2 = st.session_state.get("reports_base_dir")
            _attach_toggle2 = bool(st.session_state.get("attach_report_toggle"))

            def _worker2():
                try:
                    # Execute tests directly
                    test_results = agent.execute_test_suite(web_url, saved_test_cases, _feedback, _should_stop)
                    # Optionally save HTML/PDF report using agent
                    artifacts = {}
                    if _save_toggle2:
                        stamp = datetime.now().strftime("test_report_%Y%m%d_%H%M%S")
                        save_dir = os.path.join(_reports_base2, stamp)
                        artifacts = agent.save_artifacts(save_dir, web_url, figma_url, jira_ticket_id, {}, saved_test_cases, test_results)
                    # Log failures to Jira optionally with attachments
                    tickets = agent.log_failed_tests_to_jira(
                        test_results, web_url, figma_url, jira_ticket_id, _should_stop,
                        attachments_extra=[artifacts.get("report_pdf"), artifacts.get("report_html"), artifacts.get("test_cases"), artifacts.get("test_results")] if (_attach_toggle2 and artifacts) else None
                    )
                    st.session_state.func_results = {"user_stories_generated": {}, "test_cases_generated": saved_test_cases, "test_results": test_results, "jira_tickets_created": tickets, "artifacts": artifacts}
                except Exception as e:
                    st.session_state.func_results = {"error": str(e), "trace": traceback.format_exc()}
                finally:
                    st.session_state.func_running = False

            t2 = threading.Thread(target=_worker2, daemon=True)
            t2.start()
            st.session_state.func_thread = t2
            st.info("Execution started. View will update when finished.")
            st.rerun()

    # Results view
    if (not st.session_state.func_running) and st.session_state.func_results is not None:
        results = st.session_state.func_results
        st.subheader("Final Report")
        if results.get("error"):
            st.error(f"An error occurred: {results['error']}")
            if results.get("trace"):
                with st.expander("Traceback"):
                    st.code(results.get("trace"))
        elif results.get("stopped"):
            st.warning("Run stopped by user.")
        else:
            # Display User Stories
            st.markdown("#### Generated User Stories")
            with st.expander("Click to view the user stories generated from the UX document"):
                st.json(results.get("user_stories_generated", {}))

            # Display Test Cases
            st.markdown("#### Generated Playwright Test Cases")
            with st.expander("Click to view the test cases generated by the AI"):
                st.json(results.get("test_cases_generated", []))

            # Display Test Results
            st.markdown("#### Test Execution Results")
            test_results = results.get("test_results", [])
            passed_count = sum(1 for r in test_results if r['passed'])
            failed_count = len(test_results) - passed_count

            col1, col2 = st.columns(2)
            col1.metric("Tests Passed ✅", passed_count)
            col2.metric("Tests Failed ❌", failed_count)

            for result in test_results:
                if result['passed']:
                    st.success(f"PASS: {result['description']}")
                else:
                    with st.expander(f"FAIL: {result['description']}", expanded=True):
                        st.error(result['failure_reason'])
                        if result['screenshot']:
                            st.image(result['screenshot'], caption="Screenshot at time of failure.", use_container_width=True)

            # Display saved artifacts
            artifacts = results.get("artifacts") or {}
            if artifacts:
                st.markdown("#### Saved Artifacts")
                for k, p in artifacts.items():
                    st.write(f"- {k}: {p}")

            # Display Jira Tickets
            tickets_created = results.get("jira_tickets_created", [])
            if tickets_created:
                st.markdown("#### Jira Tickets Created for Failures")
                for ticket in tickets_created:
                    if ticket.get('success'):
                        st.success(f"Created ticket [{ticket['ticket_key']}]({ticket['ticket_url']})")
                    else:
                        st.error(f"Failed to create Jira ticket: {ticket.get('error')}")

        colrf1, colrf2 = st.columns([1,1])
        with colrf1:
            if st.button("Refresh View", type="secondary", use_container_width=True):
                st.rerun()
        with colrf2:
            if st.button("Clear Results", use_container_width=True):
                st.session_state.func_results = None
                st.session_state.func_logs = []
                st.rerun()

def render_fluid_breakpoint_tab(agent):
    """Renders the UI for the Fluid Breakpoint testing feature."""
    st.header("Fluid Breakpoint Animation")
    st.markdown("Test how your design reflows across a range of screen widths. The agent will resize the browser window and generate a GIF of the result.")
    # Initialize default in session_state to avoid conflicts
    if 'fluid_web_url_input' not in st.session_state:
        st.session_state.fluid_web_url_input = os.getenv("WEB_TEST_URL", "")

    web_url = st.text_input("Web URL to Test", placeholder="https://example.com/my-responsive-page", key="fluid_web_url_input")

    col1, col2 = st.columns(2)
    with col1:
        start_width = st.number_input("Start Width (px)", min_value=320, max_value=1920, value=320, step=10, key="fluid_start_width")
    with col2:
        end_width = st.number_input("End Width (px)", min_value=320, max_value=2560, value=1200, step=10, key="fluid_end_width")

    with st.expander("Animation Settings"):
        steps = st.slider("Animation Frames", 10, 50, 20, help="How many individual screenshots to capture for the animation.", key="fluid_steps_slider")
        frame_duration = st.slider("Frame Duration (seconds)", 0.1, 1.0, 0.2, step=0.05, help="How long each frame is displayed in the final GIF.", key="fluid_duration_slider")

    with st.expander("Artifacts & Reporting"):
        default_reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        st.text_input("Reports Base Folder", value=default_reports_dir, key="fluid_reports_base_dir")
        st.checkbox("Save HTML/PDF Fluid report", value=True, key="fluid_save_artifacts_toggle")
        st.checkbox("Attach report to Jira ticket", value=False, key="fluid_attach_report_toggle")
        jira_assignee = st.text_input("Jira Assignee (Email or Name)", value=st.session_state.get("jira_assignee_input",""), key="fluid_jira_assignee")

    if st.button("Generate Breakpoint Animation", type="primary", use_container_width=True, key="fluid_run_button"):
        if not web_url:
            st.warning("Please provide a Web URL to test.")
        elif start_width >= end_width:
            st.error("Start Width must be less than End Width.")
        else:
            with st.spinner(f"Generating animation from {start_width}px to {end_width}px... This may take a moment."):
                gif_path = agent.run_fluid_breakpoint_test(web_url, start_width, end_width, steps, frame_duration)

            if gif_path and os.path.exists(gif_path):
                st.subheader("Responsive Test Animation")
                try:
                    st.image(gif_path, caption=f"Fluid layout from {start_width}px to {end_width}px", use_container_width=True)
                    # Save report and optionally attach to Jira via design processor
                    try:
                        save_dir = os.path.join(st.session_state.get("fluid_reports_base_dir"), "") if st.session_state.get("fluid_save_artifacts_toggle") else None
                        res = None
                        if hasattr(agent, 'processor') and agent.processor:
                            res = agent.processor.process_fluid_breakpoints(
                                web_url,
                                start_width=start_width,
                                end_width=end_width,
                                steps=steps,
                                frame_duration=frame_duration,
                                device=None,
                                save_reports_dir=save_dir,
                                attach_report_to_jira=bool(st.session_state.get("fluid_attach_report_toggle")),
                                jira_assignee=st.session_state.get("fluid_jira_assignee") or None,
                            )
                        if res and res.get('artifacts'):
                            st.markdown("#### Saved Artifacts")
                            for k, v in res['artifacts'].items():
                                st.write(f"- {k}: {v}")
                        if res and res.get('ticket'):
                            t = res['ticket']
                            if t and t.get('success'):
                                st.success(f"Jira ticket created: [{t['ticket_key']}]({t['ticket_url']})")
                    except Exception as e:
                        st.warning(f"Could not save/attach fluid report: {e}")
                    # Clean up the temp GIF file after processing
                    try:
                        os.unlink(gif_path)
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Failed to display animation: {e}")
            else:
                st.error("Failed to generate the breakpoint animation. Please check the application logs for more details.")

def main():
    # Configure page with favicon
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.png")
    
    # Use the custom favicon if available, otherwise fallback to emoji
    if os.path.exists(favicon_path):
        st.set_page_config(
            page_title="Quali - Your QA Buddy", 
            page_icon=favicon_path, 
            layout="wide"
        )
    else:
        st.set_page_config(
            page_title="Quali - Your QA Buddy", 
            page_icon="🎨", 
            layout="wide"
        )

    # Load and inject custom CSS theme
    try:
        css_file_path = os.path.join(os.path.dirname(__file__), "streamlit_theme.css")
        if os.path.exists(css_file_path):
            with open(css_file_path, "r") as css_file:
                css_content = css_file.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Could not load custom CSS theme: {e}")

    # Add header with high-quality logo
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon_64x64.png")
    large_logo_path = os.path.join(os.path.dirname(__file__), "quali_logo.png")
    
    # Use the original logo if available for better quality in header
    logo_to_use = large_logo_path if os.path.exists(large_logo_path) else favicon_path
    
    if os.path.exists(logo_to_use):
        # Convert logo to base64 for embedding
        import base64
        with open(logo_to_use, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        
        # Determine logo size based on which file we're using
        logo_size = "80px" if logo_to_use == large_logo_path else "48px"
        
        # Create header with high-quality logo
        st.markdown(f"""
        <div style="
            display: flex; 
            align-items: center; 
            margin-bottom: 2rem; 
            padding: 1.5rem 0;
            background: linear-gradient(135deg, rgba(64, 224, 208, 0.05), rgba(138, 92, 246, 0.05));
            border-radius: 12px;
            border: 1px solid rgba(64, 224, 208, 0.2);
        ">
            <img src="data:image/png;base64,{logo_b64}" 
                 style="
                     width: {logo_size}; 
                     height: {logo_size}; 
                     margin-right: 1.5rem; 
                     margin-left: 1rem;
                     border-radius: 12px;
                     box-shadow: 0 4px 12px rgba(64, 224, 208, 0.3);
                 ">
            <div>
                <h1 style="
                    margin: 0; 
                    background: linear-gradient(135deg, #40e0d0, #8a5cf6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 2.8rem; 
                    font-weight: 800;
                    letter-spacing: -0.5px;
                ">
                    Quali AI
                </h1>
                <p style="
                    margin: 0; 
                    color: #a0a0a0; 
                    font-size: 1.2rem;
                    font-weight: 500;
                ">
                    Your Intelligent QA Testing Companion
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Import team features
    try:
        from team_features import render_team_welcome_tab, add_team_features
        add_team_features()
    except ImportError:
        # Team features not available, continue without them
        pass

    # Updated logo for Quali (QA → QL)
    logo_base64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI3MiIgaGVpZ2h0PSI3MiIgdmlld0JveD0iMCAwIDcyIDcyIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM4YjVjZjY7c3RvcC1vcGFjaXR5OjEiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3R5bGU9InN0b3AtY29sb3I6IzIyZDNlZTtzdG9wLW9wYWNpdHk6MSIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgPC9kZWZzPgogIDxjaXJjbGUgY3g9IjM2IiBjeT0iMzYiIHI9IjM0IiBmaWxsPSJ1cmwoI2dyYWQpIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1OCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIyNHB4IiBmb250LXdlaWdodD0iYm9sZCIgZmlsbD0id2hpdGUiPlFMPC90ZXh0Pgo8L3N2Zz4="
    
    # Hero section with Envole-inspired styling
    st.markdown(f"""
    <div class="hero-background">
        <div class="logo-container">
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 1.5rem;">
                <img src="{logo_base64}" width="72" height="72" alt="Quali Logo" style="flex-shrink: 0;"/>
                <div style="flex: 1; min-width: 300px;">
                    <h1 style="margin: 0 0 0.5rem 0; font-size: clamp(2.5rem, 5vw, 3.5rem); font-weight: 700; line-height: 1.1;">Quali</h1>
                    <p style="margin: 0 0 0.5rem 0; color: #9ca3af; font-size: clamp(1rem, 2vw, 1.2rem); font-weight: 500; line-height: 1.3;">Your AI-Powered Quality Assurance Buddy</p>
                    <p style="margin: 0; color: #22d3ee; font-size: clamp(0.8rem, 1.5vw, 0.9rem); font-style: italic; opacity: 0.9;">Intelligent • Comprehensive • Beautiful</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show cloud deployment notice if applicable
    if IS_CLOUD_DEPLOYMENT or not BROWSER_AUTOMATION_AVAILABLE:
        st.markdown("""
        <div style="
            background: rgba(34, 211, 238, 0.1);
            border: 1px solid rgba(34, 211, 238, 0.3);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            backdrop-filter: blur(10px);
        ">
            <h4 style="color: #22d3ee; margin: 0 0 1rem 0; font-size: 1.1rem; font-weight: 600;">🌤️ Cloud Deployment Mode Active</h4>
            <p style="color: #e5e7eb; margin: 0 0 0.75rem 0; font-size: 0.95rem; line-height: 1.5;">You're running Quali in cloud mode! Some features are optimized for cloud deployment:</p>
            <ul style="color: #9ca3af; margin: 0; padding-left: 1.5rem; font-size: 0.9rem; line-height: 1.6;">
                <li style="margin-bottom: 0.25rem;">Browser automation is disabled for cloud compatibility</li>
                <li style="margin-bottom: 0.25rem;">Focus on AI-powered analysis and design validation</li>
                <li style="margin-bottom: 0;">Full desktop features available when running locally</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    if 'agent' not in st.session_state:
        st.session_state.agent = MonsterQAAgent()
    if 'functional_agent' not in st.session_state:
        st.session_state.functional_agent = FunctionalQAAgent()

    if not st.session_state.agent.is_initialized:
        st.error("Agent initialization failed. Please check the logs and ensure all dependencies are correctly installed.")
        st.stop()

    # Include welcome tab for teams
    try:
        from team_features import render_team_welcome_tab
        tab0, tab1, tab4, tab3, tab6, tab7, tab8, tab2, tab5 = st.tabs([
            "👋 Welcome", 
            "🤖 Design QA", 
            "📝 Test Case Generation", 
            "🎯 Enhanced Functional Testing", 
            "�️ Solutions Architecture",
            "📋 User Story Generation", 
            "💬 AI Chat Assistant",
            "�🌊 Fluid Breakpoints", 
            "📡 Live Preview"
        ])
        
        with tab0:
            render_team_welcome_tab()
    except ImportError:
        tab1, tab4, tab3, tab6, tab7, tab8, tab2, tab5 = st.tabs([
            "🤖 Design QA", 
            "📝 Test Case Generation", 
            "🎯 Enhanced Functional Testing", 
            "🏗️ Solutions Architecture",
            "📋 User Story Generation",
            "💬 AI Chat Assistant",
            "🌊 Fluid Breakpoints", 
            "📡 Live Preview"
        ])

    with tab1:
        render_design_qa_tab(st.session_state.agent)

    with tab2:
        render_fluid_breakpoint_tab(st.session_state.agent)

    with tab3:
        # Enhanced Functional Testing - Phase 2
        try:
            from functional_testing_ui import render_functional_testing_ui
            render_functional_testing_ui()
        except ImportError:
            # Fallback to basic functional testing if enhanced version not available
            render_functional_qa_tab(st.session_state.functional_agent)
    
    with tab6:
        # Solutions Architecture - Phase 3
        try:
            from solutions_architecture import render_solutions_architecture_tab
            render_solutions_architecture_tab()
        except ImportError as e:
            st.error("❌ Solutions Architecture module not available")
            st.info("🚧 This feature requires the solutions_architecture module")
            st.code(f"Import error: {e}")
    
    with tab7:
        # User Story Generation - Phase 3
        try:
            from user_story_generation import render_user_story_generation_tab
            render_user_story_generation_tab()
        except ImportError as e:
            st.error("❌ User Story Generation module not available")
            st.info("🚧 This feature requires the user_story_generation module")
            st.code(f"Import error: {e}")
    
    with tab8:
        # AI Chat Assistant - Phase 3
        try:
            from chat_assistant import render_chat_assistant_tab
            render_chat_assistant_tab()
        except ImportError as e:
            st.error("❌ AI Chat Assistant module not available")
            st.info("🚧 This feature requires the chat_assistant module")
            st.code(f"Import error: {e}")

    with tab4:
        render_test_case_generation_tab(st.session_state.functional_agent)

    with tab5:
        render_live_preview_tab()

def render_live_preview_tab():
    """Renders the Live Preview tab for real-time test monitoring."""
    st.header("📡 Live Preview")
    st.markdown("Real-time preview of test execution. Enable Live Preview in Design QA to see live screenshots here.")
    
    # Check if live preview is enabled
    live_preview_enabled = st.session_state.get("enable_live_preview", False)
    design_running = st.session_state.get("design_running", False)
    
    if not live_preview_enabled:
        st.info("💡 Enable 'Live Preview' in the Design QA tab's Advanced Options to see real-time test execution here.")
        return
    
    if not design_running:
        st.info("🔄 Start a Design QA test with Live Preview enabled to see real-time screenshots.")
        return
    
    st.success("🎯 Live Preview is active! Screenshots will appear below as the test runs.")
    
    # Create placeholder for live preview images
    preview_container = st.empty()
    
    # Initialize live preview state
    if 'live_preview_image' not in st.session_state:
        st.session_state.live_preview_image = None
    if 'live_preview_timestamp' not in st.session_state:
        st.session_state.live_preview_timestamp = None
    
    # Display current live preview image
    with preview_container.container():
        if st.session_state.live_preview_image:
            st.image(
                st.session_state.live_preview_image,
                caption=f"Live Preview - Last updated: {st.session_state.live_preview_timestamp}",
                width='stretch'
            )
        else:
            st.info("Waiting for live preview images...")
    
    # Auto-refresh when tests are running
    if design_running:
        time.sleep(1)
        st.rerun()

def render_test_case_generation_tab(agent):
    st.header("AI-Powered Test Case Generation")
    st.markdown("Generate Playwright test cases from your UX document and Jira context, save them for later execution.")

    # Initialize defaults to avoid widget default + session_state value conflicts
    if 'gen_figma_url' not in st.session_state:
        st.session_state.gen_figma_url = os.getenv("FIGMA_TEST_URL", "")
    if 'gen_figma_ux_url' not in st.session_state:
        st.session_state.gen_figma_ux_url = os.getenv("FIGMA_UX_URL", "")

    uploaded_ux_file = st.file_uploader("Upload UX/Business Logic Document", type=[".txt", ".md", ".pdf"], help="Upload text/markdown/PDF with flows and rules.")

    col1, col2 = st.columns(2)
    with col1:
        jira_ticket_id = st.text_input("Jira Ticket ID", placeholder="QA-123", key="gen_jira_ticket")
        figma_url = st.text_input("Figma Design URL", key="gen_figma_url")
    with col2:
        figma_ux_url = st.text_input("Optional: Figma UX URL for Content", key="gen_figma_ux_url")
        reports_base_dir = st.text_input("Reports Base Folder", value=os.path.join(os.path.dirname(__file__), "reports"), key="gen_reports_dir")

    # Read UX input
    ux_content = ""
    if uploaded_ux_file is not None:
        name = (uploaded_ux_file.name or "").lower()
        if name.endswith(".pdf"):
            try:
                reader = PdfReader(uploaded_ux_file)
                pages_text = []
                for page in reader.pages:
                    try:
                        pages_text.append(page.extract_text() or "")
                    except Exception:
                        pages_text.append("")
                ux_content = "\n\n".join(pages_text).strip()
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")
        else:
            try:
                ux_content = uploaded_ux_file.read().decode("utf-8", errors="ignore")
            except Exception as e:
                st.error(f"Failed to read file: {e}")

    if st.button("Generate Test Cases", type="primary"):
        if not (figma_url and (ux_content or figma_ux_url)):
            st.warning("Provide a Figma Design URL and either upload a UX document or give a Figma UX URL.")
        else:
            jira_content = agent.get_jira_acceptance_criteria(st.session_state.get("gen_jira_ticket", ""))
            # Pull text from Figma UX URL if provided
            ux_combined = ux_content
            if figma_ux_url:
                ux_figma_text = agent.get_ux_text_from_figma_url(figma_ux_url)
                if ux_figma_text:
                    ux_combined = (ux_combined + "\n\n---\n\n" + ux_figma_text) if ux_combined else ux_figma_text
            user_stories = agent.generate_user_stories_from_ux(ux_combined, jira_content)
            test_cases = agent.generate_test_cases_from_ai(figma_url, jira_content, ux_combined)

            st.subheader("Generated User Stories")
            st.json(user_stories)
            st.subheader("Generated Test Cases")
            st.json(test_cases)

            # Save
            stamp = datetime.now().strftime("test_report_%Y%m%d_%H%M%S")
            save_dir = os.path.join(reports_base_dir, stamp)
            try:
                os.makedirs(save_dir, exist_ok=True)
                with open(os.path.join(save_dir, "user_stories.json"), "w", encoding="utf-8") as f:
                    json.dump(user_stories or {}, f, indent=2)
                with open(os.path.join(save_dir, "test_cases.json"), "w", encoding="utf-8") as f:
                    json.dump(test_cases or [], f, indent=2)
                st.success(f"Saved artifacts to: {save_dir}")
            except Exception as e:
                st.error(f"Failed to save artifacts: {e}")

if __name__ == "__main__":
    # Avoid cleaning up on each rerun; Streamlit reruns frequently during long tasks.
    try:
        main()
    except Exception as e:
        st.error(f"A critical application error occurred: {e}")
        st.code(traceback.format_exc())
