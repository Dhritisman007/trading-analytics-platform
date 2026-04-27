# Docker Testing Guide

## Prerequisites
- **Docker Desktop** installed (https://www.docker.com/products/docker-desktop)
- **Git** for cloning the repo
- **At least 4GB RAM** available for containers

## Step 1: Prepare for Docker Build

```bash
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# Verify Docker is installed
docker --version
docker compose --version
```

## Step 2: Build All Services

```bash
# Build backend, frontend, and pull postgres/redis
docker compose up --build

# This will:
# 1. Build api (FastAPI Python image)
# 2. Build web (React Nginx image)
# 3. Pull postgres:15-alpine
# 4. Pull redis:7-alpine
# 5. Start all 4 services
```

## Step 3: Verify All Services Started

```bash
# In a new terminal:
docker compose ps

# Expected output:
# NAME              STATUS           PORTS
# trading_api       Up 2 min         0.0.0.0:8000->8000/tcp
# trading_web       Up 2 min         0.0.0.0:80->80/tcp
# trading_postgres  Up 2 min         0.0.0.0:5432->5432/tcp
# trading_redis     Up 2 min         0.0.0.0:6379->6379/tcp
```

## Step 4: Test API Health

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response (JSON):
# {
#   "status": "healthy",
#   "data_provider": "yfinance",
#   "ws_connected": false,
#   "cache": {...},
#   "scheduler": {...}
# }
```

## Step 5: Access the Platform

### Frontend
- **URL**: http://localhost (port 80, not 3000 in Docker)
- **Served by**: Nginx
- **Proxies API**: /api/* → http://api:8000/*

### Backend API
- **URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Database
- **Host**: localhost:5432
- **User**: trading_user
- **Password**: trading_pass
- **Database**: trading_db

### Cache
- **Host**: localhost:6379
- **Type**: Redis

## Step 6: View Logs

```bash
# Backend logs
docker compose logs api

# Frontend logs
docker compose logs web

# Database logs
docker compose logs postgres

# Redis logs
docker compose logs redis

# Follow logs in real-time
docker compose logs -f api
```

## Step 7: Run Backend Tests (in container)

```bash
# Run pytest inside api container
docker compose exec api pytest tests/ -v --tb=short

# Expected output:
# ======================== 326 passed in X.XXs ========================
```

## Step 8: Stop Everything

```bash
# Stop all services (keep volumes)
docker compose stop

# Remove all containers (keep volumes)
docker compose down

# Remove everything including volumes
docker compose down -v
```

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Find what's using port 80
lsof -i :80

# Kill the process
kill -9 <PID>
```

### Container Fails to Start
```bash
# Check logs for errors
docker compose logs api

# Rebuild from scratch
docker compose down -v
docker compose up --build --no-cache
```

### Database Connection Error
```bash
# Check if postgres is running
docker compose ps postgres

# Re-initialize database
docker compose exec api python -m alembic upgrade head
```

### Out of Disk Space
```bash
# Clean up Docker images
docker image prune -a

# Clean up volumes
docker volume prune

# Clean up everything
docker system prune -a --volumes
```

## Performance Tips

### Faster Builds
```bash
# Use BuildKit (faster, parallel builds)
export DOCKER_BUILDKIT=1
docker compose up --build
```

### Reduce Image Size
```bash
# Use multi-stage builds (already in Dockerfile)
# Images should be:
# - api: ~500MB
# - web: ~50MB
# - postgres: ~150MB
# - redis: ~30MB
```

### Monitor Resource Usage
```bash
# Watch resource usage
docker stats

# Shows CPU, memory, network I/O per container
```

## Deployment Checklist

- [ ] Docker version 20.10+
- [ ] Docker Compose version 2.0+
- [ ] .env file configured
- [ ] All images build successfully
- [ ] All containers start
- [ ] API health check passes
- [ ] Frontend loads
- [ ] Tests pass in container
- [ ] No port conflicts
- [ ] Sufficient disk space (2GB minimum)

## Next Steps

### Local Testing Complete ✅
→ Deploy to cloud (AWS, Heroku, DigitalOcean)

### Push to Registry
```bash
# Tag images
docker tag trading-api your-registry/trading-api:latest
docker tag trading-web your-registry/trading-web:latest

# Push to Docker Hub / Registry
docker push your-registry/trading-api:latest
docker push your-registry/trading-web:latest
```

### Deploy to Production
```bash
# AWS ECS, Kubernetes, or any Docker orchestration platform
# Use docker-compose.yml as reference for service configuration
```

---

## Summary

✅ Docker setup configured and ready to test
✅ All services defined (api, web, postgres, redis)
✅ Health checks configured
✅ Nginx proxy configured for production
✅ GitHub Actions CI/CD ready

**Total startup time**: ~2-3 minutes first time, ~30 seconds subsequent

---

For issues, check `.github/workflows/ci.yml` for the CI/CD equivalent setup.
