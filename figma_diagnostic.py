"""
Figma Token Diagnostic Tool
Add this to your Streamlit app to debug token configuration issues
"""

import streamlit as st
import os
from design8 import FigmaDesignComparator

def render_figma_diagnostic():
    """Render Figma diagnostic information"""
    
    st.markdown("### 🔍 Figma Configuration Diagnostic")
    
    with st.expander("🛠️ Token Configuration Status", expanded=True):
        
        # Check token configuration
        figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        
        if figma_token:
            st.success(f"✅ FIGMA_ACCESS_TOKEN configured (length: {len(figma_token)})")
            # Mask token for security
            masked_token = figma_token[:8] + "*" * (len(figma_token) - 12) + figma_token[-4:]
            st.code(f"Token: {masked_token}")
        else:
            st.error("❌ FIGMA_ACCESS_TOKEN not configured")
            st.markdown("""
            **To fix this:**
            1. Go to Streamlit Cloud Dashboard
            2. Select your app
            3. Go to Settings → Secrets
            4. Add: `FIGMA_ACCESS_TOKEN = "your_token_here"`
            """)
        
        # Check test URL
        test_url = os.getenv("FIGMA_TEST_URL")
        if test_url:
            st.info(f"📄 FIGMA_TEST_URL configured")
            st.code(f"URL: {test_url}")
        else:
            st.warning("⚠️ FIGMA_TEST_URL not configured")
    
    # Quick test section
    st.markdown("### 🧪 Quick Access Test")
    
    test_url = st.text_input(
        "Test Figma URL", 
        value="https://www.figma.com/design/SjpnyFLxV6cCgAtRtpbpTc/Cross-Switch-Branding-and-Website?node-id=3039-12414&m=dev",
        help="Enter a Figma URL to test access"
    )
    
    if st.button("🔍 Test Access", type="primary"):
        if figma_token and test_url:
            with st.spinner("Testing Figma API access..."):
                try:
                    comparator = FigmaDesignComparator()
                    
                    # Parse URL
                    node_info = comparator.get_specific_node_from_url(test_url)
                    if node_info:
                        st.success(f"✅ URL parsed successfully")
                        st.json({
                            "file_id": node_info['file_id'],
                            "node_id": node_info['node_id']
                        })
                        
                        # Test image retrieval
                        image = comparator.get_node_image(node_info['file_id'], node_info['node_id'])
                        if image:
                            st.success("✅ Image retrieved successfully!")
                            st.image(image, caption="Retrieved Figma Design", width=300)
                        else:
                            st.error("❌ Failed to retrieve image")
                            st.markdown("""
                            **Possible causes:**
                            - Token doesn't have access to this file
                            - File is in a different organization
                            - File is private/restricted
                            - Token is expired or invalid
                            """)
                    else:
                        st.error("❌ Failed to parse Figma URL")
                        
                except Exception as e:
                    st.error(f"❌ Error testing access: {str(e)}")
        else:
            st.warning("⚠️ Please configure FIGMA_ACCESS_TOKEN and provide a test URL")

# Add this to your main app
if __name__ == "__main__":
    render_figma_diagnostic()
