# POSTGRESQL_SETUP_GUIDE.md

## PostgreSQL Setup Guide for Trade Analytics Platform

**Date**: April 14, 2026  
**Purpose**: Complete guide for setting up PostgreSQL for production use  
**Database**: PostgreSQL 15+ with SQLAlchemy ORM  
**Status**: ✅ Production Ready

---

## Why PostgreSQL?

**SQLite Limitations:**
- ❌ Single-writer limitation (one query at a time)
- ❌ Issues when scheduler + API write simultaneously
- ❌ Not suitable for concurrent operations
- ❌ Poor performance under load

**PostgreSQL Advantages:**
- ✅ Full ACID transactions
- ✅ Concurrent read/write support
- ✅ Proper locking mechanisms
- ✅ Production-grade reliability
- ✅ Better performance with indexes
- ✅ Advanced query capabilities

---

## Installation on macOS

### Step 1: Install PostgreSQL

```bash
# Using Homebrew (recommended)
brew install postgresql@15

# Verify installation
postgres --version
# Output: postgres (PostgreSQL) 15.x
```

### Step 2: Start PostgreSQL Service

```bash
# Start PostgreSQL service
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
# Output: postgresql@15  started ...

# Or start manually
pg_ctl -D /opt/homebrew/var/postgres start
```

### Step 3: Add to PATH

```bash
# Add to ~/.zshrc (for zsh shell) or ~/.bash_profile (for bash)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Reload shell
source ~/.zshrc

# Verify
which psql
# Output: /opt/homebrew/opt/postgresql@15/bin/psql
```

---

## Database Creation

### Create Main Database

```bash
# Create trading_db
createdb trading_db

# Verify creation
psql -l
# Shows: trading_db | postgres | UTF8 | ...
```

### Test Connection

```bash
# Connect to database
psql trading_db

# Inside psql, run:
SELECT version();
-- Output: PostgreSQL 15.x on ...

# Exit psql
\q
```

### Create Additional Databases (Optional)

```bash
# Test database for unit tests
createdb trading_db_test

# Backup/staging database
createdb trading_db_backup

# Verify all
psql -l
```

---

## Configuration

### Update .env File

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env
nano .env
```

### Set DATABASE_URL

```bash
# .env
DATABASE_URL="postgresql://localhost/trading_db"

# For production with password:
# DATABASE_URL="postgresql://username:password@host:port/trading_db"
```

### Verify Connection

```bash
# Test connection from Python
python3 << 'EOF'
from sqlalchemy import create_engine, text

