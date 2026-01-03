# Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Scaling & Load Balancing](#scaling--load-balancing)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, Windows with WSL2
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 50GB+ available
- **Network**: Outbound HTTPS access for LLM APIs

### Software Requirements
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.11+ (for manual deployment)
- **Redis**: 7.0+ (included in Docker setup)

### API Keys
- OpenAI API key (or Anthropic/Azure)
- (Optional) Sentry DSN for error tracking

---

## Environment Configuration

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Configure Essential Settings

#### Application Settings
```env
APP_NAME="AI-Powered EDA Platform"
APP_VERSION="1.0.0"
APP_ENV="production"
DEBUG=false
LOG_LEVEL="INFO"
```

#### Server Configuration
```env
HOST="0.0.0.0"
PORT=8000
WORKERS=4
```

#### Security Settings
```env
# Generate strong secret key
SECRET_KEY="$(openssl rand -hex 32)"

# Configure CORS
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
CORS_ENABLED=true
```

#### LLM Configuration
```env
LLM_PROVIDER="openai"
OPENAI_API_KEY="sk-your-actual-api-key-here"
LLM_MODEL="gpt-4-turbo-preview"
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
```

#### Redis Configuration
```env
REDIS_HOST="redis"
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""  # Set in production
```

#### Celery Configuration
```env
CELERY_BROKER_URL="redis://redis:6379/0"
CELERY_RESULT_BACKEND="redis://redis:6379/0"
```

---

## Docker Deployment

### 1. Basic Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 2. Production Build

```bash
# Build with production settings
docker-compose -f docker-compose.yml build --no-cache

# Start services
docker-compose -f docker-compose.yml up -d

# Verify deployment
curl http://localhost/health
```

### 3. Service Management

```bash
# Restart specific service
docker-compose restart api

# Scale workers
docker-compose up -d --scale celery-worker=4

# View resource usage
docker stats

# Stop all services
docker-compose down
```

### 4. Data Persistence

Data directories are mounted as volumes:
```yaml
volumes:
  - ./data/uploads:/app/data/uploads
  - ./data/results:/app/data/results
  - ./logs:/app/logs
```

To backup:
```bash
tar -czf eda-backup-$(date +%Y%m%d).tar.gz data/ logs/
```

---

## Manual Deployment

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip redis-server nginx
```

### 2. Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash edaapp

# Create application directory
sudo mkdir -p /opt/eda-platform
sudo chown edaapp:edaapp /opt/eda-platform

# Switch to app user
sudo su - edaapp

# Clone repository
cd /opt/eda-platform
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Services

#### Systemd Service for API

Create `/etc/systemd/system/eda-api.service`:
```ini
[Unit]
Description=EDA Platform API
After=network.target redis.service

[Service]
Type=notify
User=edaapp
Group=edaapp
WorkingDirectory=/opt/eda-platform
Environment="PATH=/opt/eda-platform/venv/bin"
ExecStart=/opt/eda-platform/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    --timeout 300 \
    src.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Systemd Service for Celery Worker

Create `/etc/systemd/system/eda-celery.service`:
```ini
[Unit]
Description=EDA Platform Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=edaapp
Group=edaapp
WorkingDirectory=/opt/eda-platform
Environment="PATH=/opt/eda-platform/venv/bin"
ExecStart=/opt/eda-platform/venv/bin/celery \
    -A src.core.celery_app worker \
    --loglevel=info \
    --concurrency=4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable eda-api eda-celery
sudo systemctl start eda-api eda-celery

# Check status
sudo systemctl status eda-api
sudo systemctl status eda-celery
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/eda-platform`:
```nginx
upstream api_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://api_backend/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/eda-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
```

---

## Cloud Deployment

### AWS Deployment

#### 1. ECS Deployment

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create ECR repository
aws ecr create-repository --repository-name eda-platform

# Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t eda-platform .
docker tag eda-platform:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/eda-platform:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/eda-platform:latest
```

#### 2. Infrastructure Setup

- **VPC**: Create VPC with public/private subnets
- **ElastiCache**: Redis cluster for caching
- **S3**: Bucket for file storage
- **RDS**: (Optional) PostgreSQL for metadata
- **ALB**: Application Load Balancer
- **ECS**: Task definitions and services

#### 3. Environment Variables

Store secrets in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
    --name eda-platform/production \
    --secret-string file://secrets.json
```

### Azure Deployment

#### 1. Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name eda-platform-rg --location eastus

# Create container registry
az acr create --resource-group eda-platform-rg \
    --name edaplatformregistry --sku Basic

# Build and push image
az acr build --registry edaplatformregistry \
    --image eda-platform:latest .
```

#### 2. Deploy Container

```bash
az container create \
    --resource-group eda-platform-rg \
    --name eda-api \
    --image edaplatformregistry.azurecr.io/eda-platform:latest \
    --cpu 2 --memory 4 \
    --registry-login-server edaplatformregistry.azurecr.io \
    --registry-username <username> \
    --registry-password <password> \
    --ports 8000 \
    --environment-variables @env-vars.txt
```

### Google Cloud Platform

#### 1. Cloud Run Deployment

```bash
# Build and submit
gcloud builds submit --tag gcr.io/<project-id>/eda-platform

# Deploy to Cloud Run
gcloud run deploy eda-platform \
    --image gcr.io/<project-id>/eda-platform \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="$(cat .env | xargs)"
```

---

## Scaling & Load Balancing

### Horizontal Scaling

#### Docker Compose
```bash
# Scale API instances
docker-compose up -d --scale api=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=5
```

#### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eda-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eda-api
  template:
    metadata:
      labels:
        app: eda-api
    spec:
      containers:
      - name: api
        image: eda-platform:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

### Load Balancer Configuration

Nginx load balancing:
```nginx
upstream api_backend {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
    server api3:8000 max_fails=3 fail_timeout=30s;
}
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# View API logs
docker-compose logs -f api

# View Celery logs
docker-compose logs -f celery-worker

# View all logs
docker-compose logs -f
```

### 2. Centralized Logging

Configure Sentry:
```env
SENTRY_DSN="https://your-sentry-dsn"
```

### 3. Metrics Collection

Access Flower for Celery monitoring:
```
http://localhost:5555
```

### 4. Health Monitoring

Setup health check monitoring:
```bash
# Continuous health check
watch -n 30 'curl -s http://localhost/health | jq'
```

---

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/eda-platform"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup data
tar -czf "$BACKUP_DIR/data-$DATE.tar.gz" \
    -C /opt/eda-platform data/

# Backup Redis (if applicable)
redis-cli BGSAVE

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/data-$DATE.tar.gz"
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore data
tar -xzf backup-file.tar.gz -C /opt/eda-platform

# Start services
docker-compose up -d
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (change port if needed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### 2. API Security

- Enable API key authentication
- Implement rate limiting
- Use HTTPS only in production
- Set strong CORS policies
- Regular security updates

### 3. Secret Management

Never commit secrets to version control:
```bash
# Use environment variables
# Or use secret management services:
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
```

---

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs api

# Check port conflicts
sudo netstat -tulpn | grep 8000

# Restart services
docker-compose restart
```

#### Redis Connection Failed
```bash
# Check Redis status
docker-compose ps redis

# Test Redis connection
redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### Celery Tasks Not Processing
```bash
# Check Celery worker status
docker-compose logs celery-worker

# Check Celery queue
celery -A src.core.celery_app inspect active

# Purge queue
celery -A src.core.celery_app purge
```

#### Out of Memory
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Or optimize application configuration
```

---

## Performance Tuning

### Gunicorn Workers
```python
# Calculate optimal workers
workers = (2 * cpu_count) + 1
```

### Redis Optimization
```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Database Connection Pooling
```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

---

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check logs for errors
2. **Monthly**: Update dependencies
3. **Quarterly**: Security audit
4. **As needed**: Scale resources based on usage

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart with zero downtime
docker-compose up -d --no-deps --build api
```

---

**Last Updated**: December 30, 2025
