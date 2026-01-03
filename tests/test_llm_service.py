from src.services.llm_service import LLMService


def test_llm_service_parses_valid_json(monkeypatch):
    service = LLMService()

    payload = {
        "dataset_schema": {"row_count": 10, "column_count": 2, "total_missing": 0},
        "column_statistics": [],
        "correlation_analysis": None,
        "outlier_analysis": [],
        "distribution_analysis": [],
    }

    fake_response = """
    {
        "executive_summary": "Sample summary",
        "key_findings": ["Finding 1", "Finding 2"],
        "data_quality_assessment": "Good",
        "insights": [
            {"category": "data_quality", "title": "T", "description": "D", "severity": "info", "affected_columns": []}
        ],
        "recommendations": ["Do X"]
    }
    """

    monkeypatch.setattr(service, "_call_llm_with_retry", lambda prompt: fake_response)

    insights = service.generate_insights(payload)

    assert insights.executive_summary == "Sample summary"
    assert insights.key_findings
    assert insights.recommendations
