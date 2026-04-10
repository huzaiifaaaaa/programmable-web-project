# ProBot API
**PWP SPRING 2026**

### Group Information
* **Student 1:** Muhammad Huzaifa (Muhammad.Huzaifa@student.oulu.fi)
* **Student 2:** Safi Shah (Safi.Shah@student.oulu.fi)
* **Student 3:** Zhenfei Sun (Zhenfei.Sun@student.oulu.fi)

---

## 1. Project Structure

The project follows a modular structure to ensure maintainability and high code quality.

```text
programmable-web-project/
├── probotapi/
│   ├── app.py              # Application factory and entry point
│   ├── auth_utils.py       # JWT logic and @auth_required decorator
│   ├── initialise.py       # Default data insertion (Models & Admin)
│   ├── models.py           # SQLAlchemy Database Models
│   ├── routes/
│   │   ├── user_routes.py  # REST Resources and Route handlers for user endpoints
│   │   └── llm_routes.py   # REST Resources and Route handlers for llm endpoints
│   ├── seed_roles.py       # Script for initial UserRole population
│   ├── extensions.py       # Flask extensions (cache, etc.)
│ 	└── tests/
│     	├── conftest.py         # Pytest fixtures and DB setup
│ 		├── test_llm_routes.py  
│ 		├── test_seed_roles.py  
│ 		├── conftest.py         # Pytest fixtures and DB setup
│     	└── test_api.py         # API functional test suite
├── deployment/
│   ├── setup_environment.sh    # Installs all dependencies and SSL certs
│   ├── deploy.sh               # Deploys configs and starts services
│   ├── test_environment.sh     # Verifies environment is correctly configured
│   ├── nginx/
│   │   └── probotapi.conf      # Nginx reverse proxy config
│   └── supervisor/
│       └── probotapi.conf      # Supervisor process config
├── requirements.txt        # External library dependencies
├── pyproject.toml          # Packaging configuration
└── .env.example            # Environment variable template
```

---

## 2. Deployment (Production)

The API is deployed on **CSC cPouta** (OpenStack VM) and publicly accessible at:

```
https://86.50.168.242
```

> Note: A self-signed SSL certificate is used. Your browser may show a security warning — click **Advanced → Proceed** to continue. For API clients use the `-k` flag: `curl -k https://86.50.168.242`

### 2.1 Deployment Components

| Component | Role |
|-----------|------|
| Ubuntu 22.04 LTS | Base OS on cPouta VM |
| Python 3.11 | Application runtime |
| Flask | WSGI web framework |
| Gunicorn | Production WSGI app server (4 workers) |
| Nginx | Reverse proxy, HTTP→HTTPS redirect, SSL termination |
| Supervisor | Process monitor — auto-start and auto-restart on crash |
| SQLite | File-based persistent database |
| OpenSSL | Self-signed SSL certificate generation |

### 2.2 Prerequisites

* A running Ubuntu 22.04 VM on CSC cPouta
* A floating public IP assigned to the VM
* Security group rules allowing ports **22**, **80**, and **443**
* SSH access to the VM

### 2.3 Setup Environment

SSH into the VM and clone the repository on the `prod` branch:

```bash
ssh ubuntu@86.50.168.242
git clone -b prod https://github.com/your-username/programmable-web-project.git
cd programmable-web-project
```

Run the setup script:

```bash
chmod +x deployment/setup_environment.sh
./deployment/setup_environment.sh
```

This will:
- Install Python 3.11, Nginx, Supervisor, and OpenSSL
- Create a Python virtual environment and install all dependencies
- Generate a self-signed SSL certificate valid for 365 days
- Create log directories at `/var/log/probotapi/`

### 2.4 Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Set the following values:

```env
APP_ENV=prod
JWT_SECRET=your-long-random-secret
JWT_EXPIRE_SECONDS=3600
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
```

### 2.5 Deploy

```bash
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

This will:
- Copy Nginx and Supervisor configs from the repo
- Enable the Nginx site and restart the service
- Start the ProBot API process under Supervisor

### 2.6 Verify Deployment

```bash
chmod +x deployment/test_environment.sh
./deployment/test_environment.sh
```

Expected output:

```
==> Running environment checks...

