# Figma Cloud Deployment Troubleshooting Guide

## Your Specific Issue

**Error**: `Analysis Failed: ERROR_STEP_FIGMA_IMG: Failed to retrieve Figma image. The configured token may not have access to this file.`

**URL**: `https://www.figma.com/design/SjpnyFLxV6cCgAtRtpbpTc/Cross-Switch-Branding-and-Website?node-id=3039-12414&m=dev`

**Status**: 
- ✅ Works locally (token has access)
- ❌ Fails in Streamlit Cloud

## Root Cause

The issue is **Streamlit Cloud environment configuration**, not the Figma URL or local token permissions.

## Immediate Fix: Configure Streamlit Cloud Secrets

### Step 1: Access Streamlit Cloud Dashboard
1. Go to https://share.streamlit.io/
2. Find your `qa-brother-app` application
3. Click on the app name to open settings

### Step 2: Configure Secrets
1. Click **"Settings"** (gear icon)
2. Click **"Secrets"** tab
3. Add your Figma token:

```toml
FIGMA_ACCESS_TOKEN = "your_figma_token_here"
```

### Step 3: Get Your Local Token
To find your local token that works:

```bash
# In your local terminal
cd "/Users/Shaakir/Documents/project1/LT agent"
grep FIGMA_ACCESS_TOKEN .env
```

Copy the token value (without quotes) and paste it into Streamlit Cloud secrets.

### Step 4: Restart the App
1. Save the secrets configuration
2. The app will automatically restart
3. Test with your Cross-Switch URL

## Verification Steps

Once configured, you should see in the Debug section:
- ✅ FIGMA_ACCESS_TOKEN configured
- ✅ Token length matches your local token
- ✅ Image retrieval works

## Alternative: Use the Working Test URL

As a temporary workaround, you can use the URL that's already configured to work:
```
https://www.figma.com/design/D0tXCTuRzPjTL1yy0NrPlG/Scans.ai--Dev-?node-id=65-4882&t=0NwZs9UxaGbSHEBM-4
```

## Advanced: Multiple Token Support

For long-term solution, consider implementing dynamic token support:

1. Add custom token input in the UI
2. Allow users to provide their own tokens
3. Support multiple organization access

See `FIGMA_ENHANCEMENT_PLAN.md` for implementation details.

## Security Notes

- Never commit tokens to your repository
- Use Streamlit Cloud Secrets for production
- Rotate tokens periodically
- Limit token permissions to necessary files only

## Common Issues

### Issue: "Token configured but still failing"
**Solution**: Check if the token in Cloud matches your local working token

### Issue: "Token length different in Cloud"
**Solution**: Token may be truncated or have extra spaces - copy-paste carefully

### Issue: "Works for some URLs but not others"
**Solution**: Token may not have access to all Figma organizations - verify file permissions

## Testing Checklist

- [ ] Token configured in Streamlit Cloud Secrets
- [ ] Token length matches local environment
- [ ] Debug section shows token configured
- [ ] Test with known working URL first
- [ ] Test with your Cross-Switch URL
- [ ] Remove debug section after fixing

## Support

If the issue persists after following these steps:
1. Check the debug section in the app
2. Verify token permissions in Figma
3. Test locally with the same URL
4. Compare local vs cloud token configuration

---
**Created**: September 8, 2025  
**Issue**: Figma token configuration in Streamlit Cloud  
**Status**: Ready for resolution
