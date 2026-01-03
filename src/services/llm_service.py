"""
LLM Service Integration

Handles AI-powered insight generation using LLM APIs with
retry logic, fallback mechanisms, and prompt engineering.
"""

import json
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from anthropic import Anthropic

from src.core.config import settings
from src.core.exceptions import (
    LLMAPIException,
    LLMRateLimitException,
    LLMTimeoutException,
)
from src.core.logging import get_logger
from src.models.schemas import AIInsights, AnalysisResult, InsightItem

logger = get_logger(__name__)


class LLMService:
    """
    Service for generating AI-powered insights using Large Language Models
    """

    def __init__(self):
        self.provider = settings.llm.llm_provider
        self.model = settings.llm.llm_model
        self.temperature = settings.llm.llm_temperature
        self.max_tokens = settings.llm.llm_max_tokens
        self.timeout = settings.llm.llm_timeout
        self.max_retries = settings.llm.llm_max_retries
        self.retry_delay = settings.llm.llm_retry_delay

        # Initialize clients
        if self.provider == "google":
            genai.configure(api_key=settings.llm.google_api_key)
            try:
                self.client = genai.GenerativeModel(self.model)
            except Exception as e:
                logger.warning(f"Model {self.model} not available, falling back to gemini-2.5-flash: {str(e)}")
                self.client = genai.GenerativeModel("models/gemini-2.5-flash")
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=settings.llm.anthropic_api_key)
        else:
            logger.warning(f"Unsupported LLM provider: {self.provider}")

    def generate_insights(self, analysis_result: Dict[str, Any]) -> AIInsights:
        """
        Generate comprehensive AI insights from analysis results

        Args:
            analysis_result: Dictionary containing analysis results

        Returns:
            AIInsights with natural language explanations
        """
        logger.info("Generating AI insights")

        try:
            # Prepare structured data for the prompt
            context = self._prepare_context(analysis_result)

            # Generate insights using LLM
            response = self._call_llm_with_retry(
                self._build_insights_prompt(context)
            )

            # Parse and structure the response
            insights = self._parse_insights_response(response)

            logger.info("AI insights generated successfully")
            return insights

        except Exception as e:
            logger.error(f"Failed to generate AI insights: {str(e)}", exc_info=True)
            raise LLMAPIException(f"Failed to generate insights: {str(e)}")

    def _prepare_context(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare condensed context for LLM prompt

        Args:
            analysis_result: Full analysis results

        Returns:
            Condensed context dictionary
        """
        context = {
            "dataset_overview": {
                "rows": analysis_result.get("dataset_schema", {}).get("row_count"),
                "columns": analysis_result.get("dataset_schema", {}).get(
                    "column_count"
                ),
                "total_missing": analysis_result.get("dataset_schema", {}).get(
                    "total_missing"
                ),
            },
            "column_summaries": [],
            "correlations": [],
            "outliers": [],
            "distributions": [],
        }

        # Add column summaries
        for col_stat in analysis_result.get("column_statistics", [])[:10]:
            summary = {
                "name": col_stat.get("column_name"),
                "type": col_stat.get("data_type"),
            }

            if col_stat.get("numeric_stats"):
                stats = col_stat["numeric_stats"]
                summary["stats"] = {
                    "mean": stats.get("mean"),
                    "median": stats.get("median"),
                    "std_dev": stats.get("std_dev"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "outliers": stats.get("outlier_count"),
                    "skewness": stats.get("skewness"),
                }

            if col_stat.get("categorical_stats"):
                stats = col_stat["categorical_stats"]
                summary["stats"] = {
                    "unique_count": stats.get("unique_count"),
                    "most_frequent": stats.get("most_frequent"),
                }

            context["column_summaries"].append(summary)

        # Add strong correlations
        if analysis_result.get("correlation_analysis"):
            context["correlations"] = analysis_result["correlation_analysis"].get(
                "strong_correlations", []
            )[:10]

        # Add outlier information
        for outlier in analysis_result.get("outlier_analysis", [])[:10]:
            if outlier.get("outlier_count", 0) > 0:
                context["outliers"].append(
                    {
                        "column": outlier.get("column_name"),
                        "count": outlier.get("outlier_count"),
                        "percentage": outlier.get("outlier_percentage"),
                    }
                )

        # Add distribution information
        for dist in analysis_result.get("distribution_analysis", [])[:10]:
            context["distributions"].append(
                {
                    "column": dist.get("column_name"),
                    "type": dist.get("distribution_type"),
                    "is_normal": dist.get("is_normal"),
                }
            )

        return context

    def _build_insights_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build comprehensive prompt for insight generation

        Args:
            context: Prepared context dictionary

        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are an expert data scientist analyzing a dataset. Based on the statistical analysis results provided, generate comprehensive insights in a structured format.

Dataset Overview:
- Total Rows: {context['dataset_overview']['rows']}
- Total Columns: {context['dataset_overview']['columns']}
- Missing Values: {context['dataset_overview']['total_missing']}

Column Summaries:
{json.dumps(context['column_summaries'], indent=2)}

Strong Correlations:
{json.dumps(context['correlations'], indent=2)}

Outliers Detected:
{json.dumps(context['outliers'], indent=2)}

Distribution Analysis:
{json.dumps(context['distributions'], indent=2)}

Please provide:
1. Executive Summary: A brief 2-3 sentence overview of the dataset
2. Key Findings: 3-5 most important discoveries (as a JSON array of strings)
3. Data Quality Assessment: Overall assessment of data quality (1 paragraph)
4. Detailed Insights: Specific insights organized by category (as a JSON array with objects containing: category, title, description, severity, affected_columns)
5. Recommendations: 3-5 actionable recommendations (as a JSON array of strings)

Return your response in the following JSON format:
{{
    "executive_summary": "string",
    "key_findings": ["string"],
    "data_quality_assessment": "string",
    "insights": [
        {{
            "category": "string (e.g., 'data_quality', 'distribution', 'correlation', 'outliers')",
            "title": "string",
            "description": "string",
            "severity": "string (info, warning, or critical)",
            "affected_columns": ["string"]
        }}
    ],
    "recommendations": ["string"]
}}

Focus on actionable insights that would help someone understand and work with this data.
"""

        return prompt

    def _call_llm_with_retry(self, prompt: str) -> str:
        """
        Call LLM API with retry logic

        Args:
            prompt: Prompt to send to LLM

        Returns:
            LLM response text

        Raises:
            LLMAPIException: If all retries fail
            LLMTimeoutException: If request times out
            LLMRateLimitException: If rate limited
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"LLM API call attempt {attempt + 1}/{self.max_retries}")

                if self.provider == "google":
                    response = self._call_google(prompt)
                elif self.provider == "anthropic":
                    response = self._call_anthropic(prompt)
                else:
                    raise LLMAPIException(f"Unsupported provider: {self.provider}")

                return response

            except Exception as e:
                error_str = str(e).lower()
                
                # Handle rate limiting
                if "rate" in error_str or "quota" in error_str:
                    logger.warning(f"Rate limit hit on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise LLMRateLimitException()
                
                # Handle timeout
                elif "timeout" in error_str or "deadline" in error_str:
                    logger.warning(f"Timeout on attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise LLMTimeoutException(self.timeout)
                
                # Handle other errors
                else:
                    logger.error(f"LLM API error on attempt {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise LLMAPIException(f"LLM API call failed: {str(e)}")

    def _call_google(self, prompt: str) -> str:
        """
        Call Google Gemini API

        Args:
            prompt: Prompt to send

        Returns:
            Response text
        """
        try:
            response = self.client.generate_content(
                contents=prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
                stream=False,
            )

            if not response.text:
                raise LLMAPIException("Empty response from Google Gemini API")

            return response.text

        except Exception as e:
            raise LLMAPIException(f"Google Gemini API call failed: {str(e)}")

    def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API (DEPRECATED - Use Google Gemini instead)

        Args:
            prompt: Prompt to send

        Returns:
            Response text
        """
        raise LLMAPIException("OpenAI provider is deprecated. Use Google Gemini instead.")

    def _call_anthropic(self, prompt: str) -> str:
        """
        Call Anthropic API

        Args:
            prompt: Prompt to send

        Returns:
            Response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text

        except Exception as e:
            raise LLMAPIException(f"Anthropic API call failed: {str(e)}")

    def _parse_insights_response(self, response: str) -> AIInsights:
        """
        Parse LLM response into structured AIInsights

        Args:
            response: Raw LLM response

        Returns:
            Structured AIInsights object
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            response_clean = response_clean.strip()

            # Parse JSON
            data = json.loads(response_clean)

            # Convert insights to InsightItem objects
            insights = [
                InsightItem(
                    category=item.get("category", "general"),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    severity=item.get("severity", "info"),
                    affected_columns=item.get("affected_columns", []),
                )
                for item in data.get("insights", [])
            ]

            return AIInsights(
                executive_summary=data.get("executive_summary", ""),
                key_findings=data.get("key_findings", []),
                data_quality_assessment=data.get("data_quality_assessment", ""),
                insights=insights,
                recommendations=data.get("recommendations", []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return fallback insights
            return self._create_fallback_insights(response)

        except Exception as e:
            logger.error(f"Failed to structure insights: {str(e)}")
            return self._create_fallback_insights(response)

    def _create_fallback_insights(self, raw_response: str) -> AIInsights:
        """
        Create fallback insights when parsing fails

        Args:
            raw_response: Raw LLM response

        Returns:
            Basic AIInsights object
        """
        return AIInsights(
            executive_summary="Analysis completed with limited insight generation.",
            key_findings=["Statistical analysis completed successfully"],
            data_quality_assessment="Data quality metrics have been calculated.",
            insights=[
                InsightItem(
                    category="general",
                    title="Analysis Complete",
                    description=raw_response[:500] if raw_response else "See detailed statistics for more information.",
                    severity="info",
                    affected_columns=[],
                )
            ],
            recommendations=[
                "Review the statistical analysis results",
                "Examine visualizations for patterns",
            ],
        )

    def test_connection(self) -> bool:
        """
        Test LLM API connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Testing {self.provider} API connection")

            test_prompt = "Respond with 'OK' if you receive this message."

            response = self._call_llm_with_retry(test_prompt)

            logger.info(f"{self.provider} API connection test successful")
            return True

        except Exception as e:
            logger.error(f"{self.provider} API connection test failed: {str(e)}")
            return False
