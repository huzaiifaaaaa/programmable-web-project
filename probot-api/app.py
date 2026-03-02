"""
ProBot Application Factory.
This module initializes the Flask app, configures the database, and registers blueprints.
"""
import os
from flask import Flask
from models import db
from initialise import insert_data
from user_routes import api_bp as user_bp
from llm_routes import llm_bp

def create_app():
    """
    Initialize and configure the Flask application.
    Returns:
        Flask: The configured application instance.
    """
    flask_app = Flask(__name__)
    env = os.getenv('APP_ENV', 'stage').lower()
    db_name = f"pro_bot_{env}.db"

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_name}"
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.config["JWT_SECRET"] = os.getenv("JWT_SECRET", "CHANGE_ME_TO_RANDOM_LONG_SECRET")
    flask_app.config["JWT_EXPIRE_SECONDS"] = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))
    flask_app.config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    # Default model is driven by .env; change there to switch models
    flask_app.config["GEMINI_MODEL"] = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    flask_app.register_blueprint(user_bp, url_prefix="/api/v1")
    flask_app.register_blueprint(llm_bp, url_prefix="/api/v1")

    flask_app.debug = env == 'stage'
    db.init_app(flask_app)

    with flask_app.app_context():
        db.create_all()
        insert_data()
        print(f"Database initialized: {db_name}!")

    return flask_app

app = create_app()

@app.route('/')
def index():
    """
    Root endpoint providing API status and environment info.
    """
    env = os.getenv('APP_ENV', 'stage')
    return {
        "message": "ProBot API is running!",
        "environment": env,
        "database": app.config['SQLALCHEMY_DATABASE_URI']
    }

if __name__ == '__main__':
    app.run()