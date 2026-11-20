#!/usr/bin/env bash
# ==============================================================================
# Zero-Downtime Deployment Script for Rahbar API Gateway
# Author: Mahandar Khatri (Backend Lead & AWS Infra)
# ==============================================================================
set -euo pipefail

echo "==> Pulling latest code from origin/main..."
git pull origin main

echo "==> Building and starting containers with Docker Compose..."
docker compose -f infra/docker-compose.yml build --pull
docker compose -f infra/docker-compose.yml up -d --remove-orphans

echo "==> Waiting for API health check..."
sleep 5
for i in {1..12}; do
    if curl -s -f http://localhost:8000/api/v1/health | grep -q '"status":"healthy"'; then
        echo "==> Deployment SUCCESS! API Gateway is healthy."
        exit 0
    fi
    echo "Waiting for health check... ($i/12)"
    sleep 3
done

echo "==> ERROR: Deployment health check failed!"
docker compose -f infra/docker-compose.yml logs api
exit 1
