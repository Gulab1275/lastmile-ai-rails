#!/usr/bin/env bash
# ==============================================================================
# EC2 Automated Provisioning Script (Supports Ubuntu, Amazon Linux 2023, & RHEL)
# Coder's Cup '26 - Rahbar Backend & Infra
# Author: Mahandar Khatri (Backend Lead & AWS Infra)
# Target Instance: AWS EC2 (t3.small or t2.micro)
# ==============================================================================
set -euo pipefail

echo "==> [1/4] Detecting OS distribution and installing Docker..."

if command -v apt-get &> /dev/null; then
    echo "Detected Ubuntu / Debian system (apt-get)..."
    sudo apt-get update && sudo apt-get upgrade -y
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release git

    # Docker official repository
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"

elif command -v dnf &> /dev/null; then
    echo "Detected Amazon Linux 2023 / Fedora (dnf)..."
    sudo dnf update -y
    sudo dnf install -y docker git --allowerasing
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"

    # Install Docker Compose Plugin
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -sSL https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64 -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"

    # Also symlink globally if possible
    sudo ln -sf "$DOCKER_CONFIG/cli-plugins/docker-compose" /usr/local/bin/docker-compose 2>/dev/null || true

elif command -v yum &> /dev/null; then
    echo "Detected Amazon Linux 2 / CentOS (yum)..."
    sudo yum update -y
    sudo yum install -y docker git curl
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER"

    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -sSL https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64 -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
    sudo ln -sf "$DOCKER_CONFIG/cli-plugins/docker-compose" /usr/local/bin/docker-compose 2>/dev/null || true
else
    echo "ERROR: Unsupported package manager. Please install Docker manually."
    exit 1
fi

echo "==> [2/4] Verifying Docker installation..."
docker --version || sudo docker --version

echo "==> [3/4] Creating application directories..."
mkdir -p "$HOME/lastmile-ai-rails"

echo "==> [4/4] Provisioning complete!"
echo "==> IMPORTANT: Log out and back in to refresh Docker group permissions:"
echo "    exit"
echo "==> Then reconnect and launch the stack:"
echo "    cd lastmile-ai-rails"
echo "    docker compose -f infra/docker-compose.yml up -d --build"
