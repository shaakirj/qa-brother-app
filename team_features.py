"""
Team-friendly configuration and user guide for QA Brother
"""

import streamlit as st
import os
from datetime import datetime

def render_team_welcome_tab():
    """Renders a welcome tab with team instructions and tips"""
    st.header("👋 Welcome to QA Brother!")
    st.markdown("""
    QA Brother is your AI-powered quality assurance companion that helps you:
    - **Compare designs** with live websites automatically
    - **Test across devices** (mobile, tablet, desktop)
    - **Generate test reports** and create Jira tickets
    - **Save time** on manual QA tasks
    """)
    
    # Quick start guide
    st.subheader("🚀 Quick Start Guide")
    
    with st.expander("🎨 Design QA Testing", expanded=True):
        st.markdown("""
        **What it does:** Compares your Figma designs with live websites
        
        **Steps:**
        1. **Get your Figma URL:** Copy the link from your Figma design
        2. **Enter website URL:** The live site you want to test
        3. **Choose device:** Desktop, mobile, or tablet
        4. **Click 'Start Design QA'**
        5. **Review results:** Get visual comparisons and AI analysis
        
        **Tip:** Make sure your Figma link includes a node-id (the part after node-id=)
        """)
    
    with st.expander("⚙️ Functional Testing"):
        st.markdown("""
        **What it does:** Tests website functionality and user flows
        
        **Steps:**
        1. **Upload test cases** or let AI generate them
        2. **Configure test parameters**
        3. **Run automated tests**
        4. **Get detailed reports**
        """)
    
    with st.expander("📱 Responsive Testing"):
        st.markdown("""
        **What it does:** Tests how your site looks across different screen sizes
        
        **Steps:**
        1. **Enter your website URL**
        2. **Set screen size range** (e.g., mobile to desktop)
        3. **Watch the animation** showing breakpoint transitions
        """)
    
    # Common issues and solutions
    st.subheader("❗ Common Issues & Solutions")
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Problem:** "Could not parse Figma URL"
        - **Solution:** Make sure your Figma URL includes `node-id=` parameter
        - **Example:** `https://figma.com/file/.../Your-Design?node-id=123-456`
        
        **Problem:** "Failed to capture web screenshot"
        - **Solution:** Check if the website is publicly accessible
        - **Solution:** Try unchecking "Full Page Screenshot" for long pages
        
        **Problem:** Browser setup failed
        - **Solution:** Try refreshing the page
        - **Solution:** Switch browser types in Device Emulation section
        
        **Problem:** Tests taking too long
        - **Solution:** Use smaller screen sizes or fewer breakpoints
        - **Solution:** Ensure stable internet connection
        """)
    
    # Tips for better results
    st.subheader("💡 Pro Tips for Better Results")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🎯 Design QA Tips:**
        - Use specific Figma frames (not entire pages)
        - Test mobile designs with mobile device emulation
        - Enable video recording for complex tests
        - Save presets for frequently tested sites
        """)
    
    with col2:
        st.markdown("""
        **📊 Reporting Tips:**
        - Enable Jira integration for team collaboration
        - Use descriptive test names for easy tracking
        - Save reports to shared folders
        - Review AI analysis for improvement suggestions
        """)
    
    # Team collaboration features
    st.subheader("👥 Team Collaboration")
    
    st.markdown("""
    **Sharing Results:**
    - All reports include shareable HTML files
    - Video recordings can be shared with stakeholders
    - Jira tickets automatically notify assignees
    
    **Best Practices:**
    - Create presets for commonly tested pages
    - Use consistent naming conventions
    - Regular testing on different devices
    - Document any recurring issues
    """)

def render_user_profile():
    """Simple user profile for team tracking"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 User Profile")
    
    # Get user name from session or ask for it
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    
    user_name = st.sidebar.text_input("Your Name", value=st.session_state.user_name, key="user_input")
    if user_name != st.session_state.user_name:
        st.session_state.user_name = user_name
    
    if st.session_state.user_name:
        st.sidebar.success(f"Logged in as: {st.session_state.user_name}")
        
        # Quick stats
        st.sidebar.markdown("**Your Session:**")
        st.sidebar.write(f"Started: {datetime.now().strftime('%H:%M')}")
        
        # Save user preference
        if 'test_count' not in st.session_state:
            st.session_state.test_count = 0
        st.sidebar.write(f"Tests run: {st.session_state.test_count}")

def render_quick_help():
    """Quick help sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("❓ Quick Help")
    
    help_topics = {
        "🎨 Figma URL Format": "Your URL should look like: https://figma.com/file/ABC123/Design?node-id=1-2",
        "📱 Device Testing": "Choose Mobile for phones, Tablet for iPads, Desktop for computers",
        "⚙️ Browser Choice": "Chromium works best, try Firefox/Safari if issues occur",
        "📊 Reports Location": "Find your test reports in the 'reports' folder",
        "🎟️ Jira Integration": "Tests can automatically create tickets for issues found"
    }
    
    selected_help = st.sidebar.selectbox("Select help topic:", list(help_topics.keys()))
    if selected_help:
        st.sidebar.info(help_topics[selected_help])

def add_team_features():
    """Add team-friendly features to the app"""
    render_user_profile()
    render_quick_help()
    
    # Add keyboard shortcuts info
    st.sidebar.markdown("---")
    st.sidebar.markdown("**⌨️ Shortcuts:**")
    st.sidebar.markdown("- `Ctrl+Enter`: Run test")
    st.sidebar.markdown("- `Ctrl+R`: Refresh page")
    st.sidebar.markdown("- `Esc`: Stop running test")

# Export functions for use in main app
__all__ = ['render_team_welcome_tab', 'add_team_features']
