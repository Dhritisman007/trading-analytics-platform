# Docker Setup & Deployment Guide

## ✅ Status: Docker Ready

Your Trade Analytics Platform is now Docker-ready with:
- ✅ Dockerfile (Python 3.12 FastAPI backend)
- ✅ Dockerfile.frontend (Node 20 → Nginx React frontend)
- ✅ docker-compose.yml (Full stack orchestration)
- ✅ nginx.conf (Production routing & API proxy)
- ✅ .env.example (Configuration template)
- ✅ .dockerignore (Build optimization)
- ✅ CI/CD Pipeline (.github/workflows/ci.yml)

---

## 🚀 Quick Start with Docker

### 1. Start Docker Desktop
- Open **Docker Desktop** application
- Wait for it to show "Docker is running" (usually 30-60 seconds)

### 2. Build and Run Everything
```bash
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# Option A: Using the startup script
chmod +x start-docker.sh
./start-docker.sh

# Option B: Manual commands
docker compose up --build
```

### 3. Access the Platform
- **Frontend**: http://localhost (served by Nginx on port 80)
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📊 Docker Architecture

```
Your Machine
├── Docker Desktop
    └── Docker Engine
        ├── trading_api (FastAPI Backend)
        │   ├── Python 3.12
        │   ├── Port: 8000
        │   └── Processes: Market data, ML, News, FVG, FII/DII
        │
        ├── trading_web (Nginx + React Frontend)
        │   ├── Node 20 (build-time)
        │   ├── Nginx (runtime)
        │   ├── Port: 80
        │   └── Routes /api/* → api:8000
        │
        ├── trading_postgres (Database)
        │   ├── PostgreSQL 15
        │   ├── Port: 5432
        │   └── Data: trading_db
        │
        └── trading_redis (Cache)
            ├── Redis 7
            └── Port: 6379
```

---

## 🔧 Common Docker Commands

### View Status
```bash
# See all running containers
docker compose ps

# Expected output:
# NAME              STATUS           PORTS
# trading_api       Up 2 minutes     0.0.0.0:8000->8000/tcp
# trading_web       Up 2 minutes     0.0.0.0:80->80/tcp
# trading_postgres  Up 2 minutes     0.0.0.0:5432->5432/tcp
# trading_redis     Up 2 minutes     0.0.0.0:6379->6379/tcp
```

### View Logs
```bash
# Backend logs
docker compose logs api

# Frontend logs
docker compose logs web

# Follow logs in real-time
docker compose logs -f api

# Last 50 lines only
docker compose logs --tail=50 api
```

### Execute Commands
```bash
# Run tests in the backend container
docker compose exec api pytest tests/ -v

# Interactive shell in backend
docker compose exec api bash

# Run any command
docker compose exec api python -c "print('Hello')"
```

### Stop/Start
```bash
# Stop all services (keep data)
docker compose stop

# Start all services
docker compose start

# Restart all services
docker compose restart

# Remove all containers (keep data)
docker compose down

# Remove everything including data
docker compose down -v
```

### Rebuild Images
```bash
# Rebuild without cache (fresh install)
docker compose build --no-cache

# Rebuild specific service
docker compose build --no-cache api
```

---

## 📦 What Gets Built

### Backend Image (trading_api)
- **Base**: python:3.12-slim
- **Size**: ~500MB
- **Includes**: FastAPI, SQLAlchemy, scikit-learn, yfinance, etc.
- **Exposed Port**: 8000
- **Health Check**: Every 30 seconds

