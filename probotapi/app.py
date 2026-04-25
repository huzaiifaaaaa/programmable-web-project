"""
ProBot Application Factory.
This module initializes the Flask app, configures the database, and registers blueprints.
"""
import os
import sys
from flask import Flask, request
from flask_cors import CORS

# Support running `python app.py` from inside the `probotapi` directory.
if __name__ == "__main__" and __package__ is None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from probotapi.models import db
from probotapi.initialise import insert_data
from probotapi.routes.user_routes import api_bp as user_bp
from probotapi.routes.llm_routes import llm_bp
from probotapi.extensions import cache
from flask_smorest import Api

def create_app():
    """
    Initialize and configure the Flask application.
    Returns:
        Flask: The configured application instance.
    """
    flask_app = Flask(__name__)
    env = os.getenv('APP_ENV', 'stage').lower()
    db_name = f"pro_bot_{env}.db"

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:////data/{db_name}"
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.config["JWT_SECRET"] = os.getenv("JWT_SECRET", "CHANGE_ME_TO_RANDOM_LONG_SECRET")
    flask_app.config["JWT_EXPIRE_SECONDS"] = int(os.getenv("JWT_EXPIRE_SECONDS", "3600"))
    flask_app.config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    # Default model is driven by .env; change there to switch models
    flask_app.config["GEMINI_MODEL"] = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    flask_app.config["CACHE_TYPE"] = "SimpleCache"
    flask_app.config["CACHE_DEFAULT_TIMEOUT"] = 60
    # flask_app.register_blueprint(user_bp, url_prefix="/api/v1")
    # flask_app.register_blueprint(llm_bp, url_prefix="/api/v1")

    flask_app.config["API_TITLE"] = "Pro Bot API"
    flask_app.config["API_VERSION"] = "v1"
    flask_app.config["OPENAPI_VERSION"] = "3.0.3"
    flask_app.config["OPENAPI_URL_PREFIX"] = "/"
    flask_app.config["OPENAPI_JSON_PATH"] = "openapi.json"
    flask_app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
    flask_app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    flask_app.debug = env == 'stage'
    db.init_app(flask_app)
    cache.init_app(flask_app)

    CORS(
        flask_app,
        origins=["https://pwp.cloverta.top"],
        supports_credentials=True,
    )

    @flask_app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")

        if origin == "https://pwp.cloverta.top":
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, If-None-Match"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Expose-Headers"] = "ETag"

        return response

    api = Api(flask_app)

    api.register_blueprint(user_bp, url_prefix="/api/v1")
    api.register_blueprint(llm_bp, url_prefix="/api/v1")

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
