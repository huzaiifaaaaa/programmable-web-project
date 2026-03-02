"""
ProBot DB initialisation.
"""
import os
from models import db, UserRole, Model, User

def insert_data():
    """Seed database."""
    print(" * Ensuring default database data...")

    # Ensure default role
    user_role = UserRole.query.filter_by(role_name="user").first()
    if user_role is None:
        user_role = UserRole(role_name="user", description="Standard user")
        db.session.add(user_role)
        db.session.commit()
        print(" * Created role 'user'")

    # Ensure default models based on env (change GEMINI_MODEL in .env to switch)
    env_model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    default_models = [env_model]
    created_models = []
    for key in default_models:
        if Model.query.filter_by(model_key=key).first() is None:
            db.session.add(Model(model_key=key))
            created_models.append(key)
    if created_models:
        db.session.commit()
        print(f" * Added models: {', '.join(created_models)}")

    # Seed a demo user if missing
    if User.query.filter_by(email="john@programmableweb.com").first() is None:
        admin_user = User(
            name="John PW",
            email="john@programmableweb.com",
            password="hashed_password_123",
            user_role=user_role.role_id,
            is_active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f" * Created default user: {admin_user.email}")

    print(" * Default data ensured")
