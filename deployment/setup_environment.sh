#!/bin/bash
# setup_environment.sh
# Sets up the full environment for ProBot API on Ubuntu 22.04

set -e
echo "==> Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "==> Installing system dependencies..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    git nginx supervisor openssl

echo "==> Creating virtual environment..."
cd ~/programmable-web-project
python3.11 -m venv venv
source venv/bin/activate

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo "==> Creating log directories..."
sudo mkdir -p /var/log/probotapi

echo "==> Generating self-signed SSL certificate..."
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/probotapi.key \
    -out /etc/nginx/ssl/probotapi.crt \
    -subj "/C=FI/ST=Helsinki/L=Helsinki/O=ProBot/CN=86.50.168.242"

echo "==> Environment setup complete!"