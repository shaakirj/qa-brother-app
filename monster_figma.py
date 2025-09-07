"""
monster2.py - Unified QA AI Agent with Visual Real-Time Test Execution
Fixed version with simplified logic and correct delegation to the processor.
"""

import streamlit as st
import os
from dotenv import load_dotenv
import time
import logging
import traceback
from datetime import datetime

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Attempt to import the necessary processor from design8
try:
    from design8 import DesignQAProcessor
    DESIGN8_AVAILABLE = True
except ImportError as e:
    st.error(f"Fatal Error: Could not import 'design8.py'. Please ensure the file exists and is correct. Details: {e}")
    DESIGN8_AVAILABLE = False
    # Define a fallback class so the app doesn't crash immediately
    class DesignQAProcessor:
        def process_qa_request(self, *args, **kwargs):
            return {"success": False, "error": "DesignQAProcessor is not available due to import failure."}
        def cleanup(self):
            pass

class VisualTestExecutor:
    """Manages the visual display of test execution steps."""
    
    def __init__(self, container):
        self.container = container
        self.steps = []
        self.start_time = None
        
    def initialize_steps(self):
        """Initializes the steps for the design QA test."""
        self.start_time = datetime.now()
        self.steps = [
            {"name": "Parse & Validate Inputs", "status": "pending", "icon": "📝", "details": ""},
            {"name": "Retrieve Figma Design", "status": "pending", "icon": "🎨", "details": ""},
            {"name": "Capture Web Page Screenshot", "status": "pending", "icon": "📸", "details": ""},
            {"name": "Compare Design vs. Web", "status": "pending", "icon": "🔍", "details": ""},
            {"name": "Run Functional Validations", "status": "pending", "icon": "⚙️", "details": ""},
            {"name": "Create Jira Tickets", "status": "pending", "icon": "🎟️", "details": ""},
            {"name": "Generate Final Report", "status": "pending", "icon": "📊", "details": ""}
        ]
        self.update_display()

    def update_step(self, step_name, status, details=""):
        """Update the status and details of a specific step."""
        for step in self.steps:
            if step["name"] == step_name:
                step["status"] = status
                step["details"] = details
                break
        self.update_display()

    def update_display(self):
        """Renders the current state of all steps."""
        with self.container.container():
            elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            st.caption(f"Elapsed time: {elapsed:.1f}s")
            
            for step in self.steps:
                icon = step["icon"]
                name = step["name"]
                status = step["status"]
                details = step.get("details", "")

                if status == "running":
                    st.info(f"**{icon} {name}...**\n\n_{details}_")
                elif status == "success":
                    st.success(f"**{icon} {name}**\n\n{details}")
                elif status == "error":
                    st.error(f"**{icon} {name}**\n\n{details}")
                else: # pending
                    st.write(f"{icon} {name}")

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

    def run_design_qa_with_visual(self, figma_url, web_url, jira_assignee=None, similarity_threshold=0.95):
        """
        Correctly runs the design QA process by delegating to the processor
        and updating the UI based on the results.
        """
        if not self.visual_executor or not self.processor:
            return {"success": False, "error": "Agent or Visual Executor not initialized."}

        self.visual_executor.initialize_steps()

        results = self.processor.process_qa_request(
            figma_url, web_url, jira_assignee, similarity_threshold
        )

        # This block is updated to handle the new, specific error codes.
        if results.get('success'):
            self.visual_executor.update_step("Parse & Validate Inputs", "success", "URLs validated.")
            self.visual_executor.update_step("Retrieve Figma Design", "success", "Figma image downloaded.")
            self.visual_executor.update_step("Capture Web Page Screenshot", "success", "Web page screenshot captured.")
            
            score = results.get('similarity_score', 0)
            self.visual_executor.update_step("Compare Design vs. Web", "success", f"Comparison complete. Similarity: {score:.1%}")
            
            issues_found = results.get('functional_issues_found', 0)
            self.visual_executor.update_step("Run Functional Validations", "success", f"Found {issues_found} functional issues.")
            
            tickets_created = len([t for t in results.get('tickets_created', []) if t.get('success')])
            self.visual_executor.update_step("Create Jira Tickets", "success", f"Created {tickets_created} Jira tickets.")
            
            self.visual_executor.update_step("Generate Final Report", "success", "All tasks completed.")
        else:
            # If the process failed, show the error at the correct step.
            error_message = results.get('error', 'An unknown error occurred.')
            if "ERROR_STEP_PARSE" in error_message:
                self.visual_executor.update_step("Parse & Validate Inputs", "error", error_message)
            elif "ERROR_STEP_FIGMA_IMG" in error_message:
                self.visual_executor.update_step("Retrieve Figma Design", "error", error_message)
            elif "ERROR_STEP_SCREENSHOT" in error_message:
                self.visual_executor.update_step("Capture Web Page Screenshot", "error", error_message)
            elif "ERROR_STEP_COMPARE" in error_message:
                self.visual_executor.update_step("Compare Design vs. Web", "error", error_message)
            else:
                self.visual_executor.update_step("Generate Final Report", "error", error_message)

        return results

    def cleanup(self):
        """Cleans up resources used by the agent."""
        if hasattr(self, 'processor') and self.processor:
            try:
                self.processor.cleanup()
                logger.info("QA Agent resources cleaned up successfully.")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

