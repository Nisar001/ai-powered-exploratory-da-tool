"""
API Key Validation Utilities

Provides functions to validate LLM API keys at startup
"""

import time
from typing import Tuple

import google.generativeai as genai
from anthropic import Anthropic

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


async def validate_google_api_key() -> Tuple[bool, str]:
    """
    Validate Google Gemini API key by making a test API call
    
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not settings.llm.google_api_key or settings.llm.google_api_key.strip() == "":
        return False, "❌ Google Gemini API key is not configured (empty)"
    
    try:
        # Configure the API key
        genai.configure(api_key=settings.llm.google_api_key)
        
        # Try the configured model first, fall back to gemini-2.5-flash if not available
        model_name = settings.llm.llm_model
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, respond with 'OK'")
        except Exception as e:
            # Fallback to gemini-2.5-flash for older configs
            logger.debug(f"Model {model_name} failed, trying fallback model: {str(e)}")
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content("Hello, respond with 'OK'")
        
        if response.text:
            logger.info("✅ Google Gemini API key validation successful")
            return True, "✅ Google Gemini API key is valid and working"
        else:
            error_msg = "❌ Google Gemini API returned empty response"
            logger.warning(error_msg)
            return False, error_msg
    
    except ValueError as e:
        if "API key" in str(e):
            error_msg = f"❌ Google Gemini API key is invalid: {str(e)}"
        else:
            error_msg = f"❌ Google Gemini API validation error: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"❌ Google Gemini API validation error: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg


async def validate_anthropic_api_key() -> Tuple[bool, str]:
    """
    Validate Anthropic API key by making a test API call
    
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    if not settings.llm.anthropic_api_key or settings.llm.anthropic_api_key.strip() == "":
        return False, "⚠️  Anthropic API key is not configured (empty)"
    
    try:
        # Create client to validate the key
        client = Anthropic(api_key=settings.llm.anthropic_api_key)
        
        # Make a minimal test call to validate the key
        response = client.models.list()
        
        logger.info("✅ Anthropic API key validation successful")
        return True, "✅ Anthropic API key is valid and working"
    
    except Exception as e:
        error_msg = f"❌ Anthropic API key validation error: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg


async def validate_llm_apis() -> None:
    """
    Validate all configured LLM API keys at startup
    Logs results but doesn't block startup
    """
    logger.info("=" * 60)
    logger.info("🔐 LLM API Key Validation")
    logger.info("=" * 60)
    
    # Check primary provider
    provider = settings.llm.llm_provider.lower()
    
    if provider == "google":
        is_valid, message = await validate_google_api_key()
        logger.info(message)
        
        # Also check Anthropic as fallback if configured
        if settings.llm.anthropic_api_key and settings.llm.anthropic_api_key.strip():
            is_valid_anthropic, message_anthropic = await validate_anthropic_api_key()
            logger.info(message_anthropic)
    
    elif provider == "anthropic":
        is_valid, message = await validate_anthropic_api_key()
        logger.info(message)
        
        # Also check Google as fallback if configured
        if settings.llm.google_api_key and settings.llm.google_api_key.strip():
            is_valid_google, message_google = await validate_google_api_key()
            logger.info(message_google)
    
    else:
        logger.warning(f"⚠️  Unknown LLM provider: {provider}")
    
    logger.info("=" * 60)
