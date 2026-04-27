# DEPLOYMENT.md — Production Deployment Guide## OverviewTrade Analytics Platform is a full-stack FastAPI + React/Vite application designed for containerized deployment.**Technology Stack:**- **Backend**: FastAPI/Uvicorn (Python 3.12)- **Frontend**: React 18 + Vite (Node 20)- **Database**: PostgreSQL 15- **Cache**: Redis 7- **Container**: Docker + Docker Compose- **CI/CD**: GitHub Actions---## Prerequisites### Local Development- Python 3.12+- Node 20+- Docker + Docker Compose- Git### Production- Docker + Docker Compose- 2+ GB RAM- 10+ GB disk space- Port 80 (HTTP) and 8000 (API) available---## Quick Start (Docker Compose)### 1. Clone & Setup```bashgit clone https://github.com/yourusername/trade-analytics-platform.gitcd Trade\ Analytics\ Platform# Copy environmentcp .env.example .env# Edit .env with your confignano .env```### 2. Build & Run```bash# Build all servicesdocker-compose build# Start all servicesdocker-compose up -d# Check logsdocker-compose logs -f# View running containersdocker-compose ps```### 3. Verify```bash# Backend healthcurl http://localhost:8000/health# Frontendopen http://localhost# API docsopen http://localhost:8000/docs```### 4. Stop```bashdocker-compose down# With cleanupdocker-compose down -v```---## Service Details### Backend API (FastAPI)- **Container**: `trading_api`- **Port**: `8000`- **Health Check**: `GET /health`- **Docs**: `GET /docs` (Swagger UI)- **Database**: PostgreSQL (auto-connects via `DATABASE_URL`)**Environment Variables:**```bashAPP_NAME=Trading Analytics PlatformDEBUG=falseDATA_PROVIDER=yfinanceDATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_dbREDIS_URL=redis://redis:6379UPSTOX_ACCESS_TOKEN=  # optionalNEWSAPI_KEY=          # optional```**Scheduler Jobs (background):**- `refresh_market`: Every 5 minutes- `refresh_indicators`: Every 15 minutes- `refresh_news`: Every 15 minutes- `refresh_fvgs`: Every 30 minutes- `refresh_fii_dii`: Daily at 4:30 PM IST### Frontend (React/Nginx)- **Container**: `trading_frontend`- **Port**: `80` (mapped to `3000` in compose)- **Build**: Multi-stage (Node builder → Nginx)- **Proxy**: `/api/*` → Backend (`http://api:8000`)**Pages:**- Dashboard - Market overview- Indicators - RSI, EMA, MACD, ATR- SMC/FVG - Smart Money Concepts- Predict - ML price predictions- Risk - Portfolio risk analysis- Backtest - Strategy backtesting- News - Financial news feed- FII/DII - Institutional flows### Database (PostgreSQL)- **Container**: `trading_postgres`- **Port**: `5432`- **User**: `trading_user`- **Password**: `trading_pass` (change in production!)- **Database**: `trading_db`- **Volume**: `postgres_data` (persistent)### Cache (Redis)- **Container**: `trading_redis`- **Port**: `6379`- **Volume**: `redis_data` (persistent)---## Configuration### Environment Variables (.env)**Required:**```bashAPP_NAME="Trading Analytics Platform"DEBUG=falseSECRET_KEY=your-secret-key-hereDATA_PROVIDER=yfinance  # or "upstox"```**Database (auto-configured in Docker):**```bashDATABASE_URL=postgresql://trading_user:trading_pass@postgres:5432/trading_dbREDIS_URL=redis://redis:6379```**Optional APIs:**```bashUPSTOX_API_KEY=your-keyUPSTOX_API_SECRET=your-secretUPSTOX_ACCESS_TOKEN=your-tokenNEWSAPI_KEY=your-key```### Database URL Formats- **PostgreSQL (Docker)**: `postgresql://user:pass@postgres:5432/dbname`- **PostgreSQL (Local)**: `postgresql://user:pass@localhost:5432/dbname`- **SQLite (Development)**: `sqlite:///./test.db`---## Development vs Production### Development (Local)```bash# Terminal 1 - Backendcd /path/to/platformsource venv/bin/activatepython main.py# Terminal 2 - Frontendcd frontendnpm run dev```### Production (Docker)```bashdocker-compose up -d```---## Nginx Configuration**nginx.conf** handles:1. **React Router** - All unknown paths serve `index.html`2. **API Proxy** - `/api/*` → FastAPI backend3. **WebSocket** - `/ws/*` → WebSocket connections4. **Caching** - Static assets cached for 1 year**Example requests:**```bash# Frontend pagesGET http://localhost/               → index.htmlGET http://localhost/indicators     → index.html (React Router)# API requests (proxied to backend)GET http://localhost/api/health     → http://api:8000/healthGET http://localhost/api/market     → http://api:8000/market```---## CI/CD Pipeline (GitHub Actions)**Workflow**: `.github/workflows/ci.yml`**Triggers:**- Push to `main` or `develop`- Pull request to `main`**Jobs:**1. **Backend Tests** - Runs pytest (326 tests)2. **Frontend Build** - Builds React app with Vite3. **Docker Build** - Builds both Docker images**Sample run:**```✓ Backend tests (2m 15s)✓ Frontend build (1m 30s)✓ Docker build (3m 45s)Total: 7m 30s```---## Troubleshooting### Backend not starting```bash# Check logsdocker-compose logs api# Verify PostgreSQL is healthydocker-compose logs postgres# Restart just the backenddocker-compose restart api```### Frontend showing 404```bash# Check nginx configdocker exec trading_frontend cat /etc/nginx/conf.d/default.conf# Check frontend builddocker exec trading_frontend ls -la /usr/share/nginx/html/```### Database connection error```bash# Check DATABASE_URL in .envcat .env | grep DATABASE_URL# Test connectionpsql postgresql://trading_user:trading_pass@localhost:5432/trading_db```### Redis connection error```bash# Check REDIS_URLcat .env | grep REDIS_URL# Test connectionredis-cli ping```---## Monitoring & Logs### View Logs```bash# All servicesdocker-compose logs -f# Specific servicedocker-compose logs -f apidocker-compose logs -f frontend# Last 50 linesdocker-compose logs --tail=50 api```### Health Checks```bash# Backendcurl http://localhost:8000/health# Frontendcurl http://localhost:80/# Databasedocker exec trading_postgres pg_isready```### Resource Usage```bash# Container statsdocker stats# Disk usagedocker system df```---## Scaling### Horizontal Scaling (Multiple Backends)
```yaml
# docker-compose.yml — scale approach
services:
  api1:
    build: .
    ports: ["8000:8000"]
    
  api2:
    build: .
    ports: ["8001:8000"]

  # Load balancer (nginx) routes to both
  nginx:
    image: nginx:alpine
    ports: ["80:80"]
```

