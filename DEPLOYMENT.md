# Deployment Guide - cjhirashi-career-ai (FASE 7)

## Local Development

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f ia-service

# Stop services
docker-compose down
```

### Direct Python

```bash
cd cjhirashi-career-ai

# Install dependencies
pip install -r requirements.txt

# Run application
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8010
```

## Docker Build & Push

```bash
# Build image
docker build -t cjhirashi-career-ai:1.0.0 ./cjhirashi-career-ai

# Tag for registry
docker tag cjhirashi-career-ai:1.0.0 ghcr.io/cjhirashi/cjhirashi-career-ai:1.0.0

# Push to registry
docker push ghcr.io/cjhirashi/cjhirashi-career-ai:1.0.0
```

## Kubernetes Deployment

### Prerequisites

- kubectl configured
- Kubernetes cluster running
- Secrets created:
  - `ia-service-secrets` with `database-url`
  - `ia-service-config` with `redis-url`, `orchestrator-url`

### Deploy

```bash
# Apply deployment
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=ia-service
kubectl get svc ia-service

# View logs
kubectl logs -l app=ia-service -f

# Scale replicas
kubectl scale deployment cjhirashi-career-ia --replicas=5
```

### Secrets Setup

```bash
# Create secret
kubectl create secret generic ia-service-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/db

# Create config
kubectl create configmap ia-service-config \
  --from-literal=redis-url=redis://redis:6379/0 \
  --from-literal=orchestrator-url=http://api:8001
```

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (min 32 chars)
- `AWS_ACCESS_KEY_ID` - AWS credentials (if using Bedrock)
- `AWS_SECRET_ACCESS_KEY` - AWS credentials

Optional:
- `REDIS_URL` - Redis connection (default: local)
- `ORCHESTRATOR_API_BASE_URL` - Orchestrator API URL
- `DEBUG` - Debug mode (default: false)

## CI/CD Pipeline

GitHub Actions workflow in `.github/workflows/ci-cd.yml` runs:
1. Tests (pytest)
2. Linting & type checking
3. Docker build
4. Security checks
5. Deploy notification

Triggers on:
- Push to develop/main
- Pull requests to develop/main

## Health Checks

Service exposes health endpoint:
- `GET /health` - Basic health check
- `GET /api/metrics/prometheus` - Prometheus metrics
- `GET /api/observability/dashboard` - Real-time dashboard

## Monitoring

### Prometheus

Metrics exposed on `/api/metrics/prometheus`:
- rate_limit_requests
- rate_limit_remaining
- http_request_duration
- external_api_latency

### Jaeger

Distributed tracing available when Jaeger is configured.

### Logs

JSON structured logs to stdout (parseable by ELK, Splunk, etc.)

## Troubleshooting

### Connection Issues

```bash
# Check service is running
curl http://localhost:8010/health

# Check logs
docker-compose logs ia-service

# Verify database connection
kubectl exec -it <pod> -- psql $DATABASE_URL -c "SELECT 1;"
```

### Performance

- Monitor `/api/metrics/prometheus`
- Check `/api/observability/performance`
- Review structured logs for slow queries/calls

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Redis connection verified
- [ ] Orchestrator API reachable
- [ ] Health check passing
- [ ] Monitoring/logging configured
- [ ] Secrets/ConfigMaps created
- [ ] Load balancer configured (if needed)
- [ ] SSL/TLS certificates installed
- [ ] Backup strategy in place
