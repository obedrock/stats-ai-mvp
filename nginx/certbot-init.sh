#!/bin/bash
# Run once on first deploy to get initial certificate
set -e

DOMAIN=${1:?Usage: certbot-init.sh <domain>}

# Stop nginx if running
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true

# Get certificate using standalone mode
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email admin@${DOMAIN} \
  --agree-tos \
  --no-eff-email \
  -d ${DOMAIN}

echo "Certificate obtained for ${DOMAIN}"
echo "Now run: ./deploy.sh"
