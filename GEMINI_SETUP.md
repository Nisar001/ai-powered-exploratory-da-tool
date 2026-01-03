# Google Gemini API Setup Guide

This application has been successfully migrated from OpenAI to **Google Gemini API**, which offers:

- ✅ **FREE** to use with generous usage limits
- ✅ High-quality AI insights for data analysis
- ✅ Fast API responses
- ✅ No credit card required for free tier

## Getting Your Free Google Gemini API Key

### Step 1: Access Google AI Studio
1. Open your browser and go to: **https://aistudio.google.com/app/apikey**
2. Click **"Get API Key"** button
3. Select **"Create API Key in new project"** (or existing project)

### Step 2: Copy Your API Key
- Google will generate a unique API key
- Copy the key (you'll see a "Copy" button)
- **Important:** Keep this key private and secure

### Step 3: Configure Your Application

#### Option A: Using .env file (Recommended for Local Development)
1. Open the `.env` file in the project root
2. Find the line: `GOOGLE_API_KEY="your-gemini-api-key"`
3. Replace `"your-gemini-api-key"` with your actual API key

Example:
```env
GOOGLE_API_KEY="AIzaSyDxQxZzYn7gZ2p5rX3mQ9jX8yN4aB6cD5eF"
```

#### Option B: Using Environment Variables (Recommended for Production)
```bash
# Linux/Mac
export GOOGLE_API_KEY="your-api-key-here"

# Windows PowerShell
$env:GOOGLE_API_KEY="your-api-key-here"

# Windows Command Prompt
set GOOGLE_API_KEY=your-api-key-here
```

## Verify Configuration

### Check API Key Validity
The application automatically validates your API key on startup. You'll see logs like:

```
============================================================
🔐 LLM API Key Validation
============================================================
✅ Google Gemini API key is valid and working
============================================================
```

### Test with Python
```python
# Run this in Python to verify setup
import google.generativeai as genai

genai.configure(api_key="your-api-key-here")
model = genai.GenerativeModel('models/gemini-2.5-flash')
response = model.generate_content("Test message")
print(response.text)
```

## Running the Application

### 1. Start Redis (if using Celery background tasks)
```bash
redis-cli
# Or on Windows with WSL2/Docker:
docker run -d -p 6379:6379 redis:latest
```

### 2. Start Uvicorn Server
```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. (Optional) Start Celery Worker for Background Jobs
```bash
celery -A src.tasks.celery_app worker -l info
```

### 4. Upload and Analyze Data
Use the API endpoints:
- **POST** `/api/v1/analyze` - Upload CSV and get AI-powered analysis
- **GET** `/api/v1/job/{job_id}/status` - Check job status
- **GET** `/api/v1/job/{job_id}/results` - Get analysis results

## API Usage Limits (Google Gemini Free)

As of January 2024:
- **Requests per minute:** 60 RPM
- **Tokens per minute:** 4,000,000 TPM
- **Monthly limit:** None specified (free tier)

See latest limits at: https://ai.google.dev/pricing

## Troubleshooting

### "API key is invalid"
- ✅ Verify the key is correctly copied from aistudio.google.com
- ✅ Check for extra spaces before/after the key
- ✅ Ensure `.env` file has proper format: `GOOGLE_API_KEY="your-key"`

### "Rate limit exceeded"
- Application automatically retries with exponential backoff
- Check Google AI Studio quotas at https://console.cloud.google.com/

### "Empty response from API"
- Model may be overloaded temporarily
- Application will retry automatically
- Check logs for detailed error messages

## Models Available

Current setup uses: **`models/gemini-2.5-flash`** (Latest Gemini 2.5 API)

Other available models:
- `models/gemini-2.5-pro` - More capable model (update LLM_MODEL in .env)
- `models/gemini-2.0-flash` - Fast and versatile
- `models/gemini-flash-latest` - Always uses the latest flash model

**Note**: Older model names like `gemini-1.5-pro` and `gemini-pro` are deprecated.
Use the `models/` prefix for all new implementations.

## Configuration File Reference

In `.env`:
```env
# LLM Configuration - Google Gemini (FREE API)
LLM_PROVIDER="google"                       # Primary AI provider
GOOGLE_API_KEY="your-gemini-api-key"       # Your free API key
LLM_MODEL="models/gemini-2.5-flash"        # Model to use (Gemini 2.5)
LLM_TEMPERATURE=0.3                         # Response creativity (0-1)
LLM_MAX_TOKENS=2000                         # Max response length
LLM_TIMEOUT=60                              # Request timeout (seconds)
LLM_MAX_RETRIES=3                           # Retry attempts
LLM_RETRY_DELAY=2                           # Delay between retries
```

## Next Steps

1. ✅ Obtain Google Gemini API key from https://aistudio.google.com/app/apikey
2. ✅ Update `.env` with your API key
3. ✅ Run tests: `pytest tests/ -v`
4. ✅ Start the server: `uvicorn src.main:app --reload`
5. ✅ Use Postman or curl to test the API

## Need Help?

- Google Generative AI Python Docs: https://github.com/google-gemini/generative-ai-python
- Google AI Studio: https://aistudio.google.com/
- API Reference: https://ai.google.dev/api
