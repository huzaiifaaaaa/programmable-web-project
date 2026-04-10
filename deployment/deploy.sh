#!/bin/bash
# deploy.sh
set -e
APP_DIR=~/programmable-web-project

echo "==> Copying Supervisor config..."
sudo cp $APP_DIR/deployment/supervisor/probotapi.conf /etc/supervisor/conf.d/probotapi.conf

echo "==> Copying Nginx config..."
sudo cp $APP_DIR/deployment/nginx/probotapi.conf /etc/nginx/sites-available/probotapi
sudo ln -sf /etc/nginx/sites-available/probotapi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "==> Testing Nginx config..."
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "==> Starting Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart probotapi

echo "==> Deployment complete! API running at https://86.50.168.242"