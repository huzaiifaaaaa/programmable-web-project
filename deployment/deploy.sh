#!/bin/bash
# deploy.sh
# Deploys ProBot API with Gunicorn, Nginx and Supervisor

set -e
APP_DIR=~/programmable-web-project

echo "==> Configuring Supervisor..."
sudo tee /etc/supervisor/conf.d/probotapi.conf > /dev/null <<EOF
[program:probotapi]
command=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 "probotapi.app:app"
directory=$APP_DIR
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/probotapi/probotapi.err.log
stdout_logfile=/var/log/probotapi/probotapi.out.log
EOF

echo "==> Configuring Nginx..."
sudo tee /etc/nginx/sites-available/probotapi > /dev/null <<EOF
server {
    listen 80;
    server_name 86.50.168.242;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name 86.50.168.242;

    ssl_certificate /etc/nginx/ssl/probotapi.crt;
    ssl_certificate_key /etc/nginx/ssl/probotapi.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    access_log /var/log/nginx/probotapi.access.log;
    error_log /var/log/nginx/probotapi.error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "==> Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/probotapi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "==> Starting Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart probotapi

echo "==> Deployment complete! API running at https://86.50.168.242"