def main():
    st.set_page_config(page_title="Monster QA Agent", page_icon="🤖", layout="wide")

    st.title("Monster QA Agent")
    st.markdown("**Unified AI-Powered Quality Assurance System**")
    st.markdown("---")

    if 'agent' not in st.session_state:
        st.session_state.agent = MonsterQAAgent()

    if not st.session_state.agent.is_initialized:
        st.error("Agent initialization failed. Please check the logs and ensure 'design8.py' is correct.")
        st.stop()

    st.header("Design QA Testing")
    st.markdown("Compare a Figma design with its live web implementation.")
    
    col1, col2 = st.columns(2)
    with col1:
        figma_url = st.text_input("Figma Design URL", value=os.getenv("FIGMA_TEST_URL", ""), help="URL must contain a `node-id`.")
    with col2:
        web_url = st.text_input("Web Implementation URL", value=os.getenv("WEB_TEST_URL", ""))
    
    with st.expander("Advanced Options"):
        similarity_threshold = st.slider("Similarity Threshold", 0.5, 1.0, 0.95, 0.05)
        jira_assignee = st.text_input("Jira Assignee (Email or Name)", help="Optional: Assign created tickets to this user.")

    if st.button("Run Design QA Analysis", type="primary", use_container_width=True):
        if not figma_url or not web_url:
            st.warning("Please provide both a Figma URL and a Web URL.")
        elif "figma.com" not in figma_url or "node-id" not in figma_url:
            st.error("Invalid Figma URL. It must be a valid `figma.com` URL containing a `node-id`.")
        else:
            st.subheader("Test Execution Progress")
            execution_container = st.empty()
            
            agent = st.session_state.agent
            agent.visual_executor = VisualTestExecutor(execution_container)
            
            with st.spinner("Running analysis..."):
                results = agent.run_design_qa_with_visual(
                    figma_url, web_url, jira_assignee, similarity_threshold
                )
            
            st.subheader("Final Report")
            if results.get('success'):
                score = results.get('similarity_score', 0)
                issues_count = results.get('functional_issues_found', 0)
                
                st.metric("Visual Similarity Score", f"{score:.1%}", 
                          delta=f"{(score - similarity_threshold):.1%}",
                          delta_color="inverse" if score < similarity_threshold else "normal")

                if issues_count > 0:
                    st.warning(f"Found {issues_count} functional issue(s).")
                
                if results.get('tickets_created'):
                    st.success("Jira tickets were created for the following issues:")
                    for ticket in results['tickets_created']:
                        if ticket.get('success'):
                            st.markdown(f"- **{ticket['ticket_key']}**: [View Ticket]({ticket['ticket_url']})")
                        else:
                            st.error(f"- Failed to create ticket: {ticket.get('error')}")
                elif score >= similarity_threshold and issues_count == 0:
                    st.success("✅ All checks passed! No discrepancies found.")

            else:
                st.error(f"Analysis Failed: {results.get('error', 'An unknown error occurred.')}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"A critical application error occurred: {e}")
        st.code(traceback.format_exc())
    finally:
        if 'agent' in st.session_state:
            st.session_state.agent.cleanup()