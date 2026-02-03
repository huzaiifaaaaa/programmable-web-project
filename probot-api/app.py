import os
from flask import Flask
from models import db
from initialise import insert_data

def create_app():
    app = Flask(__name__)
    env = os.getenv('APP_ENV', 'stage').lower()
    db_name = f"pro_bot_{env}.db"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.debug = (env == 'stage')
    db.init_app(app)

    with app.app_context():
        db.create_all()
        insert_data()
        print(f"Database initialized: {db_name}!")

    return app

app = create_app()

@app.route('/')
def index():
    env = os.getenv('APP_ENV', 'stage')
    return {
        "message": "ProBot API is running!",
        "environment": env,
        "database": app.config['SQLALCHEMY_DATABASE_URI']
    }

if __name__ == '__main__':
    app.run()