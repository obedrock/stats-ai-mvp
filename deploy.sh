#!/bin/bash
set -e

echo "=== Stats-AI Deployment ==="

# Check required env vars
: ${DOMAIN_NAME:?Set DOMAIN_NAME in .env}
: ${SECRET_KEY:?Set SECRET_KEY in .env}
: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}

# Load .env
set -a
source .env
set +a

# 1. Build R sandbox image
echo "Building R sandbox image..."
docker build -t stats-ai-r-sandbox r-sandbox/

# 2. Substitute domain in nginx config
echo "Configuring nginx for ${DOMAIN_NAME}..."
envsubst '${DOMAIN_NAME}' < nginx/nginx.conf > /tmp/nginx-stats-ai.conf
cp /tmp/nginx-stats-ai.conf nginx/nginx.conf.rendered
# Use rendered config
cp nginx/nginx.conf.rendered nginx/nginx.conf

# 3. Build frontend
echo "Building frontend..."
cd frontend
VITE_API_URL="/api" npm run build
sudo mkdir -p /var/www/stats-ai
sudo cp -r dist/* /var/www/stats-ai/
cd ..

# 4. Run database migrations
echo "Running migrations..."
docker compose -f docker-compose.prod.yml up -d postgres redis
sleep 5
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic upgrade head

# 5. Start all services
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "=== Deployment complete ==="
echo "Visit https://${DOMAIN_NAME}"
