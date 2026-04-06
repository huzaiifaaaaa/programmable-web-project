import os
import sys

import pytest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from probotapi.app import create_app
from probotapi.models import db, UserRole, Model

@pytest.fixture()
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        JWT_SECRET="test-secret",
        JWT_EXPIRE_SECONDS=3600,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        db.session.add(UserRole(role_name="user", description="Default normal user"))
        db.session.add(UserRole(role_name="admin", description="Administrator"))
        db.session.add(Model(model_key="gemini-3-flash-preview", is_active=True))
        db.session.commit()

    yield app

    # teardown
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()