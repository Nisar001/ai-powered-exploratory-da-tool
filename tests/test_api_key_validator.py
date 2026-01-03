"""
Tests for API Key Validation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.api_key_validator import (
    validate_google_api_key,
    validate_anthropic_api_key,
    validate_llm_apis,
)


@pytest.mark.asyncio
async def test_validate_google_api_key_empty():
    """Test validation with empty API key"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.google_api_key = ""
        is_valid, message = await validate_google_api_key()
        assert is_valid is False
        assert "not configured" in message


@pytest.mark.asyncio
async def test_validate_google_api_key_invalid():
    """Test validation with invalid API key"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.google_api_key = "invalid-key"
        
        with patch("src.core.api_key_validator.genai.configure") as mock_configure:
            with patch("src.core.api_key_validator.genai.GenerativeModel") as mock_model:
                mock_configure.return_value = None
                mock_model.side_effect = ValueError("API key is invalid")
                
                is_valid, message = await validate_google_api_key()
                assert is_valid is False
                assert "invalid" in message.lower()


@pytest.mark.asyncio
async def test_validate_google_api_key_success():
    """Test validation with valid API key"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.google_api_key = "valid-key"
        
        with patch("src.core.api_key_validator.genai.configure") as mock_configure:
            with patch("src.core.api_key_validator.genai.GenerativeModel") as mock_model:
                # Mock successful response
                mock_instance = MagicMock()
                mock_model.return_value = mock_instance
                mock_response = MagicMock()
                mock_response.text = "OK"
                mock_instance.generate_content.return_value = mock_response
                
                is_valid, message = await validate_google_api_key()
                assert is_valid is True
                assert "valid" in message.lower()


@pytest.mark.asyncio
async def test_validate_anthropic_api_key_empty():
    """Test validation with empty Anthropic API key"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.anthropic_api_key = ""
        is_valid, message = await validate_anthropic_api_key()
        assert is_valid is False
        assert "not configured" in message


@pytest.mark.asyncio
async def test_validate_anthropic_api_key_success():
    """Test validation with valid Anthropic API key"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.anthropic_api_key = "sk-ant-valid-key"
        
        with patch("src.core.api_key_validator.Anthropic") as mock_anthropic:
            # Mock successful response
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.models.list.return_value = MagicMock()
            
            is_valid, message = await validate_anthropic_api_key()
            assert is_valid is True
            assert "valid" in message.lower()


@pytest.mark.asyncio
async def test_validate_llm_apis_google_provider():
    """Test validate_llm_apis with Google as primary provider"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.llm_provider = "google"
        mock_settings.llm.google_api_key = "valid-key"
        mock_settings.llm.anthropic_api_key = ""
        
        with patch("src.core.api_key_validator.validate_google_api_key") as mock_validate_google:
            with patch("src.core.api_key_validator.validate_anthropic_api_key") as mock_validate_anthropic:
                mock_validate_google.return_value = (True, "✅ Google Gemini API key is valid")
                
                # Should not raise any exception
                await validate_llm_apis()
                
                mock_validate_google.assert_called_once()


@pytest.mark.asyncio
async def test_validate_llm_apis_anthropic_provider():
    """Test validate_llm_apis with Anthropic as primary provider"""
    with patch("src.core.api_key_validator.settings") as mock_settings:
        mock_settings.llm.llm_provider = "anthropic"
        mock_settings.llm.anthropic_api_key = "sk-ant-valid-key"
        mock_settings.llm.google_api_key = ""
        
        with patch("src.core.api_key_validator.validate_anthropic_api_key") as mock_validate_anthropic:
            with patch("src.core.api_key_validator.validate_google_api_key") as mock_validate_google:
                mock_validate_anthropic.return_value = (True, "✅ Anthropic API key is valid")
                
                # Should not raise any exception
                await validate_llm_apis()
                
                mock_validate_anthropic.assert_called_once()
