# 🚀 Deployment Guide - ORBIT Integration Middleware

Complete guide for deploying the middleware to production.

---

## 📋 Pre-Deployment Checklist

### 1. **Environment Configuration**

- [ ] Copy `.env.example` to `.env`
- [ ] Update `WEBHOOK_SECRET` with strong secret
- [ ] Update `DASHBOARD_PASSWORD` with strong password
- [ ] Configure `MCP_URL` to your production MCP
- [ ] Review all environment variables

### 2. **Security**

- [ ] Change all default secrets
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Configure IP whitelisting (optional)
- [ ] Review security settings

### 3. **Infrastructure**

- [ ] Redis instance ready
- [ ] MCP server accessible
- [ ] Domain/subdomain configured
- [ ] SSL certificates ready

---

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

#### **Step 1: Prepare Environment**

```bash
cd infra

# Copy and edit environment file
cp .env.example .env
nano .env
```

**Required changes:**
```env
WEBHOOK_SECRET=<generate-strong-secret-32-chars>
DASHBOARD_PASSWORD=<strong-password>
MCP_URL=http://your-mcp-server:8080/query
```

#### **Step 2: Deploy**

```bash
# Production deployment (without mock MCP)
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### **Step 3: Verify**

```bash
# Test API health
curl http://localhost:8000/health

# Test dashboard
curl http://localhost:8501
```

### Option 2: Individual Containers

```bash
# Build API
docker build -f infra/Dockerfile.api -t respondio-api .

# Build Dashboard
docker build -f infra/Dockerfile.dashboard -t respondio-dashboard .

# Run API
docker run -d \
  --name respondio_api \
  -p 8000:8000 \
  --env-file .env \
  respondio-api

# Run Dashboard
docker run -d \
  --name respondio_dashboard \
  -p 8501:8501 \
  --env-file .env \
  respondio-dashboard
```

---

## ☁️ Cloud Deployment

### Google Cloud Run

#### **Deploy API**

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy respondio-api \
  --source . \
  --dockerfile infra/Dockerfile.api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="MCP_URL=http://your-mcp:8080/query" \
  --set-env-vars="WEBHOOK_SECRET=your-secret" \
  --memory 512Mi \
  --cpu 1
```

#### **Deploy Dashboard**

```bash
gcloud run deploy respondio-dashboard \
  --source . \
  --dockerfile infra/Dockerfile.dashboard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="API_URL=https://respondio-api-xxx.run.app" \
  --memory 512Mi \
  --cpu 1
```

#### **Configure Redis**

Use Google Cloud Memorystore:
```bash
gcloud redis instances create respondio-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

### AWS App Runner

#### **Push to ECR**

```bash
# Authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name respondio-api

# Build and push
docker build -f infra/Dockerfile.api -t respondio-api .
docker tag respondio-api:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/respondio-api:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/respondio-api:latest
```

#### **Create App Runner Service**

```bash
aws apprunner create-service \
  --service-name respondio-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/respondio-api:latest",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "MCP_URL": "http://your-mcp:8080/query",
          "WEBHOOK_SECRET": "your-secret"
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }'
```

### Azure Container Apps

#### **Create Resource Group**

```bash
az group create \
  --name respondio-rg \
  --location eastus
```

#### **Create Container Registry**

```bash
az acr create \
  --resource-group respondio-rg \
  --name respondioregistry \
  --sku Basic
```

#### **Build and Push**

```bash
az acr build \
  --registry respondioregistry \
  --image respondio-api:latest \
  --file infra/Dockerfile.api \
  .
```

#### **Create Container App**

```bash
az containerapp create \
  --name respondio-api \
  --resource-group respondio-rg \
  --image respondioregistry.azurecr.io/respondio-api:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    MCP_URL=http://your-mcp:8080/query \
    WEBHOOK_SECRET=your-secret
```

---

## 🔒 HTTPS/SSL Setup

### Option 1: Nginx Reverse Proxy

#### **Install Nginx**

```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

#### **Configure Nginx**

Create `/etc/nginx/sites-available/respondio`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name dashboard.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### **Enable Site**

```bash
sudo ln -s /etc/nginx/sites-available/respondio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### **Get SSL Certificate**

```bash
sudo certbot --nginx -d api.yourdomain.com -d dashboard.yourdomain.com
```

### Option 2: Traefik

Create `docker-compose.traefik.yml`:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your@email.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=myresolver"
```

---

## 📊 Monitoring Setup

### Prometheus + Grafana (Optional)

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 🔧 Post-Deployment

### 1. **Configure Respond.io**

1. Go to Respond.io Settings → Webhooks
2. Add webhook:
   - URL: `https://api.yourdomain.com/webhook`
   - Header: `X-Webhook-Secret: your-secret`
   - Events: Message Received

### 2. **Test Integration**

```bash
# Send test message
curl -X POST https://api.yourdomain.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "conversation_id": "test_123",
    "contact_id": "contact_456",
    "channel": "whatsapp",
    "user_text": "test message"
  }'
```

### 3. **Monitor Dashboard**

1. Access: `https://dashboard.yourdomain.com`
2. Login with credentials
3. Check KPIs page for metrics
4. Verify requests appear in History

---

## 🔄 Updates and Maintenance

### Update Deployment

```bash
# Pull latest changes
git pull

# Rebuild and restart
cd infra
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup Redis Data

```bash
docker-compose exec redis redis-cli SAVE
docker cp respondio_redis:/data/dump.rdb ./backup_$(date +%Y%m%d).rdb
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f dashboard
```

---

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service_name

# Check if port is in use
netstat -tulpn | grep :8000

# Restart service
docker-compose restart service_name
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Limit memory in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
```

### Redis Connection Issues

```bash
# Test Redis
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] Secrets changed from defaults
- [ ] HTTPS/SSL configured
- [ ] Firewall rules set
- [ ] Redis backup configured
- [ ] Monitoring set up
- [ ] Respond.io webhook configured
- [ ] Test webhook working
- [ ] Dashboard accessible
- [ ] Logs being collected
- [ ] Health checks passing

---

**Your middleware is now production-ready!** 🚀
