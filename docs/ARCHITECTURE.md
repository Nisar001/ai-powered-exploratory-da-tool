# System Architecture

## Overview

The AI-Powered EDA Platform follows a **microservices-inspired architecture** with clear separation of concerns, designed for scalability, maintainability, and production-grade reliability.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client Layer                              │
│  (Web Browser, API Clients, CLI Tools, Mobile Apps)             │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                          │
│  - Request routing                                                │
│  - SSL termination                                                │
│  - Rate limiting                                                  │
│  - Compression                                                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌──────────────────────┐     ┌──────────────────────┐
│   FastAPI Instance 1 │     │   FastAPI Instance N │
│  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │  API Routes    │  │     │  │  API Routes    │  │
│  │  - Upload      │  │     │  │  - Upload      │  │
│  │  - Analysis    │  │     │  │  - Analysis    │  │
│  │  - Health      │  │     │  │  - Health      │  │
│  └────────────────┘  │     │  └────────────────┘  │
│  ┌────────────────┐  │     │  ┌────────────────┐  │
│  │  Middleware    │  │     │  │  Middleware    │  │
│  │  - Logging     │  │     │  │  - Logging     │  │
│  │  - Auth        │  │     │  │  - Auth        │  │
│  │  - CORS        │  │     │  │  - CORS        │  │
│  └────────────────┘  │     │  └────────────────┘  │
└──────────┬───────────┘     └──────────┬───────────┘
           │                             │
           └─────────────┬───────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    Redis     │ │   Celery     │ │  File System │
│              │ │   Broker     │ │              │
│ - Caching    │ │              │ │ - Uploads    │
│ - Job State  │ │              │ │ - Results    │
│ - Sessions   │ │              │ │ - Logs       │
└──────────────┘ └──────┬───────┘ └──────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ Celery Workers  │
               │   (Pool)        │
               └────────┬────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Data Loader  │ │  Statistical │ │Visualization │
│              │ │   Analyzer   │ │   Engine     │
└──────────────┘ └──────────────┘ └──────────────┘
                        │
                        ▼
                ┌──────────────┐
                │ LLM Service  │
                │ (OpenAI/     │
                │  Anthropic)  │
                └──────────────┘
```

---

## Component Architecture

### 1. API Layer (`src/api/`)

**Responsibility**: HTTP request handling and routing

**Components**:
- **Routes** (`routes/`)
  - `upload.py`: File upload endpoints
  - `analysis.py`: Analysis job management
  - `health.py`: Health checks and monitoring
  
- **Middleware** (`middleware.py`)
  - Request logging
  - CORS handling
  - Security headers
  - Request ID generation
  
- **Exception Handlers** (`exception_handlers.py`)
  - Global error handling
  - Structured error responses
  - HTTP status code mapping

**Design Patterns**:
- Router pattern for modularity
- Middleware chain for cross-cutting concerns
- Exception handler registration for centralized error handling

---

### 2. Core Layer (`src/core/`)

**Responsibility**: Infrastructure and cross-cutting concerns

**Components**:
- **Configuration** (`config.py`)
  - Type-safe settings with Pydantic
  - Environment-driven configuration
  - Hierarchical settings organization
  
- **Logging** (`logging.py`)
  - Structured logging
  - Context enrichment
  - JSON formatting for production
  
- **Exceptions** (`exceptions.py`)
  - Exception hierarchy
  - Domain-specific exceptions
  - Error context preservation
  
- **Redis Client** (`redis_client.py`)
  - Connection pooling
  - Serialization/deserialization
  - Error handling
  
- **Celery App** (`celery_app.py`)
  - Task queue configuration
  - Worker management
  - Task routing

**Design Patterns**:
- Singleton pattern for shared clients
- Factory pattern for configuration
- Template method for exception handling

---

### 3. Service Layer (`src/services/`)

**Responsibility**: Business logic and data processing

**Components**:
- **Data Loader** (`data_loader.py`)
  - File validation
  - Schema inference
  - Memory optimization
  - Chunked reading for large files
  
- **Statistical Analyzer** (`statistical_analyzer.py`)
  - Descriptive statistics
  - Correlation analysis
  - Outlier detection
  - Distribution analysis
  - Data quality assessment
  
- **Visualization Engine** (`visualization_engine.py`)
  - Automated chart generation
  - Multiple chart types
  - Interactive visualizations
  - Publication-ready exports
  
- **LLM Service** (`llm_service.py`)
  - Prompt engineering
  - API integration (OpenAI/Anthropic)
  - Retry logic
  - Response parsing
  
- **EDA Orchestrator** (`eda_orchestrator.py`)
  - Workflow coordination
  - Pipeline execution
  - Resource management
  - Error recovery

**Design Patterns**:
- Strategy pattern for pluggable algorithms
- Template method for analysis workflows
- Facade pattern for orchestration
- Retry pattern with exponential backoff

---

### 4. Model Layer (`src/models/`)

**Responsibility**: Data structures and validation

**Components**:
- **Schemas** (`schemas.py`)
  - Request models
  - Response models
  - Internal data structures
  - Validation rules

**Design Patterns**:
- DTO (Data Transfer Object) pattern
- Builder pattern for complex objects

---

### 5. Task Layer (`src/tasks/`)

**Responsibility**: Asynchronous background processing

**Components**:
- **EDA Tasks** (`eda_tasks.py`)
  - Analysis job execution
  - Job state management
  - Result persistence
  - Cleanup operations

**Design Patterns**:
- Worker pattern for background processing
- State machine for job lifecycle

---

## Data Flow

### 1. File Upload Flow

```
Client
  │
  ▼ POST /api/v1/upload/