url = "postgresql://localhost/trading_db"
engine = create_engine(url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✅ Connection successful:", result.fetchone())
EOF
```

---

## Database Initialization

### Automatic (Recommended)

```bash
# Start the application — tables are created automatically
cd "/Users/dhritismansarma/Desktop/Trade Analytics Platform"
source venv/bin/activate
uvicorn main:app --reload

# Watch logs:
# ... Database tables initialized successfully ...
```

### Manual

```bash
# Initialize database manually
python3 << 'EOF'
from core.database import init_db
init_db()
print("✅ Database tables created")
EOF
```

### Verify Tables Created

```bash
# Connect to database
psql trading_db

# List tables
\dt
```

Output should show:
```
                List of relations
 Schema |        Name         | Type  |  Owner
--------+---------------------+-------+-----------
 public | backtest_results    | table | postgres
 public | fiidii_flows        | table | postgres
 public | news_articles       | table | postgres
 public | predictions         | table | postgres
 public | trades              | table | postgres
 public | user_preferences    | table | postgres
 (6 rows)
```

### View Table Structure

```bash
# View specific table schema
psql trading_db -c "\d trades"

# View all column details
psql trading_db -c "SELECT * FROM information_schema.columns WHERE table_name = 'trades';"
```

---

## Data Types Mapping

How Python ORM types map to PostgreSQL:

```
Python/SQLAlchemy          →  PostgreSQL
─────────────────────────────────────────────
Integer                    →  INTEGER
String(50)                 →  VARCHAR(50)
Float                      →  DOUBLE PRECISION
DateTime                   →  TIMESTAMP WITHOUT TIME ZONE
Boolean                    →  BOOLEAN
Text                       →  TEXT
Enum                       →  VARCHAR (with CHECK constraint)
```

---

## Common Operations

### Connect to Database

```bash
# Interactive connection
psql trading_db

# Run single command
psql trading_db -c "SELECT COUNT(*) FROM trades;"

# With output to file
psql trading_db -c "SELECT * FROM trades;" > output.csv
```

### Query Examples

```bash
# Inside psql:

-- Count trades
SELECT COUNT(*) FROM trades;

-- Get trades from last 7 days
SELECT * FROM trades 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Get trade statistics
SELECT 
    signal,
    grade,
    COUNT(*) as count,
    AVG(ml_confidence) as avg_confidence
FROM trades
GROUP BY signal, grade
ORDER BY count DESC;

-- Get prediction accuracy
SELECT 
    symbol,
    COUNT(*) as total,
    SUM(CASE WHEN correct = true THEN 1 ELSE 0 END) as correct,
    (SUM(CASE WHEN correct = true THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100) as accuracy
FROM predictions
GROUP BY symbol;

-- Get latest FII/DII flow
SELECT * FROM fiidii_flows 
ORDER BY date DESC 
LIMIT 1;
```

---

## Backups

### Backup Database

```bash
# Backup to SQL file
pg_dump trading_db > trading_db_backup.sql

# Backup specific table
pg_dump trading_db -t trades > trades_backup.sql

# Compressed backup (recommended for large databases)
pg_dump trading_db | gzip > trading_db_backup.sql.gz

# With date timestamp
pg_dump trading_db | gzip > "trading_db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
```

### Restore Database

```bash
# Restore from SQL file
psql trading_db < trading_db_backup.sql

# Restore from compressed backup
gunzip -c trading_db_backup.sql.gz | psql trading_db

# Restore specific table
psql trading_db < trades_backup.sql
```

### Backup Strategy

```bash
# Create backup script
mkdir -p backups
cat > backups/backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump trading_db | gzip > "backups/trading_db_$TIMESTAMP.sql.gz"
echo "✅ Backup completed: backups/trading_db_$TIMESTAMP.sql.gz"
EOF

chmod +x backups/backup.sh

# Schedule daily backups with cron (optional)
# 0 2 * * * /path/to/backups/backup.sh  (runs at 2 AM daily)
```

---

## Performance Tuning

### Basic Indexes

```bash
# Indexes already created via SQLAlchemy models:
-- Trades
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_created_at ON trades(created_at);

-- Predictions
CREATE INDEX idx_predictions_symbol ON predictions(symbol);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);

-- FII/DII
CREATE INDEX idx_fiidii_date ON fiidii_flows(date);

-- News
CREATE INDEX idx_news_url ON news_articles(url UNIQUE);
CREATE INDEX idx_news_published ON news_articles(published_at);
```

### Check Index Usage

```bash
psql trading_db << 'EOF'
-- Show index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Show missing indexes
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY tablename;
EOF
```

### Connection Pool Monitoring

```python
from core.database import engine

# Check pool status
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
```

---

## Troubleshooting

### Issue: "Connection refused"

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running, start it
brew services start postgresql@15

# Or start manually
pg_ctl -D /opt/homebrew/var/postgres start
```

### Issue: "database does not exist"

```bash
# Create the database
createdb trading_db

# Or specify port if non-standard
createdb -h localhost -p 5432 trading_db

# Verify
psql -l | grep trading_db
```

### Issue: "permission denied"

```bash
# Login as postgres user
sudo -u postgres psql

# Inside psql:
ALTER DATABASE trading_db OWNER TO postgres;
GRANT ALL PRIVILEGES ON DATABASE trading_db TO postgres;

# Exit
\q
```

### Issue: "too many connections"

```bash
# Check current connections
psql trading_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection limit
psql -t -c "SHOW max_connections;"

# Increase if needed (in postgresql.conf):
# max_connections = 200
```

### Issue: "out of disk space"

```bash
# Check database size
psql trading_db -c "SELECT pg_size_pretty(pg_database_size('trading_db'));"

# Check table sizes
psql trading_db << 'EOF'
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

---

## Production Deployment

### Pre-Deployment Checklist

```bash
# ✅ PostgreSQL installed and running
brew services list | grep postgresql

# ✅ Database created
psql -l | grep trading_db

# ✅ Connection verified
python3 -c "from core.database import engine; print('✅ Connected')"

# ✅ Tables created
psql trading_db -c "\dt"

# ✅ Environment variables set
grep DATABASE_URL .env

# ✅ All tests passing
pytest tests/ -v

# ✅ Application starts
uvicorn main:app --reload
```

### Docker Setup (Optional)

```dockerfile
# Dockerfile for PostgreSQL
FROM postgres:15-alpine

ENV POSTGRES_DB=trading_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

VOLUME ["/var/lib/postgresql/data"]
EXPOSE 5432
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Run with Docker

```bash
docker-compose up -d

# Verify
docker-compose ps

# Connect
psql -h localhost -U postgres -d trading_db
```

---

## Security Best Practices

### Development

```bash
# Use local connection (default)
DATABASE_URL="postgresql://localhost/trading_db"
```

### Production

```bash
# Use strong credentials
DATABASE_URL="postgresql://user:strong_password@production.db.server:5432/trading_db"

# OR use environment secrets
# DATABASE_URL from AWS Secrets Manager, GCP Secret Manager, etc.
```

### SSL Connection (Production)

```bash
# Enable SSL
DATABASE_URL="postgresql://user:password@host:5432/trading_db?sslmode=require"

# In sqlalchemy
from sqlalchemy import create_engine
engine = create_engine(
    url,
    connect_args={
        "sslmode": "require",
        "sslcert": "/path/to/client-cert.pem",
        "sslkey": "/path/to/client-key.pem",
        "sslrootcert": "/path/to/ca-cert.pem",
    }
)
```

### User Permissions

```bash
# Create dedicated database user
psql << 'EOF'
CREATE USER trading_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE trading_db TO trading_app;
GRANT USAGE ON SCHEMA public TO trading_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_app;
EOF
```

---

## Monitoring & Maintenance

### Regular Maintenance

```bash
# Vacuum (reclaim space)
vacuumdb trading_db

# Analyze (update statistics)
analyzedb trading_db

# Reindex (rebuild indexes)
reindexdb trading_db

# Or combined
vacuumdb --analyze --reindex trading_db
```

### Check Database Health

```bash
psql trading_db << 'EOF'
-- Unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Slow queries (requires log_statement enabled)
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table bloat
SELECT 
    schemaname,
    tablename,
    ROUND(100 * (CASE WHEN otta > 0 THEN sml.relpages - otta ELSE 0 END) / sml.relpages) AS table_bloat_ratio
FROM pg_class
LIMIT 10;
EOF
```

---

## Next Steps

1. ✅ Install PostgreSQL
2. ✅ Create database
3. ✅ Configure .env
4. ✅ Initialize tables
5. ✅ Run application
6. 📊 Monitor performance
7. 📅 Set up backups
8. 🔒 Implement security

---

**Status**: Ready for production! 🚀

For issues or questions, check troubleshooting section above or refer to:
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- psycopg2 Driver: https://www.psycopg.org/
