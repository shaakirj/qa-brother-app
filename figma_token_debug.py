"""
Alternative Figma Token Access for Streamlit Cloud
This handles different ways Streamlit Cloud might expose secrets
"""

import streamlit as st
import os

def get_figma_token():
    """Try multiple ways to get Figma token from Streamlit Cloud"""
    
    # Method 1: Direct environment variable
    token = os.getenv("FIGMA_ACCESS_TOKEN")
    if token:
        return token, "Environment Variable"
    
    # Method 2: Streamlit secrets (flat structure)
    try:
        if hasattr(st, 'secrets') and 'FIGMA_ACCESS_TOKEN' in st.secrets:
            return st.secrets['FIGMA_ACCESS_TOKEN'], "Streamlit Secrets (Direct)"
    except:
        pass
    
    # Method 3: Streamlit secrets (nested structure)
    try:
        if hasattr(st, 'secrets') and 'figma' in st.secrets:
            return st.secrets['figma']['FIGMA_ACCESS_TOKEN'], "Streamlit Secrets (Nested)"
    except:
        pass
    
    # Method 4: Check api_keys section
    try:
        if hasattr(st, 'secrets') and 'api_keys' in st.secrets:
            # Look for various possible names
            for key in ['figma_token', 'FIGMA_ACCESS_TOKEN', 'figma_access_token']:
                if key in st.secrets['api_keys']:
                    return st.secrets['api_keys'][key], f"Streamlit Secrets (api_keys.{key})"
    except:
        pass
    
    return None, "Not Found"

# Test function
if __name__ == "__main__":
    token, method = get_figma_token()
    if token:
        print(f"✅ Token found via: {method}")
        print(f"   Length: {len(token)}")
        print(f"   Masked: {token[:8]}****{token[-4:]}")
    else:
        print("❌ Token not found")
        print("   Checked: Environment, Streamlit Secrets (direct, nested, api_keys)")