FastAPI Upload Route
  │
  ├─→ Validate file type & size
  │
  ├─→ Generate unique file ID
  │
  ├─→ Save to file system
  │
  └─→ Store metadata in Redis
      │
      ▼
  Return file_id to client
```

### 2. Analysis Trigger Flow

```
Client
  │
  ▼ POST /api/v1/analyze/
FastAPI Analysis Route
  │
  ├─→ Validate file exists
  │
  ├─→ Generate job ID
  │
  ├─→ Store job metadata in Redis
  │
  └─→ Queue Celery task
      │
      ▼
  Return job_id to client
  
  (Async Processing)
      │
      ▼
Celery Worker
  │
  ├─→ EDA Orchestrator
  │   │
  │   ├─→ Data Loader
  │   │   └─→ Load & validate CSV
  │   │
  │   ├─→ Statistical Analyzer
  │   │   ├─→ Column analysis
  │   │   ├─→ Correlation analysis
  │   │   ├─→ Outlier detection
  │   │   └─→ Distribution analysis
  │   │
  │   ├─→ Visualization Engine
  │   │   ├─→ Generate histograms
  │   │   ├─→ Generate box plots
  │   │   ├─→ Generate heatmaps
  │   │   └─→ Save visualizations
  │   │
  │   └─→ LLM Service
  │       ├─→ Prepare context
  │       ├─→ Call LLM API
  │       └─→ Parse insights
  │
  ├─→ Store result in Redis
  │
  └─→ Update job status to COMPLETED
```

### 3. Result Retrieval Flow

```
Client
  │
  ▼ GET /api/v1/analyze/result/{job_id}
FastAPI Analysis Route
  │
  ├─→ Check job status in Redis
  │
  ├─→ Retrieve result from Redis
  │
  └─→ Return complete analysis result
```

---

## Scalability Architecture

### Horizontal Scaling

**API Tier**: Multiple FastAPI instances behind load balancer
```
nginx ──┬─→ FastAPI Instance 1
        ├─→ FastAPI Instance 2
        ├─→ FastAPI Instance 3
        └─→ FastAPI Instance N
```

**Worker Tier**: Multiple Celery workers
```
Redis Broker ──┬─→ Celery Worker 1
               ├─→ Celery Worker 2
               ├─→ Celery Worker 3
               └─→ Celery Worker N
