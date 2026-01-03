# API Reference Guide

## Base URL
```
Production: https://api.yourdomain.com
Development: http://localhost:8000
```

## Authentication
Currently, the API supports optional API key authentication. Set `API_KEY_ENABLED=true` in your environment configuration.

```bash
# With API key
curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/v1/..."
```

---

## Endpoints

### 1. File Upload

#### Upload CSV File
**Endpoint:** `POST /api/v1/upload/`

Upload a CSV file for analysis.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body:
  - `file` (required): CSV file
  - `description` (optional): File description

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@sales_data.csv" \
  -F "description=Q4 Sales Data"
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "sales_data.csv",
  "size_bytes": 2048576,
  "upload_timestamp": "2025-12-30T12:00:00.000Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type or validation error
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Upload processing failed

#### Get File Metadata
**Endpoint:** `GET /api/v1/upload/{file_id}`

Retrieve metadata for an uploaded file.

**Example:**
```bash
curl "http://localhost:8000/api/v1/upload/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "file_metadata": {
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "original_filename": "sales_data.csv",
    "size_bytes": 2048576,
    "size_mb": 1.95,
    "upload_timestamp": "2025-12-30T12:00:00.000Z"
  }
}
```

#### Delete File
**Endpoint:** `DELETE /api/v1/upload/{file_id}`

Delete an uploaded file and its metadata.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/upload/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "File a1b2c3d4-e5f6-7890-abcd-ef1234567890 deleted successfully"
}
```

---

### 2. Analysis

#### Trigger Analysis
**Endpoint:** `POST /api/v1/analyze/`

Start an EDA analysis job for an uploaded file.

**Request:**
```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "analysis_types": ["all"],
  "generate_insights": true,
  "generate_visualizations": true,
  "custom_config": {}
}
```

**Fields:**
- `file_id` (required): ID of uploaded file
- `analysis_types` (optional): Array of analysis types
  - `"all"` (default): All analysis types
  - `"descriptive"`: Descriptive statistics only
  - `"correlation"`: Correlation analysis only
  - `"distribution"`: Distribution analysis only
  - `"outlier"`: Outlier detection only
- `generate_insights` (optional): Generate AI insights (default: true)
- `generate_visualizations` (optional): Generate charts (default: true)
- `custom_config` (optional): Custom configuration overrides

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "analysis_types": ["all"],
    "generate_insights": true,
    "generate_visualizations": true
  }'
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "message": "Analysis job created successfully",
  "job_id": "job-uuid-12345",
  "status": "pending",
  "created_at": "2025-12-30T12:00:00.000Z",
  "estimated_completion": null
}
```

#### Get Job Status
**Endpoint:** `GET /api/v1/analyze/status/{job_id}`

Check the status of an analysis job.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analyze/status/job-uuid-12345"
```

**Response:** `200 OK`
```json
{
  "job_id": "job-uuid-12345",
  "status": "processing",
  "progress": 65.0,
  "created_at": "2025-12-30T12:00:00.000Z",
  "started_at": "2025-12-30T12:00:05.000Z",
  "completed_at": null,
  "error_message": null,
  "result_available": false
}
```

**Job Statuses:**
- `pending`: Job queued, not started
- `processing`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis failed
- `cancelled`: Job was cancelled

#### Get Analysis Results
**Endpoint:** `GET /api/v1/analyze/result/{job_id}`

Retrieve complete analysis results for a completed job.

**Example:**
```bash
curl "http://localhost:8000/api/v1/analyze/result/job-uuid-12345"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Analysis results retrieved successfully",
  "result": {
    "job_id": "job-uuid-12345",
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "dataset_schema": {
      "row_count": 10000,
      "column_count": 15,
      "columns": [...],
      "total_missing": 150,
      "memory_usage_mb": 12.5
    },
    "column_statistics": [...],
    "correlation_analysis": {...},
    "outlier_analysis": [...],
    "distribution_analysis": [...],
    "visualizations": [...],
    "ai_insights": {
      "executive_summary": "...",
      "key_findings": [...],
      "data_quality_assessment": "...",
      "insights": [...],
      "recommendations": [...]
    },
    "analysis_duration_seconds": 45.2,
    "completed_at": "2025-12-30T12:00:45.000Z"
  }
}
```

#### Delete Job
**Endpoint:** `DELETE /api/v1/analyze/{job_id}`

Cancel a running job or delete a completed job.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/analyze/job-uuid-12345"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Job job-uuid-12345 deleted successfully"
}
```

---

### 3. Health & Monitoring

#### Health Check
**Endpoint:** `GET /health`

Check API health and service availability.

