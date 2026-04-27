#!/bin/bash
# start-docker.sh — Start the Trade Analytics Platform with Docker

set -e

cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

echo "🐳 Trade Analytics Platform — Docker Startup"
echo "=============================================="
echo ""

# Step 1: Check Docker
echo "1️⃣  Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
docker --version

# Step 2: Check Docker Compose
echo ""
echo "2️⃣  Checking Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found."
    exit 1
fi
docker compose --version

# Step 3: Check .env file
echo ""
echo "3️⃣  Checking .env file..."
if [ ! -f .env ]; then
    echo "⚠️  .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env (please edit if needed)"
fi

# Step 4: Build images
echo ""
echo "4️⃣  Building Docker images (this may take 2-5 minutes)..."
docker compose build --no-cache

# Step 5: Start services
echo ""
echo "5️⃣  Starting services..."
docker compose up -d

# Step 6: Wait for services
echo ""
echo "6️⃣  Waiting for services to be ready..."
sleep 5

# Step 7: Check status
echo ""
echo "7️⃣  Checking service status..."
docker compose ps

# Step 8: Test API
echo ""
echo "8️⃣  Testing API health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is healthy"
else
    echo "⚠️  API not responding yet (may still be starting)"
fi

# Step 9: Summary
echo ""
echo "✅ Docker services started!"
echo ""
echo "📍 Access the platform:"
echo "   Frontend:  http://localhost"
echo "   API:       http://localhost:8000"
echo "   Docs:      http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f api"
echo "   docker compose logs -f web"
echo ""
echo "🛑 Stop all services:"
echo "   docker compose down"
echo ""
