# AWS EC2 Deployment Guide (Docker Compose)

This repository is already containerized (`Dockerfile`, `Dockerfile.frontend`, `docker-compose.yml`), so the recommended AWS path is:

**EC2 (Ubuntu) + Docker Compose + Nginx + Certbot**

---

## 1) Provision AWS Infrastructure

Create an Ubuntu 22.04/24.04 EC2 instance (recommended: `t3.medium` or higher):

- Attach an **Elastic IP**
- Security Group inbound rules:
  - `80/tcp` from `0.0.0.0/0`
  - `443/tcp` from `0.0.0.0/0`
  - `22/tcp` from **your IP only**
- Do **not** expose `5432` (PostgreSQL) or `6379` (Redis) publicly

---

## 2) Prepare EC2 Host

SSH into EC2 and run:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/<YOUR_ORG_OR_USER>/trading-analytics-platform/main/deploy/aws/ec2-bootstrap.sh)"
```

Or copy and run locally from repo:

```bash
chmod +x deploy/aws/ec2-bootstrap.sh
sudo ./deploy/aws/ec2-bootstrap.sh
```

This installs:

- Docker Engine + Compose plugin
- Nginx
- Certbot
- AWS CLI
- CloudWatch Agent

---

## 3) Deploy Repository on EC2

```bash
git clone https://github.com/Dhritisman007/trading-analytics-platform.git
cd trading-analytics-platform
cp .env.example .env
```

Set production values in `.env`:

- `SECRET_KEY` (strong random)
- `DATABASE_URL=postgresql://trading_user:<strong_password>@postgres:5432/trading_db`
- `REDIS_URL=redis://redis:6379`
- `DEBUG=False`
- Optional API keys (`UPSTOX_*`, `NEWSAPI_KEY`, `OPENAI_API_KEY`)

Update compose credentials in `/home/ubuntu/trading-analytics-platform/docker-compose.yml` for production:

- `POSTGRES_PASSWORD`
- `POSTGRES_USER` / `POSTGRES_DB` as needed

Then deploy:

```bash
chmod +x deploy/aws/scripts/deploy-compose.sh
./deploy/aws/scripts/deploy-compose.sh
```

---

## 4) Domain + HTTPS

1. Point your domain A record to the EC2 Elastic IP.
2. Copy nginx template:

```bash
sudo cp deploy/aws/nginx/trading-platform.conf /etc/nginx/sites-available/trading-platform.conf
```

3. Replace `example.com` with your real domain in that file.
4. Enable config:

```bash
sudo ln -sf /etc/nginx/sites-available/trading-platform.conf /etc/nginx/sites-enabled/trading-platform.conf
sudo nginx -t
sudo systemctl reload nginx
```

5. Enable TLS:

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

Nginx terminates TLS and proxies traffic to the frontend container on `localhost:3000`.

---

## 5) Persist, Backup, and Operate

### Volumes

Persistence is already handled by Docker volumes in `docker-compose.yml`:

- `postgres_data`
- `redis_data`
- model artifacts under `./models:/app/models`

### Postgres backup to S3

```bash
chmod +x deploy/aws/scripts/backup-postgres-to-s3.sh
S3_BUCKET=my-trading-backups AWS_REGION=ap-south-1 ./deploy/aws/scripts/backup-postgres-to-s3.sh
```

Schedule with cron (example: every day 2:30 AM):

```bash
crontab -e
30 2 * * * cd /home/ubuntu/trading-analytics-platform && S3_BUCKET=my-trading-backups AWS_REGION=ap-south-1 ./deploy/aws/scripts/backup-postgres-to-s3.sh >> /var/log/trading-backup.log 2>&1
```

### Health checks

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:3000/
```

### Monitoring

- CloudWatch Agent installed via bootstrap script
- Send system/docker logs and metrics per your CloudWatch config

---

## 6) Optional CI/CD (GitHub Actions + ECR + EC2)

Workflow: `.github/workflows/deploy-aws-ec2.yml`

It can:

- Build backend/frontend images
- Push both to Amazon ECR
- SSH into EC2 and refresh containers

Required GitHub repository secrets:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME` (OIDC role)
- `ECR_REPOSITORY_API`
- `ECR_REPOSITORY_FRONTEND`
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_PRIVATE_KEY`
- `EC2_APP_DIR` (example: `/home/ubuntu/trading-analytics-platform`)

Required EC2 env file for ECR deployment:

- `${EC2_APP_DIR}/deploy/aws/.ecr.env` with:

```env
ECR_API_IMAGE=<account>.dkr.ecr.<region>.amazonaws.com/<api-repo>:latest
ECR_FRONTEND_IMAGE=<account>.dkr.ecr.<region>.amazonaws.com/<frontend-repo>:latest
```

And deploy with compose override:

```bash
docker compose -f docker-compose.yml -f deploy/aws/docker-compose.ec2.yml pull

docker compose -f docker-compose.yml -f deploy/aws/docker-compose.ec2.yml up -d
```

---

## Verification Checklist

- [ ] Frontend reachable on domain over HTTPS
- [ ] `GET /health` returns 200
- [ ] Postgres/Redis not publicly exposed
- [ ] Backups written to S3
- [ ] Nginx and Docker restart on reboot
- [ ] CI/CD secrets configured (if using Actions deploy)