### Frontend Image (trading_web)
- **Build Stage**: node:20-alpine
- **Runtime**: nginx:alpine
- **Size**: ~50MB (very small!)
- **Includes**: React app, optimized production build
- **Exposed Port**: 80
- **Routes**: / → React app, /api/* → backend proxy

### Databases (Pre-built images)
- **PostgreSQL 15-alpine**: ~150MB
- **Redis 7-alpine**: ~30MB

**Total**: ~730MB initial download (cached after first build)

---

## 🌐 Network & Communication

### Internal Docker Network: `trading_net`

```
Frontend (Nginx)
  ↓
  Routes:
  - / → React SPA (serve index.html)
  - /api/* → http://api:8000/
  - /ws/* → ws://api:8000/

Backend (FastAPI)
  ↓
  Connects to:
  - PostgreSQL (postgres:5432)
  - Redis (redis:6379)
  - Upstox API (external)
  - yfinance (external)
```

### External Access (Your Machine)

```
Your Browser
  ↓
http://localhost:80 → Nginx (frontend)
http://localhost:8000 → FastAPI (backend API)
http://localhost:5432 → PostgreSQL (if needed)
http://localhost:6379 → Redis (if needed)
```

---

## 🐛 Troubleshooting

### Services not starting?
```bash
# Check Docker is running
docker ps

# View detailed logs
docker compose logs

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Port already in use?
```bash
# macOS/Linux: Find what's using port 80
lsof -i :80

# Kill the process
kill -9 <PID>

# Or use different port in docker-compose.yml
# Change: ports: - "8080:80"
```

### Out of disk space?
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

### Can't connect to database?
```bash
# Check PostgreSQL is running
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Connect directly
docker compose exec postgres psql -U trading_user -d trading_db
```

---

## 📈 Performance

### Startup Time
- **First time**: 2-5 minutes (image build + startup)
- **Subsequent**: 30-60 seconds (just container startup)

### Resource Usage (While Running)
- **Backend**: 150-300 MB RAM
- **Frontend**: 50-100 MB RAM
- **PostgreSQL**: 100-200 MB RAM
- **Redis**: 10-20 MB RAM
- **Total**: ~400-600 MB RAM

### Optimization Tips
```bash
# Run in the background
docker compose up -d

# Use BuildKit for faster builds (5-10x faster)
export DOCKER_BUILDKIT=1
docker compose build

# Limit resource usage
docker compose -f docker-compose.yml -f docker-compose.limits.yml up
```

---

## 🚢 Next: Deploy to Production

### Option 1: AWS (ECS, EC2)
```bash
# Push to AWS ECR
aws ecr create-repository --repository-name trading-api
docker tag trading-api:latest <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/trading-api:latest
docker push <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/trading-api:latest
```

### Option 2: Heroku
```bash
# Push to Heroku Container Registry
heroku login
heroku container:login
heroku create your-app-name
heroku container:push web --app your-app-name
heroku container:release web --app your-app-name
```

### Option 3: DigitalOcean App Platform
```bash
# Connect your GitHub repo
# DigitalOcean reads docker-compose.yml automatically
# Auto-deploys on push to main branch
```

### Option 4: Self-hosted (VPS)
```bash
# On your VPS
scp docker-compose.yml user@vps:/home/app/
ssh user@vps

# On VPS:
cd /home/app
docker compose pull
docker compose up -d
```

---

## ✅ Verification Checklist

- [ ] Docker Desktop installed and running
- [ ] Docker version 20.10+
- [ ] Docker Compose version 2.0+
- [ ] .env file created
- [ ] Images built successfully (`docker images | grep trading`)
- [ ] Containers running (`docker compose ps`)
- [ ] API health check passing (`curl http://localhost:8000/health`)
- [ ] Frontend loads (`open http://localhost`)
- [ ] API documentation works (`open http://localhost:8000/docs`)
- [ ] Tests pass in container (`docker compose exec api pytest`)
- [ ] No port conflicts

---

## 📚 Useful Resources

- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Dockerfile Reference**: https://docs.docker.com/engine/reference/builder/
- **Docker Hub**: https://hub.docker.com/

---

## 🎉 You're All Set!

Your platform is now:
- ✅ **Production-ready** with Docker
- ✅ **Scalable** (easy to deploy anywhere)
- ✅ **Reproducible** (same environment everywhere)
- ✅ **Isolated** (no dependency conflicts)

**Next steps**:
1. Run locally with `docker compose up`
2. Test all features in browser
3. Deploy to your preferred cloud platform
4. Monitor with Docker logs

---

**Last Updated**: 2026-04-25
**Platform Version**: 0.16.0
**Docker Status**: ✅ READY FOR DEPLOYMENT
