
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
probot-api/
├── app.py              # Application factory and entry point
├── auth_utils.py       # JWT logic and @auth_required decorator
├── initialise.py       # Default data insertion (Models & Admin)
├── models.py           # SQLAlchemy Database Models
├── user_routes.py      # REST Resources and Route handlers for user endpoints
├── llm_routes.py      # REST Resources and Route handlers for llm endpoints
├── seed_roles.py       # Script for initial UserRole population
├── requirements.txt    # External library dependencies
└── tests/
    ├── conftest.py     # Pytest fixtures and DB setup
    └── test_api.py     # API functional test suite

```

---

## 2. Setup & Execution

### 2.1 Dependencies

This project requires **Python 3.12+**.

* **Flask / Flask-SQLAlchemy**: Core web framework and ORM.
* **PyJWT / Werkzeug**: Security, JWT authentication, and password hashing.
* **PyTest / Coverage**: Functional testing and reporting.
* **Flask-SQLAlchemy**: ORM for SQLite.
* **Werkzeug**: Security and password hashing.

### 2.2 Installation & Database Setup

1. **Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

- Copy `.env.example` to `.env` and fill values.
- `APP_ENV` (default `stage`) selects DB file name.
- `JWT_SECRET` secret for signing JWTs.
- `JWT_EXPIRE_SECONDS` token lifetime in seconds.
- `GEMINI_API_KEY` required for LLM responses (get one at https://aistudio.google.com/api-keys).
- `GEMINI_MODEL` default LLM model key (e.g., `gemini-3-flash-preview`).

2. **Configuration**: Copy `.env.example` to `.env` and configure `JWT_SECRET` and `GEMINI_API_KEY`.
3. **Database**: The API is self-provisioning. To manually seed roles:
```bash
python seed_roles.py

```


4. **Run**:
```bash
python app.py

```

* **Local Entry Point**: `http://127.0.0.1:5000/api/v1/`
* **Remote Access URL**: `https://[YOUR-DEPLOYED-URL]/api/v1/`

4. **Packagin**:
```bash
pip install -e .     
python -m probotapi.app

```

5. **Testing & Coverage**

```bash
# Run tests with coverage
coverage run -m pytest tests/test_api.py

# Generate report for screen share
coverage report -m

```
---

## 3. Sample Requests

- Signup `POST /api/v1/signup/`
	```json
	{"name": "Alice", "email": "alice@example.com", "password": "secret123"}
	```
- Login `POST /api/v1/login/`
	```json
	{"email": "alice@example.com", "password": "secret123"}
	```
- Create chat `POST /api/v1/chats/` (Auth: Bearer <token>)
	```json
	{}
	```
- List user chats `GET /api/v1/users/<user_key>/chats/` (Auth)
	- No body
- Send message `POST /api/v1/chats/<chat_key>/messages/` (Auth)
	```json
	{
		"message": "Explain Gemini briefly",
		"model_key": "gemini-3-flash-preview"  // optional; defaults to GEMINI_MODEL
	}
	```
- Get chat history `GET /api/v1/chats/<chat_key>/messages/` (Auth)
	- No body
- Delete chat `DELETE /api/v1/chats/<chat_key>/` (Auth)
	- No body
---

## 4. AI Disclosure

* **Tool**: Gemini 1.5 Flash.
* **Usage**: Used for structuring this README, generating resource tables, and functional test headers.

---
