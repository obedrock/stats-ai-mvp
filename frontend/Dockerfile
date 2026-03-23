FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files first for layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
ENV VITE_API_URL=/api
RUN npm run build

# Use busybox to copy built files into the shared volume at runtime
FROM busybox:stable
COPY --from=build /app/dist /dist
CMD ["cp", "-r", "/dist/.", "/var/www/stats-ai/"]
