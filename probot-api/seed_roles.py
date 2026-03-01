from app import create_app
from models import db, UserRole

def seed():
    app = create_app()
    with app.app_context():
        roles = [
            ("user", "Default normal user"),
            ("admin", "Administrator"),
        ]
        for name, desc in roles:
            exists = UserRole.query.filter_by(role_name=name).first()
            if not exists:
                db.session.add(UserRole(role_name=name, description=desc))
        db.session.commit()
        print("seed roles done")

if __name__ == "__main__":
    seed()