
# PWP SPRING 2026
# PROJECT NAME: ProBot
# Group information
* Student 1. Muhammad Huzaifa (Muhammad.Huzaifa@student.oulu.fi)
* Student 2. Safi Shah (Safi.Shah@student.oulu.fi)
* Student 3. Zhenfei Sun (Zhenfei.Sun@student.oulu.fi)

---

## 1. Project Structure

The project follows a modular structure to avoid "single-file application" penalties.

```text
probot-api/
├── app.py              # Application factory and entry point
├── auth_utils.py       # JWT logic and @auth_required decorator
├── initialise.py       # Default data insertion (Models & Admin)
├── models.py           # SQLAlchemy Database Models
├── routes.py           # REST Resources and Route handlers
├── seed_roles.py       # Script for initial UserRole population
├── requirements.txt    # External library dependencies
└── tests/
    ├── conftest.py     # Pytest fixtures and DB setup
    └── test_api.py     # API functional test suite

```

## 2. Dependencies

This project requires **Python 3.12+**. Key libraries include:

* **Flask**: Web framework.
* **Flask-SQLAlchemy**: ORM for SQLite.
* **PyJWT**: Token-based authentication.
* **Werkzeug**: Security and password hashing.
* **PyTest & Coverage**: Testing and reporting.

### Installation

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate # Windows

pip install -r requirements.txt

```

## 3. Database Setup & Population

The API is designed to be self-provisioning.

1. **Automated Seeding**: When `app.py` runs, it automatically creates the SQLite database and calls `insert_data()` from `initialise.py` to add default roles and a test user.
2. **Manual Seeding**: To ensure roles exist before first run:
```bash
python seed_roles.py

```



## 4. Execution & Entry Point

To run the API locally:

```bash
python app.py

```

* **Local Entry Point**: `http://127.0.0.1:5000/api/v1/`
* **Remote Access URL**: `https://[YOUR-DEPLOYED-URL]/api/v1/`

## 5. Testing & Coverage

To demonstrate the **96%+ coverage** requirement:

```bash
# Run tests with coverage
coverage run -m pytest tests/test_api.py

# Generate report for screen share
coverage report -m

```

---

## 6. Code Documentation (Public Methods)

As per grading criteria, all public methods are documented below:

| Function | Method | Description | Input | Output |
| --- | --- | --- | --- | --- |
| `signup` | `POST` | Registers a new user. | JSON: `name`, `email`, `password` | `201 Created` |
| `login` | `POST` | Authenticates and returns JWT. | JSON: `email`, `password` | `200 OK` + Token |
| `get_user` | `GET` | Fetches a user's own profile. | `user_key` (URL) | `200 OK` |
| `update_user` | `PUT` | Updates profile information. | JSON: `name`, `email`, or `password` | `200 OK` |
| `delete_user` | `DELETE` | Removes a user account. | `user_key` (URL) | `200 OK` |
| `create_jwt` | N/A | Generates a signed HS256 token. | Payload dictionary | String (JWT) |
| `auth_required` | N/A | Decorator for protected routes. | Request Header (Bearer Token) | Authorized view |

**Exceptions Handling**:

* `401 Unauthorized`: Missing or expired JWT.
* `403 Forbidden`: Attempting to modify `user_role` or access another user's profile.
* `409 Conflict`: Attempting to register or update to an existing email.

---

## 7. AI

* **AI Tool**: Gemini 1.5 Flash.
* **Prompts used**: "Help me generate a README template based on these grading criteria".