### Vertical Scaling (More Resources)
```bash
# Increase memory
docker-compose up -d --memory="4g"

# Increase CPU
docker run --cpus="2" ...
```

---

## Security Best Practices

1. **Change Default Passwords**
   ```bash
   # In .env
   POSTGRES_PASSWORD=your-secure-password-here
   SECRET_KEY=generate-with-secrets.token_urlsafe(32)
   ```

2. **Use HTTPS**
   - Deploy behind reverse proxy (nginx/HAProxy)
   - Install SSL certificate (Let's Encrypt)
   - Redirect HTTP → HTTPS

3. **Restrict Database Access**
   - Only backend can access PostgreSQL
   - Redis not exposed publicly
   - Use strong credentials

4. **Environment Variables**
   - Never commit `.env` to git
   - Use `.env.example` for reference
   - Rotate tokens regularly

5. **API Rate Limiting**
   - Implement via nginx or FastAPI middleware
   - Protect against abuse

---

## Backups

### Database Backup
```bash
# Full backup
docker exec trading_postgres pg_dump -U trading_user trading_db > backup.sql

# Restore
docker exec -i trading_postgres psql -U trading_user trading_db < backup.sql
```

### Model Artifacts
```bash
# Backup ML models
docker exec trading_api tar -czf models_backup.tar.gz /app/models
docker cp trading_api:/models_backup.tar.gz .
```

---

## Upgrades

### Backend Update
```bash
# Pull latest code
git pull origin main

# Rebuild backend image
docker-compose build api

# Restart backend
docker-compose up -d api
```

### Database Migration
```bash
# Create schema
docker exec trading_api python -c "from core.database import init_db; init_db()"

# Verify
curl http://localhost:8000/health
```

---

## Deployment Checklist

- [ ] `.env` configured with production values
- [ ] Database credentials changed from defaults
- [ ] SECRET_KEY set to secure random value
- [ ] SSL/HTTPS configured
- [ ] Database backups scheduled
- [ ] Monitoring & alerting configured
- [ ] Log rotation set up
- [ ] Resource limits configured
- [ ] Health checks passing
- [ ] Tests passing in CI/CD

---

## Support & Resources

- **API Docs**: http://localhost:8000/docs
- **Backend Tests**: `pytest tests/ -v`
- **Frontend Build**: `npm run build`
- **Docker Docs**: https://docs.docker.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

**Last Updated**: 2026-04-25
**Version**: v0.16.0