[PASS] Python 3.11 installed
[PASS] pip installed
[PASS] Gunicorn installed
[PASS] Nginx installed
[PASS] Supervisor installed
[PASS] SSL certificate exists
[PASS] SSL key exists
[PASS] Nginx config valid
[PASS] Nginx is running
[PASS] Supervisor is running
[PASS] ProBot process running
[PASS] API responding on port 5000
[PASS] API responding via Nginx HTTP
[PASS] API responding via HTTPS

==> Results: 14 passed, 0 failed
```

---

## 3. Local Setup & Execution

### 3.1 Dependencies

This project requires **Python 3.11+**.

* **Flask / Flask-SQLAlchemy**: Core web framework and ORM.
* **PyJWT / Werkzeug**: Security, JWT authentication, and password hashing.
* **PyTest / Coverage**: Functional testing and reporting.
* **Flask-Smorest**: OpenAPI/Swagger documentation generation.

### 3.2 Installation & Database Setup

1. **Environment**:

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configuration**: Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `APP_ENV` | Selects DB file name (default: `stage`) |
| `JWT_SECRET` | Secret for signing JWTs |
| `JWT_EXPIRE_SECONDS` | Token lifetime in seconds |
| `GEMINI_API_KEY` | Required for LLM responses — get one at https://aistudio.google.com/api-keys |
| `GEMINI_MODEL` | Default LLM model key (e.g. `gemini-3-flash-preview`) |

3. **Database**: The API is self-provisioning. To manually seed roles:

```bash
python seed_roles.py
```

4. **Run**:

```bash
python probotapi/app.py
```

* **Local Entry Point**: `http://127.0.0.1:5000/`
* **Production URL**: `https://86.50.168.242/`
* * **API Docs (Swagger)**: `[[http://127.0.0.1:5000/](https://app.swaggerhub.com/apis/universityofoulu-bc7/pwp-probot-api/1.0.0)](https://app.swaggerhub.com/apis/universityofoulu-bc7/pwp-probot-api/1.0.0)`

5. **Packaging**:

```bash
pip install -e .
python -m probotapi.app
```

---

## 4. Testing

### 4.1 Run Tests with Coverage

```bash
coverage run -m pytest tests/test_api.py
coverage report -m
```

### 4.2 Environment Tests (Production)

To verify the production deployment is correctly configured:

```bash
./deployment/test_environment.sh
```

### 4.3 Manual API Tests

Test the live API using curl:

```bash
# Health check
curl -k https://86.50.168.242/
```

---

## 5. Sample Requests

All endpoints are prefixed with `/api/v1/`. Use the `-k` flag with curl for self-signed SSL.

- **Signup** `POST /api/v1/signup/`
```json
{"name": "Alice", "email": "alice@example.com", "password": "secret123"}
```

- **Login** `POST /api/v1/login/`
```json
{"email": "alice@example.com", "password": "secret123"}
```

- **Create chat** `POST /api/v1/chats/` *(Auth: Bearer \<token\>)*
```json
{}
```

- **List user chats** `GET /api/v1/users/<user_key>/chats/` *(Auth)*
  - No body

- **Send message** `POST /api/v1/chats/<chat_key>/messages/` *(Auth)*
```json
{
  "message": "Explain Gemini briefly",
  "model_key": "gemini-3-flash-preview"
}
```

- **Get chat history** `GET /api/v1/chats/<chat_key>/messages/` *(Auth)*
  - No body

- **Delete chat** `DELETE /api/v1/chats/<chat_key>/` *(Auth)*
  - No body

---

## 6. Managing the Application (Production)

```bash
# Check status
sudo supervisorctl status probotapi

# Restart API
sudo supervisorctl restart probotapi

# View application logs
tail -f /var/log/probotapi/probotapi.out.log
tail -f /var/log/probotapi/probotapi.err.log

# View Nginx logs
tail -f /var/log/nginx/probotapi.access.log
tail -f /var/log/nginx/probotapi.error.log

# Pull latest code and redeploy
git pull origin prod
sudo supervisorctl restart probotapi
```

---

## 7. SSL Certificate Management

Certificates are generated automatically by `setup_environment.sh` and stored at:

| File | Path |
|------|------|
| Certificate | `/etc/nginx/ssl/probotapi.crt` |
| Private key | `/etc/nginx/ssl/probotapi.key` |

To regenerate manually:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/probotapi.key \
    -out /etc/nginx/ssl/probotapi.crt \
    -subj "/C=FI/ST=Helsinki/L=Helsinki/O=ProBot/CN=86.50.168.242"
sudo systemctl restart nginx
```