**Example:**
```bash
curl "http://localhost:8000/health"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-30T12:00:00.000Z",
  "services": {
    "redis": true,
    "file_system": true
  },
  "details": {
    "environment": "production",
    "debug_mode": false
  }
}
```

#### Metrics
**Endpoint:** `GET /metrics`

Get application metrics (Prometheus-compatible).

**Example:**
```bash
curl "http://localhost:8000/metrics"
```

---

## Data Models

### AnalysisResult

Complete analysis result structure:

```json
{
  "job_id": "string",
  "file_id": "string",
  "dataset_schema": {
    "row_count": 0,
    "column_count": 0,
    "columns": [
      {
        "name": "string",
        "data_type": "numeric|categorical|datetime|text|boolean",
        "missing_count": 0,
        "missing_percentage": 0.0,
        "unique_count": 0,
        "sample_values": []
      }
    ],
    "total_missing": 0,
    "memory_usage_mb": 0.0
  },
  "column_statistics": [
    {
      "column_name": "string",
      "data_type": "numeric|categorical",
      "numeric_stats": {
        "mean": 0.0,
        "median": 0.0,
        "std_dev": 0.0,
        "min": 0.0,
        "max": 0.0,
        "q1": 0.0,
        "q3": 0.0,
        "skewness": 0.0,
        "kurtosis": 0.0,
        "outlier_count": 0
      },
      "categorical_stats": {
        "unique_count": 0,
        "most_frequent": "string",
        "frequency": 0,
        "frequency_distribution": {}
      }
    }
  ],
  "correlation_analysis": {
    "method": "pearson",
    "correlation_matrix": {},
    "strong_correlations": [
      {
        "column1": "string",
        "column2": "string",
        "correlation": 0.0,
        "strength": "strong|moderate|weak",
        "direction": "positive|negative"
      }
    ]
  },
  "outlier_analysis": [
    {
      "column_name": "string",
      "method": "iqr",
      "outlier_count": 0,
      "outlier_percentage": 0.0,
      "outlier_indices": []
    }
  ],
  "visualizations": [
    {
      "viz_id": "string",
      "viz_type": "histogram|boxplot|heatmap|bar_chart",
      "title": "string",
      "file_path": "string",
      "columns_used": [],
      "description": "string"
    }
  ],
  "ai_insights": {
    "executive_summary": "string",
    "key_findings": [],
    "data_quality_assessment": "string",
    "insights": [
      {
        "category": "string",
        "title": "string",
        "description": "string",
        "severity": "info|warning|critical",
        "affected_columns": []
      }
    ],
    "recommendations": []
  },
  "analysis_duration_seconds": 0.0,
  "completed_at": "2025-12-30T12:00:00.000Z"
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE",
    "details": {}
  }
}
```

### Common Error Codes

- `FILE_UPLOAD_ERROR`: File upload failed
- `DATA_PROCESSING_ERROR`: Data processing failed
- `ANALYSIS_ERROR`: Analysis execution failed
- `LLM_ERROR`: AI insight generation failed
- `JOB_ERROR`: Job management error
- `VALIDATION_ERROR`: Request validation failed
- `HTTP_ERROR`: HTTP-level error

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File too large
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

Default rate limits:
- 10 requests per second per IP
- Burst allowance: 20 requests

Rate limit headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1640000000
```

---

## Webhooks (Future)

Future support for webhooks to notify when analysis completes:

```json
{
  "url": "https://your-app.com/webhook",
  "events": ["analysis.completed", "analysis.failed"]
}
```

---

## SDK Examples

### Python
```python
import requests

# Upload file
with open('data.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/upload/',
        files={'file': f}
    )
    file_id = response.json()['file_id']

# Trigger analysis
response = requests.post(
    'http://localhost:8000/api/v1/analyze/',
    json={
        'file_id': file_id,
        'analysis_types': ['all'],
        'generate_insights': True
    }
)
job_id = response.json()['job_id']

# Check status
response = requests.get(
    f'http://localhost:8000/api/v1/analyze/status/{job_id}'
)
print(response.json())
```

### JavaScript
```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/api/v1/upload/', {
  method: 'POST',
  body: formData
});
const { file_id } = await uploadResponse.json();

// Trigger analysis
const analysisResponse = await fetch('http://localhost:8000/api/v1/analyze/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file_id,
    analysis_types: ['all'],
    generate_insights: true
  })
});
const { job_id } = await analysisResponse.json();
```

---

## Interactive Documentation

Visit `/docs` for interactive Swagger UI documentation where you can:
- Explore all endpoints
- Test API calls directly
- View request/response schemas
- See example requests

Alternative: Visit `/redoc` for ReDoc documentation.
