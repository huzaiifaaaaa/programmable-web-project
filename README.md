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
