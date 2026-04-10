#!/bin/bash
# test_environment.sh
# Verifies the environment is correctly configured

PASS=0
FAIL=0

check() {
    if eval "$2" > /dev/null 2>&1; then
        echo "[PASS] $1"
        PASS=$((PASS+1))
    else
        echo "[FAIL] $1"
        FAIL=$((FAIL+1))
    fi
}

echo "==> Running environment checks..."
echo ""

check "Python 3.11 installed"        "python3.11 --version"
check "pip installed"                "pip --version"
check "Gunicorn installed"           "~/programmable-web-project/venv/bin/gunicorn --version"
check "Nginx installed"              "nginx -v"
check "Supervisor installed"         "supervisord --version"
check "SSL certificate exists"       "test -f /etc/nginx/ssl/probotapi.crt"
check "SSL key exists"               "test -f /etc/nginx/ssl/probotapi.key"
check "Nginx config valid"           "sudo nginx -t"
check "Nginx is running"             "systemctl is-active nginx"
check "Supervisor is running"        "systemctl is-active supervisor"
check "ProBot process running"       "sudo supervisorctl status probotapi | grep RUNNING"
check "API responding on port 5000"  "curl -s http://127.0.0.1:5000 | grep -q ProBot"
check "API responding via Nginx HTTP" "curl -s http://86.50.168.242 | grep -q ProBot"
check "API responding via HTTPS"     "curl -sk https://86.50.168.242 | grep -q ProBot"

echo ""
echo "==> Results: $PASS passed, $FAIL failed"