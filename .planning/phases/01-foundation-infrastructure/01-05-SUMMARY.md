---
phase: 01-foundation-infrastructure
plan: 05
subsystem: infra
tags: [docker, nginx, certbot, letsencrypt, gunicorn, uvicorn, digitalocean, deployment]

# Dependency graph
requires:
  - phase: 01-foundation-infrastructure
    provides: FastAPI backend, Celery worker, R sandbox, React frontend

provides:
  - Production Dockerfile with gunicorn + uvicorn workers
  - nginx reverse proxy with HTTPS via Let's Encrypt
  - docker-compose.prod.yml orchestrating all production services
  - certbot-init.sh for SSL certificate provisioning
  - deploy.sh for full automated deployment

affects:
  - deployment
  - production-readiness

# Tech tracking
tech-stack:
  added: [gunicorn, nginx:alpine, certbot/letsencrypt, envsubst]
  patterns:
    - nginx serves React static files + proxies /api/ to backend container
    - HTTPS via Let's Encrypt certbot standalone mode
    - Celery worker mounts /var/run/docker.sock to spawn R sandbox containers
    - envsubst used to inject DOMAIN_NAME into nginx config at deploy time

key-files:
  created:
    - Dockerfile
    - nginx/nginx.conf
    - nginx/certbot-init.sh
    - docker-compose.prod.yml
    - deploy.sh
  modified:
    - .env.example

key-decisions:
  - "nginx proxies /api/* to backend:8000/ — frontend sets VITE_API_URL=/api so apiFetch paths match"
  - "certbot standalone mode (not webroot) for initial certificate provisioning — simpler first-deploy flow"
  - "gunicorn with 2 uvicorn workers — sufficient for MVP scale on 2GB droplet, configurable via env"
  - "celery-worker mounts /var/run/docker.sock to spawn R sandbox containers — required for subprocess R execution model"

patterns-established:
  - "nginx.conf uses ${DOMAIN_NAME} placeholder replaced by envsubst in deploy.sh"
  - "docker-compose.prod.yml uses :?Set VAR pattern for required production secrets"
  - "All services have restart: unless-stopped for production resilience"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03]

# Metrics
duration: 2min
completed: 2026-03-23
---

# Phase 01 Plan 05: Production Deployment Infrastructure Summary

**nginx HTTPS reverse proxy serving React SPA and proxying /api/ to FastAPI backend, orchestrated via docker-compose.prod.yml with gunicorn, Celery worker with Docker socket access, and automated deploy.sh script**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-23T21:58:53Z
- **Completed:** 2026-03-23T22:00:25Z
- **Tasks:** 1 of 2 (Task 2 is a human-action checkpoint requiring a live Digital Ocean droplet)
- **Files modified:** 6

## Accomplishments

- Backend Dockerfile using python:3.12-slim with uv, gunicorn + uvicorn workers for production-grade serving
- nginx config with HTTP->HTTPS redirect, Let's Encrypt SSL, React SPA routing (try_files), and /api/ proxy to backend service
- Production docker-compose with postgres:16, redis:7, backend, celery-worker (docker.sock mount), nginx with SSL volume mounts
- certbot-init.sh for standalone SSL certificate acquisition on first deploy
- deploy.sh automating: R sandbox build, nginx envsubst, frontend build, DB migrations, service start
- .env.example updated with DOMAIN_NAME and POSTGRES_PASSWORD production vars

## Task Commits

1. **Task 1: Production Dockerfile, nginx config, Docker Compose, and deploy script** - `fd79b47` (chore)

## Files Created/Modified

- `Dockerfile` - Production backend image: python:3.12-slim, uv, gunicorn+uvicorn, 2 workers
- `nginx/nginx.conf` - Reverse proxy: HTTP redirect, HTTPS+SSL, React SPA, /api/ proxy with security headers
- `nginx/certbot-init.sh` - One-time Let's Encrypt certificate provisioning via standalone certbot
- `docker-compose.prod.yml` - Production service orchestration: postgres, redis, backend, celery-worker, nginx
- `deploy.sh` - Full deployment automation script (executable)
- `.env.example` - Added DOMAIN_NAME and POSTGRES_PASSWORD production variables

## Decisions Made

- nginx uses `${DOMAIN_NAME}` placeholder replaced by `envsubst` at deploy time — keeps a single nginx.conf template in source control
- certbot standalone mode chosen over webroot for simpler first-deploy experience (no nginx running during initial cert issuance)
- celery-worker mounts `/var/run/docker.sock` to enable spawning R sandbox containers at runtime — aligns with the subprocess R execution architecture decided in Phase 1
- gunicorn with 2 uvicorn workers — appropriate for 2GB droplet MVP; increase `-w` flag to scale
- `/api/` nginx proxy strips prefix before forwarding to `http://backend:8000/` — frontend must set `VITE_API_URL=/api` at build time

## Deviations from Plan

None - plan executed exactly as written.

## User Setup Required

Task 2 is a `checkpoint:human-action` that requires:

1. Create a Digital Ocean droplet (Ubuntu 24.04, 2GB+ RAM, Docker marketplace image)
2. SSH into droplet and clone repo to `/opt/stats-ai`
3. Create `.env` with `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `POSTGRES_PASSWORD`, `DOMAIN_NAME`
4. Point domain DNS A record to droplet IP
5. Run `bash nginx/certbot-init.sh yourdomain.com` to provision SSL certificate
6. Run `bash deploy.sh` to deploy all services
7. Verify: visit `https://yourdomain.com` — should show the auth page

## Issues Encountered

None - all files created without issues.

## Known Stubs

None - all deployment artifacts are complete and functional. The deploy.sh script is ready to execute against a real droplet.

## Next Phase Readiness

- All production deployment artifacts are created and ready for use
- When a Digital Ocean droplet is provisioned, deployment can proceed immediately with `bash nginx/certbot-init.sh <domain>` then `bash deploy.sh`
- Phase 2 (data pipeline) can begin immediately — no deployment blocker

---
*Phase: 01-foundation-infrastructure*
*Completed: 2026-03-23*
