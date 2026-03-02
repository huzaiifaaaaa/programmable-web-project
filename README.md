# PWP SPRING 2026
# PROJECT NAME: ProBot
# Group information
* Student 1. Muhammad Huzaifa (Muhammad.Huzaifa@student.oulu.fi)
* Student 2. Safi Shah (Safi.Shah@student.oulu.fi)
* Student 3. Zhenfei Sun (Zhenfei.Sun@student.oulu.fi)

---

# Deliverable 2 - Database Implementation

## 1. Directory Structure
```
probot-api/
├── app.py # Contains the Flask app
├── models.py # Contains all 5 data models
├── initialise.py # Seeds the database, inserts default values
├── requirements.txt # Generated via pip freeze
├── instance/pro_bot_stage.db # SQLite database generated after running the app
```

## 2. Project Dependencies

This project requires **Python 3.x** and the following external libraries:

- **Flask** – Web framework for the API  
- **Flask-SQLAlchemy** – ORM for database interactions  

### Installation

Install dependencies using:

```bash
pip install -r requirements.txt
```

## 3. Database Specification

- Database Engine: SQLite 3

- ORM: SQLAlchemy (via Flask-SQLAlchemy)

- SQLite Version: SQLite 3.x (bundled with Python)

## 4. Setup and Configuration

- Virtual Environment
```
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

- Environment Variable    
The application uses the APP_ENV environment variable to determine the database name:
```
stage → pro_bot_stage.db
production → pro_bot_production.db
```

### If not set, the default environment is stage.

## 5. Database Setup and Population
The database is self provisioning. No manual SQL scripts are required.

### Automatic Creation
- When the application starts, it checks for the existence of the .db file.
- If the file does not exist, db.create_all() is executed to create all tables.

### Automatic Seeding
- The insert_data() function in app.py automatically inserts default records.

### Running the Application

```
python app.py
```

### Generating requirements.txt
```
pip install flask flask-sqlalchemy
pip freeze > requirements.txt
```

## 6. API Overview

### 6.1 Resource Table
| Resource | Methods | Path | Auth | Notes |
| --- | --- | --- | --- | --- |
| Users | POST | /api/v1/signup/ | No | Create user account |
| Users | POST | /api/v1/login/ | No | Obtain JWT token |
| Users | GET | /api/v1/users/<user_key>/ | Yes | Get own profile |
| Users | PUT | /api/v1/users/<user_key>/ | Yes | Update own profile (no role change) |
| Users | DELETE | /api/v1/users/<user_key>/ | Yes | Delete own account |
| Chats | POST | /api/v1/chats/ | Yes | Create chat thread |
| Chats | GET | /api/v1/users/<user_key>/chats/ | Yes | List user chats |
| Chat Messages | POST | /api/v1/chats/<chat_key>/messages/ | Yes | Send message (LLM) |
| Chat Messages | GET | /api/v1/chats/<chat_key>/messages/ | Yes | Chat history |
| Chats | DELETE | /api/v1/chats/<chat_key>/ | Yes | Delete chat (cascades messages) |

### 6.2 Addressability
- Every user has stable `user_key` (UUID) used in user and chat listing URIs.
- Chats have `chat_key` (UUID) used to fetch messages and continue conversations.
- Models referenced by `model_key` in requests; stored in `models` table.

### 6.3 Uniform Interface
- POST creates resources (`/signup/`, `/chats/`, `/chats/<chat_key>/messages/`).
- GET retrieves resources (`/users/<user_key>/`, `/users/<user_key>/chats/`, `/chats/<chat_key>/messages/`).
- PUT updates mutable user fields (`/users/<user_key>/`).
- DELETE removes resources (`/users/<user_key>/`, `/chats/<chat_key>/`).
- JSON request/response bodies; errors as `{ "error": "..." }`.

### 6.4 Statelessness
- JWT carries auth context; server does not keep session state.
- Each request is authenticated/authorized via token and path parameters; no server-side session storage.

### 6.5 Connectedness
- User → Chats via `user_key` and `user_id`; list at `/users/<user_key>/chats/`.
- Chat → Messages via `chat_key` and `chat_id`; history at `/chats/<chat_key>/messages/`.
- Conversation rows link to Model via `model_id` to record which LLM answered.

### 6.6 Sample Requests (JSON)
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

## 7. Running & Testing

### 7.1 Run the API
```
python app.py
```

### 7.2 Environment
- Copy `.env.example` to `.env` and fill values.
- `APP_ENV` (default `stage`) selects DB file name.
- `JWT_SECRET` secret for signing JWTs.
- `JWT_EXPIRE_SECONDS` token lifetime in seconds.
- `GEMINI_API_KEY` required for LLM responses (get one at https://aistudio.google.com/api-keys).
- `GEMINI_MODEL` default LLM model key (e.g., `gemini-3-flash-preview`).

### 7.3 Tests
```
pytest
```
Add `--cov` to measure coverage once tests are expanded.