```

### Vertical Scaling

- Increase worker concurrency
- Optimize memory usage
- Tune connection pools

### Caching Strategy

**Redis Caching**:
- File metadata (7 days TTL)
- Job status (7 days TTL)
- Analysis results (24 hours TTL)

---

## Data Persistence

### Storage Architecture

```
File System
├── data/
│   ├── uploads/        # Uploaded CSV files
│   ├── results/        # Generated visualizations
│   └── temp/           # Temporary processing files
├── logs/               # Application logs
└── reports/            # Optional report exports
```

### State Management

**Redis Structure**:
```
eda:file:{file_id}      → Hash (file metadata)
eda:job:{job_id}        → Hash (job state)
eda:result:{job_id}     → JSON (analysis results)
```

---

## Security Architecture

### Defense in Depth

1. **Network Layer**
   - Firewall rules
   - DDoS protection
   - Rate limiting

2. **Application Layer**
   - Input validation
   - File type restrictions
   - Size limits
   - CORS policies

3. **Data Layer**
   - Encryption in transit (HTTPS)
   - Secure file storage
   - Access control

4. **API Layer**
   - Optional API key authentication
   - Request signing
   - Token validation

---

## Resilience & Fault Tolerance

### Error Handling Strategy

1. **Graceful Degradation**
   - Continue without AI insights if LLM fails
   - Partial results if some analyses fail
   
2. **Retry Logic**
   - Exponential backoff for LLM calls
   - Configurable retry attempts
   
3. **Circuit Breaker**
   - Prevent cascade failures
   - Automatic recovery

### High Availability

- **Stateless API**: Any instance can handle any request
- **Redundant Workers**: Multiple Celery workers
- **Redis Persistence**: Optional AOF/RDB persistence
- **Health Checks**: Continuous monitoring

---

## Monitoring & Observability

### Logging Levels

1. **Application Logs**: Structured JSON logs
2. **Access Logs**: Nginx request logs
3. **Worker Logs**: Celery task execution logs

### Metrics Collection

- Request latency
- Error rates
- Queue lengths
- Worker utilization
- Memory usage
- CPU usage

### Health Checks

- `/health`: Overall system health
- Individual service checks (Redis, filesystem)

---

## Technology Choices & Rationale

### FastAPI
- **Why**: High performance, async support, automatic docs
- **Alternatives Considered**: Flask, Django REST

### Celery
- **Why**: Mature, distributed, flexible
- **Alternatives Considered**: RQ, Dramatiq

### Redis
- **Why**: Fast, versatile, reliable
- **Alternatives Considered**: Memcached, PostgreSQL

### Pandas
- **Why**: Industry standard, rich ecosystem
- **Alternatives Considered**: Polars, Dask

### Pydantic
- **Why**: Type safety, validation, performance
- **Alternatives Considered**: Marshmallow, dataclasses

---

## Performance Characteristics

### Expected Performance

- **File Upload**: < 2 seconds (for 10MB file)
- **Analysis Initiation**: < 500ms
- **Analysis Completion**: 30-120 seconds (depends on dataset size)
- **Result Retrieval**: < 1 second

### Bottlenecks

1. **LLM API Calls**: 5-15 seconds
2. **Large Dataset Processing**: Memory-bound
3. **Visualization Generation**: CPU-bound

### Optimization Strategies

1. **Async Processing**: Non-blocking I/O
2. **Caching**: Redis for frequent access
3. **Chunked Reading**: Memory efficiency
4. **Parallel Processing**: Multiple workers

---

## Future Architecture Enhancements

### Planned Improvements

1. **Database Integration**: PostgreSQL for persistent metadata
2. **Object Storage**: S3/MinIO for files
3. **Message Queue**: Separate broker from cache
4. **Streaming**: WebSocket for real-time progress
5. **Multi-tenancy**: User isolation and quotas
6. **API Gateway**: Centralized authentication
7. **Service Mesh**: Istio for microservices

### Scalability Roadmap

1. **Phase 1**: Current single-machine deployment
2. **Phase 2**: Multi-instance with load balancer
3. **Phase 3**: Kubernetes orchestration
4. **Phase 4**: Multi-region deployment

---

## Architectural Principles

1. **Separation of Concerns**: Clear layer boundaries
2. **Single Responsibility**: Each component has one job
3. **Dependency Inversion**: Depend on abstractions
4. **Open/Closed**: Open for extension, closed for modification
5. **Configuration Over Code**: Environment-driven behavior
6. **Fail Fast**: Validate early, fail gracefully
7. **Observability First**: Log, measure, monitor

---

**Last Updated**: December 30, 2025
