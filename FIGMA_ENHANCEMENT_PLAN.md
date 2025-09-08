# Enhanced Figma Integration with Dynamic Token Support

## Implementation Plan

This document outlines how to implement dynamic Figma token support to allow users to process Figma URLs from any organization.

### Current Architecture Issue

The current `FigmaDesignComparator` class loads a single token during initialization:

```python
class FigmaDesignComparator:
    def __init__(self):
        self.figma_token = os.getenv("FIGMA_ACCESS_TOKEN")  # Fixed token
        self.headers = {"X-Figma-Token": self.figma_token}
```

### Proposed Enhanced Architecture

#### Option A: Token Parameter in Methods
Modify methods to accept an optional token parameter:

```python
class FigmaDesignComparator:
    def __init__(self):
        self.default_figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.base_url = "https://api.figma.com/v1"
    
    def _get_headers(self, custom_token=None):
        token = custom_token or self.default_figma_token
        return {"X-Figma-Token": token} if token else {}
    
    def get_node_image(self, file_id, node_id, scale=3, figma_token=None):
        headers = self._get_headers(figma_token)
        # ... rest of implementation
```

#### Option B: Context Manager Pattern
Use a context manager for temporary token switching:

```python
@contextmanager
def figma_token_context(self, custom_token):
    old_token = self.figma_token
    self.figma_token = custom_token
    self.headers = {"X-Figma-Token": custom_token} if custom_token else {}
    try:
        yield
    finally:
        self.figma_token = old_token
        self.headers = {"X-Figma-Token": old_token} if old_token else {}
```

### UI Integration

Add an optional token input field in the Streamlit interface:

```python
# In monster2.py Design QA section
with st.expander("🔧 Advanced Figma Settings", expanded=False):
    custom_token = st.text_input(
        "Custom Figma Token (Optional)", 
        type="password",
        help="Provide your own Figma token to access files from different organizations",
        placeholder="Enter your personal Figma access token..."
    )
    st.info("💡 If left empty, will use the default configured token")
```

### Security Considerations

1. **Token Storage**: Never store user-provided tokens permanently
2. **Session Isolation**: Ensure tokens don't leak between user sessions
3. **Validation**: Validate tokens before use
4. **Error Handling**: Don't expose token values in error messages

### Implementation Steps

1. **Phase 1**: Enhanced error reporting (✅ Already implemented)
2. **Phase 2**: Add optional token parameters to Figma methods
3. **Phase 3**: Update UI to accept custom tokens
4. **Phase 4**: Add token validation and testing
5. **Phase 5**: Update documentation and user guides

### Code Changes Required

#### 1. FigmaDesignComparator Class Updates
- Add `_get_headers()` helper method
- Modify `get_node_image()` and `get_node_properties()` to accept token parameter
- Add token validation method

#### 2. UI Updates
- Add expandable section for advanced Figma settings
- Add password input for custom token
- Add token testing functionality

#### 3. Processing Pipeline Updates
- Pass custom token through the processing chain
- Update `process_qa_request()` to handle custom tokens

### Testing Strategy

1. **Token Validation**: Test with valid/invalid tokens
2. **Cross-Organization**: Test with files from different organizations
3. **Permission Testing**: Test with restricted file access
4. **Security Testing**: Ensure no token leakage in logs/errors

### Benefits

- ✅ Users can process any Figma URL they have access to
- ✅ Maintains backward compatibility with default token
- ✅ Improves error messages and user experience
- ✅ Adds flexibility without breaking existing functionality

### Risks and Mitigation

- **Risk**: Token security concerns
  - **Mitigation**: Use password input, don't log tokens, clear from memory
- **Risk**: UI complexity
  - **Mitigation**: Keep advanced features in collapsible section
- **Risk**: Session management
  - **Mitigation**: Use proper Streamlit session state handling
