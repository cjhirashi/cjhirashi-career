# Quick Start Guide

Get cjhirashi-career-ai running in 5 minutes.

## 1️⃣ Clone Repository

```bash
git clone https://github.com/cjhirashi/cjhirashi-career.git
cd cjhirashi-career
```

## 2️⃣ Start Services (Docker Compose)

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

This starts:
- PostgreSQL (5432)
- Redis (6379)
- IA Service (8010)
- Prometheus (9090)

## 3️⃣ Test Service

```bash
# Health check
curl http://localhost:8010/health

# Get endpoints info
curl http://localhost:8010/api/metrics/endpoints

# Check observability dashboard
curl http://localhost:8010/api/observability/service-info
```

## 4️⃣ Try API

### Chat Endpoint

```bash
curl -X POST http://localhost:8010/api/bedrock/chat \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess-123",
    "message": "Hello, agent!",
    "model_id": "claude-3-5-sonnet-20241022"
  }'
```

### Get Metrics

```bash
# Rate limit status
curl -H "Authorization: Bearer test-token" \
  http://localhost:8010/api/metrics/rate-limit/status

# Prometheus metrics
curl http://localhost:8010/api/metrics/prometheus

# Observability dashboard
curl -H "Authorization: Bearer test-token" \
  http://localhost:8010/api/observability/dashboard
```

## 5️⃣ Run Tests

```bash
cd cjhirashi-career-ai

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src --cov-report=html
```

## 📊 Monitoring

### Logs

```bash
# Follow service logs
docker-compose logs -f ia-service

# View structured JSON logs
docker-compose logs ia-service | jq '.'
```

### Prometheus

Access: http://localhost:9090

Query examples:
```
rate_limit_requests{limiter="chat"}
rate_limit_remaining{limiter="model"}
ia_service_up
```

### Health Checks

```bash
# Service health
curl http://localhost:8010/health

# Database health (via service info)
curl http://localhost:8010/api/observability/service-info
```

## 🔧 Development

### Local Python Setup

```bash
cd cjhirashi-career-ai
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

python -m uvicorn src.main:app --reload
```

### Edit Code

- Endpoints: `src/routes/bedrock.py`
- Middleware: `src/middleware/`
- Clients: `src/clients/orchestrator_client.py`
- Tests: `tests/`

Changes auto-reload with `--reload` flag.

## 🚀 Deployment

### Docker Build

```bash
cd cjhirashi-career-ai
docker build -t my-org/career-ai:1.0.0 .
docker push my-org/career-ai:1.0.0
```

### Kubernetes

```bash
# Create secrets
kubectl create secret generic ia-service-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/db

# Create config
kubectl create configmap ia-service-config \
  --from-literal=redis-url=redis://redis:6379 \
  --from-literal=orchestrator-url=http://api:8001

# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=ia-service
kubectl logs -l app=ia-service -f
```

## 🛑 Stop Services

```bash
# Docker Compose
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Kubernetes
kubectl delete deployment cjhirashi-career-ia
kubectl delete service ia-service
```

## 📚 Next Steps

- Read `README.md` for architecture
- Read `DEPLOYMENT.md` for production setup
- Read `RELEASE_NOTES.md` for features
- Explore `src/` for code structure
- Run `pytest tests/ -v` for test coverage

## 🆘 Troubleshooting

### Service not responding

```bash
# Check container is running
docker-compose ps

# View logs
docker-compose logs ia-service

# Restart service
docker-compose restart ia-service
```

### Database connection error

```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Verify connection
docker-compose exec ia-service python -c \
  "import sqlalchemy; print('DB OK')"
```

### Redis connection error

```bash
# Check Redis is running
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping
```

## ✅ Success Checklist

- [x] Services started with docker-compose
- [x] Health check passes
- [x] API responds to requests
- [x] Tests pass
- [x] Logs are visible
- [x] Ready to develop!

---

**Time to production:** 5 minutes ✅
