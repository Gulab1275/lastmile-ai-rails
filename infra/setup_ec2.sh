#!/usr/bin/env bash
# ==============================================================================
# EC2 Ubuntu 24.04 LTS Automated Provisioning Script
# Coder's Cup '26 - Rahbar Backend & Infra
# Author: Mahandar Khatri (Backend Lead & AWS Infra)
# Target Instance: AWS EC2 t3.small
# ==============================================================================
set -euo pipefail

echo "==> [1/6] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release git ufw fail2ban

echo "==> [2/6] Configuring UFW Firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
echo "y" | sudo ufw enable

echo "==> [3/6] Installing Docker & Docker Compose Plugin..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"

echo "==> [4/6] Creating application directory..."
sudo mkdir -p /opt/rahbar
sudo chown -R "$USER":"$USER" /opt/rahbar

echo "==> [5/6] Setting up DuckDNS Cron Keep-alive (Subdomain: rahbar.duckdns.org)..."
# In production, replace with user DuckDNS token:
# echo 'url="https://www.duckdns.org/update?domains=rahbar&token=YOUR_TOKEN_HERE&ip=" | curl -k -o /var/log/duckdns.log -K -' > /opt/rahbar/duck.sh
# chmod 700 /opt/rahbar/duck.sh
# (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/rahbar/duck.sh >/dev/null 2>&1") | crontab -

echo "==> [6/6] Provisioning complete! Log out and back in to refresh Docker group permissions."
echo "==> To deploy: cd /opt/rahbar && ./infra/deploy.sh"
