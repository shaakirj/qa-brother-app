# Environment Configuration Troubleshooting

## Common Issues and Solutions

### OpenAI API Key Warnings
**Issue**: `WARNING - OpenAI API key not found` in logs

**Root Cause**: Modules not loading environment variables from `.env` file

**Solution**: ✅ **FIXED** - Added `load_dotenv()` to all modules
- `solutions_architecture.py` 
- `user_story_generation.py`
- `chat_assistant.py`

### Environment Variable Loading

#### Local Development
The app uses a `.env` file in the project root:
```properties
OPENAI_API_KEY=sk-proj-your-key-here
GROQ_API_KEY=gsk_your-groq-key-here
FIGMA_ACCESS_TOKEN=figd_your-figma-token-here
```

#### Cloud Deployment (Streamlit Cloud)
The app uses Streamlit secrets in `streamlit_secrets.toml`:
```toml
[api_keys]
openai_api_key = "sk-proj-your-key-here"
groq_api_key = "gsk_your-groq-key-here"
figma_token = "figd_your-figma-token-here"
```

### Module Loading Order
All AI-powered modules now properly load environment variables:

1. **Import phase**: `from dotenv import load_dotenv`
2. **Loading phase**: `load_dotenv()` 
3. **Access phase**: `os.environ['OPENAI_API_KEY']` or `st.secrets['OPENAI_API_KEY']`

### Verification Commands

Test environment loading:
```bash
# Check if .env file exists and has the key
./qa_env/bin/python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY found:', 'OPENAI_API_KEY' in os.environ)"

# Check if Streamlit can access secrets (in cloud)
# This will be visible in the debug section of the app
```

### Error Resolution Status
- ✅ Solutions Architecture module - API key loading fixed
- ✅ User Story Generation module - API key loading fixed  
- ✅ Chat Assistant module - API key loading fixed
- ✅ Design QA module - Already working (uses different loading pattern)
- ✅ Functional Testing module - Already working

### Best Practices
1. **Local**: Use `.env` file with `load_dotenv()`
2. **Cloud**: Use Streamlit Cloud secrets configuration
3. **Fallback**: Each module checks both sources automatically
4. **Security**: Never commit API keys to git repositories
