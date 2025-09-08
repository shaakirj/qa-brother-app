# Figma Integration Usage Guide

## Understanding Figma Access Limitations

The QA Brother app uses Figma's API to retrieve design images and properties for comparison. Due to how Figma's authentication system works, there are important limitations to understand:

### How Figma Authentication Works

- **Access Tokens**: Figma uses personal access tokens for API authentication
- **Organization Scope**: Each token can only access files within the same Figma organization/account that created the token
- **Privacy Settings**: Tokens can only access files they have permission to view

### Current App Configuration

The app is configured with a single Figma access token through the `FIGMA_ACCESS_TOKEN` environment variable. This means:

✅ **Will Work**: Figma URLs from the same organization/account as the configured token
❌ **Will NOT Work**: Figma URLs from different organizations or accounts

### Common Error Scenarios

#### Error: "Failed to retrieve Figma image"
**Likely Causes:**
1. **Different Organization**: The Figma URL is from a different organization than the token
2. **Private File**: The file is private and the token doesn't have access
3. **Invalid Token**: The configured token is expired or invalid
4. **Non-existent Node**: The node-id in the URL doesn't exist

#### Error: "Figma API access denied (403)"
- The token doesn't have permission to access this specific file
- The file may be in a different organization

#### Error: "Figma file not found (404)"
- The file ID is invalid or the file doesn't exist
- The file may be private and inaccessible to the token

### Solutions and Workarounds

#### Option 1: Use Compatible Figma Files
- Use Figma files from the same organization as the configured token
- Ask your team admin to share the file with the account that created the token

#### Option 2: Configure Multiple Tokens (Development Required)
*This would require code changes to support dynamic token selection*

#### Option 3: Public File Testing
- Create a public Figma file for testing purposes
- Note: Public files still require a valid token for API access

### Testing Your Figma Setup

1. **Check Token Configuration**: Ensure `FIGMA_ACCESS_TOKEN` is properly set
2. **Use Known Working URL**: Start with a Figma URL you know the token can access
3. **Verify Node ID**: Ensure your URL contains a valid `node-id` parameter

### URL Format Requirements

Your Figma URL must follow this format:
```
https://www.figma.com/design/[FILE_ID]/[FILE_NAME]?node-id=[NODE_ID]
```

Example:
```
https://www.figma.com/design/ABC123DEF456/My-Design?node-id=123-456
```

### Troubleshooting Steps

1. **Verify URL Format**: Ensure the URL contains both file ID and node-id
2. **Check Permissions**: Confirm you have access to view the Figma file
3. **Test in Browser**: Open the Figma URL in your browser to confirm it loads
4. **Review Logs**: Check the application logs for detailed error messages

### Getting Help

If you continue to experience issues:
1. Check the detailed error messages in the app
2. Verify your Figma URL format
3. Confirm the file is accessible with your current account
4. Consider using a file from the same organization as the configured token

---
*For technical support or feature requests regarding Figma integration, consult your development team.*
