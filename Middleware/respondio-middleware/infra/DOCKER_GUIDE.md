# 🐳 Docker Deployment Guide

## Quick Start (Development with Mock MCP)

```bash
# Navigate to infra directory
cd infra

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services will be available at:**
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Mock MCP: http://localhost:8080
- Redis: localhost:6379

---

## Production Deployment

### 1. Prepare Environment

```bash
cd infra

# Copy environment template
cp .env.example .env

# Edit .env with your production values
nano .env
```

**Required changes:**
- `WEBHOOK_SECRET` - Strong secret for Respond.io
- `DASHBOARD_PASSWORD` - Strong password for dashboard
- `MCP_URL` - Your actual MCP server URL

### 2. Deploy

```bash
# Build and start (production mode, without mock MCP)
docker-compose -f docker-compose.prod.yml up -d

# Check health
docker-compose -f docker-compose.prod.yml ps
```

---

## Docker Commands

### Start Services
```bash
# Development (with mock MCP)
docker-compose up -d

# Production (without mock MCP)
docker-compose -f docker-compose.prod.yml up -d

# Start specific service
docker-compose up -d api
```

### Stop Services
```bash
# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f dashboard
docker-compose logs -f mock_mcp
docker-compose logs -f redis
```

### Rebuild
```bash
# Rebuild all
docker-compose build

# Rebuild specific service
docker-compose build api

# Rebuild and restart
docker-compose up -d --build
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

---

## Service Details

### API (Port 8000)
- **Image:** Custom (built from Dockerfile.api)
- **Dependencies:** Redis, Mock MCP (dev) or Real MCP (prod)
- **Health Check:** GET /health
- **Restart Policy:** unless-stopped

### Dashboard (Port 8501)
- **Image:** Custom (built from Dockerfile.dashboard)
- **Dependencies:** API
- **Access:** http://localhost:8501
- **Restart Policy:** unless-stopped

### Mock MCP (Port 8080) - Dev Only
- **Image:** Custom (built from Dockerfile.mock_mcp)
- **Purpose:** Testing with real Google News
- **Health Check:** GET /health
- **Restart Policy:** unless-stopped

### Redis (Port 6379)
- **Image:** redis:7-alpine
- **Purpose:** Configuration and telemetry storage
- **Persistence:** Volume mounted
- **Restart Policy:** unless-stopped

---

## Networking

All services are on the same Docker network: `respondio_network`

**Internal DNS:**
- `api` → API service
- `dashboard` → Dashboard service
- `mock_mcp` → Mock MCP service
- `redis` → Redis service

---

## Volumes

### redis_data
- **Purpose:** Persist Redis data
- **Location:** Docker managed volume
- **Backup:** `docker run --rm -v respondio_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data`

---

## Health Checks

All services have health checks configured:

```bash
# Check health status
docker-compose ps

# Detailed health check
docker inspect respondio_api | grep -A 10 Health
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs service_name

# Check if port is already in use
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :8080
```

### Redis connection failed
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### API can't reach MCP
```bash
# Check MCP is running
docker-compose ps mock_mcp

# Test MCP from API container
docker-compose exec api curl http://mock_mcp:8080/health
```

### Dashboard can't reach API
```bash
# Check API is running
docker-compose ps api

# Test API from dashboard container
docker-compose exec dashboard curl http://api:8000/health
```

---

## Scaling

### Horizontal Scaling (Multiple API Instances)

```yaml
# In docker-compose.yml
api:
  # ... existing config ...
  deploy:
    replicas: 3
```

Then use a load balancer (nginx, traefik) in front.

---

## Monitoring

### Container Stats
```bash
# Real-time stats
docker stats

# Specific service
docker stats respondio_api
```

### Logs to File
```bash
# Export logs
docker-compose logs > logs.txt

# Follow logs to file
docker-compose logs -f > logs.txt
```

---

## Backup & Restore

### Backup Redis Data
```bash
docker-compose exec redis redis-cli SAVE
docker cp respondio_redis:/data/dump.rdb ./redis_backup.rdb
```

### Restore Redis Data
```bash
docker-compose down
docker cp ./redis_backup.rdb respondio_redis:/data/dump.rdb
docker-compose up -d
```

---

## Security Best Practices

1. **Change default secrets**
   - Update `WEBHOOK_SECRET`
   - Update `DASHBOARD_PASSWORD`

2. **Use HTTPS in production**
   - Add nginx/traefik with SSL
   - Use Let's Encrypt certificates

3. **Limit exposed ports**
   - Only expose necessary ports
   - Use firewall rules

4. **Regular updates**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Monitor logs**
   - Set up log aggregation
   - Configure alerts

---

## Cloud Deployment

### Google Cloud Run
```bash
# Build and push
docker build -f infra/Dockerfile.api -t gcr.io/PROJECT_ID/respondio-api .
docker push gcr.io/PROJECT_ID/respondio-api

# Deploy
gcloud run deploy respondio-api \
  --image gcr.io/PROJECT_ID/respondio-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### AWS App Runner
```bash
# Build and push to ECR
docker build -f infra/Dockerfile.api -t respondio-api .
docker tag respondio-api:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/respondio-api:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/respondio-api:latest

# Create App Runner service via console or CLI
```

### Azure Container Apps
```bash
# Build and push to ACR
az acr build --registry REGISTRY_NAME --image respondio-api:latest -f infra/Dockerfile.api .

# Deploy
az containerapp create \
  --name respondio-api \
  --resource-group RESOURCE_GROUP \
  --image REGISTRY_NAME.azurecr.io/respondio-api:latest
```

---

## Next Steps

1. ✅ Test locally with `docker-compose up`
2. ✅ Verify all services are healthy
3. ✅ Test webhook endpoint
4. ✅ Access dashboard and verify functionality
5. ✅ Configure production environment variables
6. ✅ Deploy to production
7. ✅ Connect Respond.io webhook
8. ✅ Monitor and optimize
