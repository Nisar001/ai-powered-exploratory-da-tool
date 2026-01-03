# 🚀 AI-Powered Exploratory Data Analysis Platform

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-success.svg)

**Enterprise-grade Exploratory Data Analysis platform powered by AI**

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [Examples](#-usage-examples) • [Deployment](#-docker-deployment)

</div>

---

## 📋 Overview

A production-ready, scalable platform for automated exploratory data analysis (EDA) with AI-powered insights. Built with modern async architecture, this platform provides comprehensive statistical analysis, intelligent visualizations, and natural language insights powered by Google Gemini AI.

### 🎯 Key Benefits

- **⚡ Fast & Scalable**: Async processing with Celery for background jobs
- **🤖 AI-Powered**: Google Gemini integration for intelligent insights (FREE tier available)
- **📊 Comprehensive**: Complete statistical analysis, correlation, outlier detection, and more
- **🔒 Production-Ready**: Security, monitoring, error handling, and Redis caching
- **🐳 Docker Support**: Full containerization with Docker Compose
- **📈 Real-Time Progress**: WebSocket-ready architecture for live updates
- **🎨 Auto Visualizations**: Automatic generation of publication-quality charts

---

## ✨ Features

### Core Capabilities
- 📤 **Secure File Upload**: CSV file validation, size limits, and unique ID generation
- 📊 **Statistical Analysis**: Descriptive stats, correlation analysis, distribution tests
- 🔍 **Outlier Detection**: IQR and Z-score based outlier identification
- 📉 **Trend Analysis**: Time-series pattern detection and seasonality analysis
- 🎨 **Smart Visualizations**: Automatic chart generation (histograms, scatter plots, heatmaps)
- 🤖 **AI Insights**: Natural language summaries and recommendations
- ⚡ **Background Processing**: Async job execution with progress tracking
- 💾 **Redis Caching**: Fast metadata and result retrieval
- 🔐 **API Security**: Optional API key authentication
- 📝 **Comprehensive Logging**: Structured JSON logging with context

### Analysis Types
- **Descriptive Statistics**: Mean, median, mode, std dev, quartiles, skewness, kurtosis
- **Correlation Analysis**: Pearson, Spearman, and Kendall correlation matrices
- **Distribution Analysis**: Normality tests, distribution fitting
- **Outlier Detection**: Multiple methods (IQR, Z-score, Isolation Forest)
- **Missing Data Analysis**: Detection and impact assessment
- **Data Quality Scoring**: Automated data quality metrics

---

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | FastAPI 0.109, Python 3.11+, Uvicorn, Gunicorn |
| **Data Processing** | Pandas 2.1, NumPy 1.26, SciPy 1.11 |
| **Visualization** | Matplotlib 3.8, Seaborn 0.13, Plotly 5.18 |
| **AI/LLM** | Google Gemini (FREE), Anthropic Claude, LangChain |
| **Background Jobs** | Celery 5.3, Redis 4.5+ |
| **Caching** | Redis, Aioredis |
| **Database** | SQLAlchemy 2.0, PostgreSQL, SQLite |
| **HTTP/Async** | HTTPX, Aiofiles |
| **Monitoring** | Prometheus, Sentry, Python-JSON-Logger |
| **Security** | Python-JOSE, Passlib, Bcrypt |
| **Containerization** | Docker, Docker Compose, Nginx |

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11 or higher
- Redis server (or Docker)
- 2GB+ RAM recommended
- Google Gemini API key (FREE at https://makersuite.google.com/app/apikey)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ai-powered-exploratory-da-tool

# Create environment file
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://redis:6379/0
APP_ENV=production
LOG_LEVEL=INFO
EOF

# Start all services
docker-compose up -d

# Check health
curl http://localhost/health
```

Services will be available at:
- API: `http://localhost` (via Nginx)
- API Docs: `http://localhost/docs`
- Flower (Celery Monitor): `http://localhost:5555`

### Option 2: Local Development

```bash
# Clone and navigate
git clone <repository-url>
cd ai-powered-exploratory-da-tool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/uploads data/results data/temp logs

# Configure environment
cat > .env << EOF
GOOGLE_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
EOF

# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)
celery -A src.core.celery_app worker --loglevel=info

# Start FastAPI server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit: `http://localhost:8000/docs` for interactive API documentation

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Optional API key authentication via header:
```http
X-API-Key: your_api_key_here
```

---

## 📡 Endpoints

### 1. Health Check

#### `GET /health`

Check the health status of the API and its dependencies.

**Response: 200 OK**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-03T12:00:00",
  "services": {
    "redis": true,
    "file_system": true,
    "celery": true
  },
  "details": {
    "uptime_seconds": 3600,
    "active_jobs": 5
  }
}
```

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/health"
```

---

### 2. Upload CSV File

#### `POST /api/v1/upload/`

Upload a CSV file for analysis with automatic validation and secure storage.

**Request Parameters:**
- `file` (form-data, **required**): CSV file to upload
- `description` (form-data, optional): Description of the file

**Validation Rules:**
- File type: `.csv` only
- Max size: 100MB (configurable)
- Automatic virus scanning (if enabled)
- Unique file ID generation

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/data.csv" \
  -F "description=Sales data Q4 2025"
```

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/api/v1/upload/"
files = {"file": open("data.csv", "rb")}
data = {"description": "Sales data Q4 2025"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Response: 201 Created**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "data.csv",
  "size_bytes": 1048576,
  "upload_timestamp": "2026-01-03T12:00:00",
  "timestamp": "2026-01-03T12:00:00"
}
```

**Error Responses:**

**400 Bad Request** - Invalid file type:
```json
{
  "error": {
    "message": "Invalid file type: .xlsx. Allowed types: ['.csv']",
    "code": "INVALID_FILE_TYPE"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

**413 Payload Too Large** - File too large:
```json
{
  "error": {
    "message": "File size 150.5MB exceeds maximum allowed size of 100MB",
    "code": "FILE_SIZE_EXCEEDED"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 3. Get File Metadata

#### `GET /api/v1/upload/{file_id}`

Retrieve metadata for an uploaded file.

**Path Parameters:**
- `file_id` (string, **required**): Unique file identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/upload/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response: 200 OK**
```json
{
  "success": true,
  "file_metadata": {
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "original_filename": "data.csv",
    "stored_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890_20260103_120000.csv",
    "file_path": "/app/data/uploads/a1b2c3d4-e5f6-7890-abcd-ef1234567890_20260103_120000.csv",
    "size_bytes": 1048576,
    "size_mb": 1.0,
    "description": "Sales data Q4 2025",
    "upload_timestamp": "2026-01-03T12:00:00",
    "content_type": "text/csv"
  }
}
```

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "File a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 4. Delete Uploaded File

#### `DELETE /api/v1/upload/{file_id}`

Delete an uploaded file and its metadata permanently.

**Path Parameters:**
- `file_id` (string, **required**): Unique file identifier

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/upload/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "File a1b2c3d4-e5f6-7890-abcd-ef1234567890 deleted successfully"
}
```

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "File a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 5. Trigger Analysis

#### `POST /api/v1/analyze/`

Start a background EDA analysis job for an uploaded file.

**Request Body:**
```json
{
  "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "analysis_types": ["descriptive", "correlation", "outlier", "distribution"],
  "generate_insights": true,
  "generate_visualizations": true,
  "custom_config": {
    "correlation_method": "pearson",
    "outlier_method": "iqr"
  }
}
```

**Request Parameters:**
- `file_id` (string, **required**): ID of uploaded file
- `analysis_types` (array, optional): Types of analysis to perform
  - Options: `"descriptive"`, `"correlation"`, `"distribution"`, `"outlier"`, `"trend"`, `"all"`
  - Default: `["all"]`
- `generate_insights` (boolean, optional): Generate AI insights (default: `true`)
- `generate_visualizations` (boolean, optional): Create charts (default: `true`)
- `custom_config` (object, optional): Custom analysis configuration

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "analysis_types": ["descriptive", "correlation"],
    "generate_insights": true,
    "generate_visualizations": true
  }'
```

**Example Request (Python):**
```python
import requests

url = "http://localhost:8000/api/v1/analyze/"
payload = {
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "analysis_types": ["all"],
    "generate_insights": True,
    "generate_visualizations": True
}

response = requests.post(url, json=payload)
result = response.json()
job_id = result["job_id"]
print(f"Analysis started: {job_id}")
```

**Response: 202 Accepted**
```json
{
  "success": true,
  "message": "Analysis job created successfully",
  "job_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "pending",
  "created_at": "2026-01-03T12:00:00",
  "estimated_completion": "2026-01-03T12:05:00",
  "timestamp": "2026-01-03T12:00:00"
}
```

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "File a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 6. Check Analysis Status

#### `GET /api/v1/analyze/status/{job_id}`

Check the status and progress of an analysis job.

**Path Parameters:**
- `job_id` (string, **required**): Unique job identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analyze/status/f9e8d7c6-b5a4-3210-9876-543210fedcba"
```

**Example Request (Python - Polling):**
```python
import requests
import time

job_id = "f9e8d7c6-b5a4-3210-9876-543210fedcba"
url = f"http://localhost:8000/api/v1/analyze/status/{job_id}"

while True:
    response = requests.get(url)
    data = response.json()
    
    print(f"Status: {data['status']} - Progress: {data['progress']}%")
    
    if data["status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)  # Poll every 2 seconds
```

**Response: 200 OK (Processing)**
```json
{
  "job_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "processing",
  "progress": 45.5,
  "created_at": "2026-01-03T12:00:00",
  "started_at": "2026-01-03T12:00:05",
  "completed_at": null,
  "error_message": null,
  "result_available": false
}
```

**Response: 200 OK (Completed)**
```json
{
  "job_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "completed",
  "progress": 100.0,
  "created_at": "2026-01-03T12:00:00",
  "started_at": "2026-01-03T12:00:05",
  "completed_at": "2026-01-03T12:04:30",
  "error_message": null,
  "result_available": true
}
```

**Response: 200 OK (Failed)**
```json
{
  "job_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "status": "failed",
  "progress": 65.0,
  "created_at": "2026-01-03T12:00:00",
  "started_at": "2026-01-03T12:00:05",
  "completed_at": "2026-01-03T12:03:00",
  "error_message": "Failed to parse CSV: Invalid column names",
  "result_available": false
}
```

**Status Values:**
- `pending`: Job queued, not started
- `processing`: Job currently running
- `completed`: Job finished successfully
- `failed`: Job encountered an error
- `cancelled`: Job was cancelled by user

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "Job f9e8d7c6-b5a4-3210-9876-543210fedcba not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 7. Get Analysis Results

#### `GET /api/v1/analyze/result/{job_id}`

Retrieve complete analysis results for a completed job.

**Path Parameters:**
- `job_id` (string, **required**): Unique job identifier

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/analyze/result/f9e8d7c6-b5a4-3210-9876-543210fedcba"
```

**Example Request (Python):**
```python
import requests

job_id = "f9e8d7c6-b5a4-3210-9876-543210fedcba"
url = f"http://localhost:8000/api/v1/analyze/result/{job_id}"

response = requests.get(url)
results = response.json()

# Access specific parts
dataset_info = results["result"]["dataset_schema"]
statistics = results["result"]["column_statistics"]
ai_insights = results["result"]["ai_insights"]

print(f"Analyzed {dataset_info['row_count']} rows")
print(f"AI Summary: {ai_insights['executive_summary']}")
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Analysis results retrieved successfully",
  "timestamp": "2026-01-03T12:05:00",
  "result": {
    "job_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "dataset_schema": {
      "row_count": 10000,
      "column_count": 15,
      "columns": [
        {
          "name": "customer_id",
          "data_type": "numeric",
          "missing_count": 0,
          "missing_percentage": 0.0,
          "unique_count": 10000,
          "sample_values": [1001, 1002, 1003, 1004, 1005]
        },
        {
          "name": "purchase_amount",
          "data_type": "numeric",
          "missing_count": 150,
          "missing_percentage": 1.5,
          "unique_count": 8750,
          "sample_values": [49.99, 129.95, 89.50, 199.99, 75.00]
        }
      ],
      "total_missing": 450,
      "memory_usage_mb": 2.5
    },
    "column_statistics": [
      {
        "column_name": "purchase_amount",
        "data_type": "numeric",
        "numeric_stats": {
          "mean": 95.45,
          "median": 89.99,
          "mode": 49.99,
          "std_dev": 35.20,
          "variance": 1239.04,
          "min": 10.00,
          "max": 500.00,
          "q1": 65.00,
          "q3": 125.00,
          "iqr": 60.00,
          "skewness": 0.85,
          "kurtosis": 2.15,
          "outlier_count": 127
        },
        "categorical_stats": null
      },
      {
        "column_name": "product_category",
        "data_type": "categorical",
        "numeric_stats": null,
        "categorical_stats": {
          "unique_count": 5,
          "most_frequent": "Electronics",
          "frequency": 3500,
          "frequency_distribution": {
            "Electronics": 3500,
            "Clothing": 2800,
            "Home": 2000,
            "Sports": 1200,
            "Books": 500
          }
        }
      }
    ],
    "correlation_analysis": {
      "method": "pearson",
      "correlation_matrix": {
        "purchase_amount": {
          "purchase_amount": 1.0,
          "customer_age": 0.42,
          "loyalty_score": 0.68
        },
        "customer_age": {
          "purchase_amount": 0.42,
          "customer_age": 1.0,
          "loyalty_score": 0.31
        }
      },
      "strong_correlations": [
        {
          "column1": "purchase_amount",
          "column2": "loyalty_score",
          "correlation": 0.68,
          "strength": "moderate"
        }
      ]
    },
    "outlier_analysis": [
      {
        "column_name": "purchase_amount",
        "method": "iqr",
        "outlier_count": 127,
        "outlier_percentage": 1.27,
        "outlier_indices": [45, 123, 456, 789, 1024]
      }
    ],
    "distribution_analysis": [
      {
        "column_name": "purchase_amount",
        "distribution_type": "normal",
        "is_normal": true,
        "normality_test_statistic": 0.985,
        "normality_p_value": 0.08
      }
    ],
    "visualizations": [
      {
        "viz_id": "hist_purchase_amount",
        "viz_type": "histogram",
        "title": "Distribution of Purchase Amount",
        "file_path": "/app/data/results/f9e8d7c6_histogram_purchase_amount.png",
        "columns_used": ["purchase_amount"],
        "description": "Histogram showing the distribution of purchase amounts"
      },
      {
        "viz_id": "corr_heatmap",
        "viz_type": "heatmap",
        "title": "Correlation Matrix Heatmap",
        "file_path": "/app/data/results/f9e8d7c6_correlation_heatmap.png",
        "columns_used": ["purchase_amount", "customer_age", "loyalty_score"],
        "description": "Heatmap of correlations between numeric columns"
      }
    ],
    "ai_insights": {
      "executive_summary": "This dataset contains 10,000 customer purchase records with 15 features. The data quality is excellent with minimal missing values (0.45%). Purchase amounts show a normal distribution with mean $95.45 and strong positive correlation (0.68) with customer loyalty scores.",
      "key_findings": [
        "Electronics is the most popular product category (35% of purchases)",
        "Strong correlation between loyalty score and purchase amount indicates effective loyalty program",
        "127 outliers detected in purchase amounts, likely bulk orders or premium products",
        "Customer age shows moderate positive correlation (0.42) with purchase amount"
      ],
      "data_quality_assessment": "High quality dataset with <2% missing values, no duplicate records, and consistent data types. All numeric columns are within expected ranges.",
      "insights": [
        {
          "category": "Data Quality",
          "title": "Minimal Missing Data",
          "description": "Only 1.5% of purchase_amount values are missing, indicating good data collection practices.",
          "severity": "info",
          "affected_columns": ["purchase_amount"]
        },
        {
          "category": "Business Insight",
          "title": "Loyalty Program Effectiveness",
          "description": "Strong positive correlation (0.68) between loyalty score and purchase amount suggests the loyalty program is successfully driving higher spending.",
          "severity": "info",
          "affected_columns": ["loyalty_score", "purchase_amount"]
        },
        {
          "category": "Outlier Detection",
          "title": "High-Value Transactions",
          "description": "127 outliers detected in purchase amounts (1.27% of data). These may represent bulk orders or premium products worth investigating.",
          "severity": "warning",
          "affected_columns": ["purchase_amount"]
        }
      ],
      "recommendations": [
        "Consider targeted marketing campaigns for Electronics category to maintain market leadership",
        "Investigate outlier transactions to identify potential bulk buyer opportunities",
        "Enhance loyalty program benefits to further strengthen purchase amount correlation",
        "Analyze age demographics to create age-specific product recommendations"
      ],
      "generated_at": "2026-01-03T12:04:25"
    },
    "analysis_duration_seconds": 265.5,
    "completed_at": "2026-01-03T12:04:30"
  }
}
```

**Error Response: 400 Bad Request (Not Completed)**
```json
{
  "error": {
    "message": "Job f9e8d7c6-b5a4-3210-9876-543210fedcba is not completed. Current status: processing"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "Job f9e8d7c6-b5a4-3210-9876-543210fedcba not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

**Error Response: 404 Not Found (Results Expired)**
```json
{
  "error": {
    "message": "Results for job f9e8d7c6-b5a4-3210-9876-543210fedcba not found or expired"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

### 8. Delete Analysis Job

#### `DELETE /api/v1/analyze/{job_id}`

Cancel a running job or delete a completed job and its results.

**Path Parameters:**
- `job_id` (string, **required**): Unique job identifier

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/analyze/f9e8d7c6-b5a4-3210-9876-543210fedcba"
```

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Job f9e8d7c6-b5a4-3210-9876-543210fedcba deleted successfully"
}
```

**Error Response: 404 Not Found**
```json
{
  "error": {
    "message": "Job f9e8d7c6-b5a4-3210-9876-543210fedcba not found"
  },
  "timestamp": "2026-01-03T12:00:00"
}
```

---

## 💡 Usage Examples

### Complete Analysis Workflow (Python)

```python
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def complete_analysis_workflow(csv_file_path: str):
    """Complete EDA workflow from upload to results"""
    
    # Step 1: Upload file
    print("📤 Uploading file...")
    with open(csv_file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload/",
            files={"file": f},
            data={"description": "Analysis test file"}
        )
    
    upload_result = response.json()
    file_id = upload_result["file_id"]
    print(f"✅ File uploaded: {file_id}")
    
    # Step 2: Trigger analysis
    print("🚀 Starting analysis...")
    response = requests.post(
        f"{BASE_URL}/analyze/",
        json={
            "file_id": file_id,
            "analysis_types": ["all"],
            "generate_insights": True,
            "generate_visualizations": True
        }
    )
    
    analysis_result = response.json()
    job_id = analysis_result["job_id"]
    print(f"✅ Analysis job created: {job_id}")
    
    # Step 3: Poll for completion
    print("⏳ Waiting for analysis to complete...")
    while True:
        response = requests.get(f"{BASE_URL}/analyze/status/{job_id}")
        status_data = response.json()
        
        status = status_data["status"]
        progress = status_data["progress"]
        
        print(f"   Status: {status} - Progress: {progress:.1f}%")
        
        if status == "completed":
            print("✅ Analysis completed!")
            break
        elif status == "failed":
            error = status_data.get("error_message", "Unknown error")
            print(f"❌ Analysis failed: {error}")
            return None
        
        time.sleep(3)
    
    # Step 4: Retrieve results
    print("📊 Fetching results...")
    response = requests.get(f"{BASE_URL}/analyze/result/{job_id}")
    results = response.json()
    
    # Step 5: Process results
    result_data = results["result"]
    dataset = result_data["dataset_schema"]
    ai_insights = result_data["ai_insights"]
    
    print(f"\n{'='*60}")
    print("📈 ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"📁 Dataset: {dataset['row_count']:,} rows × {dataset['column_count']} columns")
    print(f"💾 Memory: {dataset['memory_usage_mb']:.2f} MB")
    print(f"⏱️  Duration: {result_data['analysis_duration_seconds']:.1f}s")
    print(f"\n🤖 AI SUMMARY:")
    print(ai_insights['executive_summary'])
    print(f"\n💡 KEY FINDINGS:")
    for i, finding in enumerate(ai_insights['key_findings'], 1):
        print(f"  {i}. {finding}")
    print(f"\n🎯 RECOMMENDATIONS:")
    for i, rec in enumerate(ai_insights['recommendations'], 1):
        print(f"  {i}. {rec}")
    print(f"\n📊 VISUALIZATIONS:")
    for viz in result_data['visualizations']:
        print(f"  - {viz['title']} ({viz['viz_type']})")
    print(f"{'='*60}\n")
    
    return results

# Run the workflow
if __name__ == "__main__":
    results = complete_analysis_workflow("path/to/your/data.csv")
```

### Simple Upload and Analyze (cURL)

```bash
#!/bin/bash

# Upload file
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@data.csv" \
  -F "description=Test dataset")

FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')
echo "File uploaded: $FILE_ID"

# Start analysis
ANALYSIS_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analyze/" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_id\": \"$FILE_ID\",
    \"analysis_types\": [\"all\"],
    \"generate_insights\": true,
    \"generate_visualizations\": true
  }")

JOB_ID=$(echo $ANALYSIS_RESPONSE | jq -r '.job_id')
echo "Analysis job: $JOB_ID"

# Poll for completion
while true; do
  STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/analyze/status/$JOB_ID")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  PROGRESS=$(echo $STATUS_RESPONSE | jq -r '.progress')
  
  echo "Status: $STATUS - Progress: $PROGRESS%"
  
  if [ "$STATUS" = "completed" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Analysis failed!"
    exit 1
  fi
  
  sleep 3
done

# Get results
curl -s "http://localhost:8000/api/v1/analyze/result/$JOB_ID" | jq
```

### Async Analysis with Callbacks (Advanced)

```python
import asyncio
import aiohttp
from typing import Optional

class EDAClient:
    """Async client for EDA Platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    async def upload_file(self, file_path: str, description: Optional[str] = None):
        """Upload a CSV file"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("file", f, filename=file_path)
                if description:
                    data.add_field("description", description)
                
                async with session.post(f"{self.base_url}/upload/", data=data) as resp:
                    return await resp.json()
    
    async def start_analysis(self, file_id: str, **options):
        """Start analysis job"""
        async with aiohttp.ClientSession() as session:
            payload = {"file_id": file_id, **options}
            async with session.post(f"{self.base_url}/analyze/", json=payload) as resp:
                return await resp.json()
    
    async def get_status(self, job_id: str):
        """Get job status"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/analyze/status/{job_id}") as resp:
                return await resp.json()
    
    async def get_results(self, job_id: str):
        """Get analysis results"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/analyze/result/{job_id}") as resp:
                return await resp.json()
    
    async def wait_for_completion(self, job_id: str, callback=None):
        """Wait for job completion with optional progress callback"""
        while True:
            status_data = await self.get_status(job_id)
            status = status_data["status"]
            progress = status_data["progress"]
            
            if callback:
                callback(status, progress)
            
            if status in ["completed", "failed"]:
                return status_data
            
            await asyncio.sleep(2)

# Usage
async def main():
    client = EDAClient()
    
    # Upload
    upload_result = await client.upload_file("data.csv", "Async test")
    file_id = upload_result["file_id"]
    print(f"Uploaded: {file_id}")
    
    # Start analysis
    job_result = await client.start_analysis(
        file_id,
        analysis_types=["all"],
        generate_insights=True
    )
    job_id = job_result["job_id"]
    print(f"Job started: {job_id}")
    
    # Wait with progress callback
    def progress_callback(status, progress):
        print(f"Progress: {status} - {progress}%")
    
    final_status = await client.wait_for_completion(job_id, progress_callback)
    
    if final_status["status"] == "completed":
        results = await client.get_results(job_id)
        print("Analysis complete!")
        print(results["result"]["ai_insights"]["executive_summary"])

asyncio.run(main())
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application Settings
APP_NAME=AI-Powered EDA Platform
APP_VERSION=1.0.0
APP_ENV=production  # development, staging, production
DEBUG=False
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=4
SERVER_RELOAD=False

# AI/LLM Configuration (REQUIRED)
GOOGLE_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=optional_claude_api_key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TRACK_STARTED=True

# File Upload Settings
MAX_UPLOAD_SIZE_MB=100
ALLOWED_EXTENSIONS=.csv
UPLOAD_DIR=data/uploads
RESULTS_DIR=data/results
TEMP_DIR=data/temp

# Data Processing Limits
MAX_ROWS=1000000
MAX_COLUMNS=1000
CHUNK_SIZE=10000
NUMERIC_PRECISION=4

# Security
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=*  # Comma-separated for production: https://example.com,https://app.example.com
CORS_ENABLED=True
API_KEY_ENABLED=False  # Set to True for API key authentication
API_KEY=your-api-key-here

# Performance
BACKGROUND_TASKS_ENABLED=True
CACHE_ENABLED=True
CACHE_TTL_SECONDS=3600

# Monitoring (Optional)
SENTRY_DSN=
PROMETHEUS_ENABLED=False
```

### Configuration Files

**Docker Compose (`docker-compose.yml`):**
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery_worker:
    build: .
    command: celery -A src.core.celery_app worker --loglevel=info
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    depends_on:
      - redis

  api:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    depends_on:
      - redis
      - celery_worker

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api

  flower:
    build: .
    command: celery -A src.core.celery_app flower --port=5555
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
      - celery_worker

volumes:
  redis_data:
```

---

## 📁 Project Structure

```
ai-powered-exploratory-da-tool/
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes and middleware
│   │   ├── routes/
│   │   │   ├── health.py         # Health check endpoint
│   │   │   ├── upload.py         # File upload endpoints
│   │   │   └── analysis.py       # Analysis endpoints
│   │   ├── middleware.py         # Custom middleware
│   │   └── exception_handlers.py # Global exception handling
│   ├── core/                     # Core functionality
│   │   ├── config.py             # Configuration management
│   │   ├── logging.py            # Logging configuration
│   │   ├── redis_client.py       # Redis connection
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── api_key_validator.py  # API key authentication
│   │   └── exceptions.py         # Custom exceptions
│   ├── models/                   # Data models
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/                 # Business logic
│   │   ├── data_loader.py        # Data loading and validation
│   │   ├── statistical_analyzer.py # Statistical analysis
│   │   ├── visualization_engine.py # Chart generation
│   │   ├── llm_service.py        # AI/LLM integration
│   │   └── eda_orchestrator.py   # Analysis orchestration
│   └── tasks/                    # Background tasks
│       └── eda_tasks.py          # Celery tasks
├── tests/                        # Test suite
│   ├── conftest.py               # Pytest configuration
│   ├── test_api_routes.py        # API endpoint tests
│   ├── test_data_loader.py       # Data loading tests
│   ├── test_statistical_analyzer.py
│   └── test_llm_service.py
├── data/                         # Data directories
│   ├── uploads/                  # Uploaded files
│   ├── results/                  # Analysis results
│   └── temp/                     # Temporary files
├── logs/                         # Application logs
├── docs/                         # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── nginx/                        # Nginx configuration
│   └── nginx.conf
├── postman/                      # Postman collections
│   └── AI_Powered_EDA_Platform.postman_collection.json
├── .env.example                  # Environment template
├── .gitignore
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Docker Compose config
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

---

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api_routes.py -v

# Run with markers
pytest -m "not slow" -v
```

### Test API Endpoints

```bash
# Using Postman collection
# Import postman/AI_Powered_EDA_Platform.postman_collection.json

# Or use pytest
pytest tests/test_api_routes.py::test_health_check -v
pytest tests/test_api_routes.py::test_upload_file -v
pytest tests/test_api_routes.py::test_trigger_analysis -v
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with sample data
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@tests/fixtures/sample_data.csv"
```

---

## 🐳 Docker Deployment

### Quick Deploy

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production Deployment

```bash
# Set production environment
export APP_ENV=production
export DEBUG=False

# Build with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale celery_worker=4

# Monitor
docker-compose ps
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Health Checks

```bash
# Check all services
docker-compose ps

# Test API
curl http://localhost/health

# Check Redis
docker-compose exec redis redis-cli ping

# Check Celery workers
docker-compose exec celery_worker celery -A src.core.celery_app inspect active
```

---

## 🔒 Security Considerations

### Best Practices Implemented

- ✅ **Input Validation**: All file uploads and requests validated
- ✅ **File Type Restrictions**: Only CSV files allowed
- ✅ **Size Limits**: Configurable max upload size (default 100MB)
- ✅ **Unique File IDs**: UUID-based file identification
- ✅ **Secure File Storage**: Files stored with sanitized names
- ✅ **API Key Authentication**: Optional API key protection
- ✅ **CORS Configuration**: Configurable allowed origins
- ✅ **Error Handling**: No sensitive data in error messages
- ✅ **Redis Expiration**: Automatic cleanup of old data (7 days)
- ✅ **Rate Limiting Ready**: Infrastructure for rate limiting

### Recommended Production Security

```bash
# Enable API key authentication
API_KEY_ENABLED=True
API_KEY=your-secure-random-api-key

# Restrict CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Use strong secret key
SECRET_KEY=$(openssl rand -hex 32)

# Enable HTTPS (Nginx)
# Update nginx.conf with SSL certificates

# Use environment secrets
# Store sensitive data in secure vaults (AWS Secrets Manager, HashiCorp Vault)
```

---

## 📊 Performance Notes

### Optimization Features

- **Async I/O**: All API endpoints use async/await
- **Background Jobs**: Long-running analysis in Celery workers
- **Redis Caching**: Fast metadata and result retrieval
- **Chunked Processing**: Large files processed in chunks
- **Connection Pooling**: Redis and database connection reuse
- **Lazy Loading**: Results loaded on-demand

### Benchmarks

| Dataset Size | Rows | Columns | Analysis Time | Memory Usage |
|--------------|------|---------|---------------|--------------|
| Small | 1K | 10 | ~5s | ~50MB |
| Medium | 100K | 20 | ~30s | ~200MB |
| Large | 1M | 50 | ~3min | ~1GB |
| X-Large | 10M | 100 | ~20min | ~4GB |

**Note**: Times include AI insights generation. Disable for faster processing.

### Scaling Recommendations

```bash
# Scale Celery workers
docker-compose up -d --scale celery_worker=8

# Increase Redis memory
# Edit redis.conf: maxmemory 4gb

# Use Redis Cluster for high availability
# Enable sharding for large datasets
```

---

## 🗺️ Roadmap

### Version 1.1 (Q2 2026)
- [ ] WebSocket support for real-time progress updates
- [ ] Support for additional file formats (Excel, Parquet, JSON)
- [ ] Advanced time series analysis
- [ ] Custom visualization templates
- [ ] Export results to PDF/PowerPoint

### Version 1.2 (Q3 2026)
- [ ] Multi-file comparison analysis
- [ ] Interactive dashboards with Plotly Dash
- [ ] Machine learning model suggestions
- [ ] Automated data cleaning
- [ ] Natural language query interface

### Version 2.0 (Q4 2026)
- [ ] Streaming data analysis
- [ ] Real-time collaboration features
- [ ] Advanced ML model integration
- [ ] Data lineage tracking
- [ ] Enterprise SSO integration

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black src/
flake8 src/
mypy src/

# Run tests before committing
pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 AI-Powered EDA Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Support

### Documentation
- **API Reference**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-powered-eda/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-powered-eda/discussions)
- **Email**: support@yourproject.com

### Getting Help

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/ai-powered-eda/issues)
3. Ask in [discussions](https://github.com/yourusername/ai-powered-eda/discussions)
4. Create a [new issue](https://github.com/yourusername/ai-powered-eda/issues/new)

---

## 🙏 Acknowledgments

- **FastAPI**: For the excellent async web framework
- **Google Gemini**: For providing free AI API access
- **Pandas & NumPy**: For powerful data processing
- **Plotly & Seaborn**: For beautiful visualizations
- **Redis & Celery**: For robust background job processing
- **Open Source Community**: For continuous inspiration

---

<div align="center">

**Built with ❤️ using Python, FastAPI, and Google Gemini AI**

⭐ **Star this repository if you find it helpful!** ⭐

[Report Bug](https://github.com/yourusername/ai-powered-eda/issues) • [Request Feature](https://github.com/yourusername/ai-powered-eda/issues) • [Documentation](docs/)

</div>
