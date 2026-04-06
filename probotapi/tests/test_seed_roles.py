"""Tests for role seeding script behavior."""

import importlib
import sys
import types


def _load_seed_module(monkeypatch, fake_create_app, fake_db, fake_user_role):
    app_module = types.ModuleType("app")
    app_module.create_app = fake_create_app

    models_module = types.ModuleType("models")
    models_module.db = fake_db
    models_module.UserRole = fake_user_role

    monkeypatch.setitem(sys.modules, "app", app_module)
    monkeypatch.setitem(sys.modules, "models", models_module)
    sys.modules.pop("probotapi.seed_roles", None)

    return importlib.import_module("probotapi.seed_roles")


def test_seed_roles_adds_missing_roles(monkeypatch, app):
    existing = {}
    added = []
    committed = {"value": 0}

    class FakeQuery:
        def filter_by(self, role_name):
            class _Result:
                @staticmethod
                def first():
                    return existing.get(role_name)

            return _Result()

    class FakeUserRole:
        query = FakeQuery()

        def __init__(self, role_name, description):
            self.role_name = role_name
            self.description = description

    class FakeSession:
        @staticmethod
        def add(role):
            added.append((role.role_name, role.description))
            existing[role.role_name] = role

        @staticmethod
        def commit():
            committed["value"] += 1

    fake_db = types.SimpleNamespace(session=FakeSession())

    module = _load_seed_module(monkeypatch, lambda: app, fake_db, FakeUserRole)
    module.seed()

    assert ("user", "Default normal user") in added
    assert ("admin", "Administrator") in added
    assert committed["value"] == 1


def test_seed_roles_skips_existing_roles(monkeypatch, app):
    existing = {
        "user": object(),
        "admin": object(),
    }
    added = []
    committed = {"value": 0}

    class FakeQuery:
        def filter_by(self, role_name):
            class _Result:
                @staticmethod
                def first():
                    return existing.get(role_name)

            return _Result()

    class FakeUserRole:
        query = FakeQuery()

        def __init__(self, role_name, description):
            self.role_name = role_name
            self.description = description

    class FakeSession:
        @staticmethod
        def add(role):
            added.append((role.role_name, role.description))

        @staticmethod
        def commit():
            committed["value"] += 1

    fake_db = types.SimpleNamespace(session=FakeSession())

    module = _load_seed_module(monkeypatch, lambda: app, fake_db, FakeUserRole)
    module.seed()

    assert added == []
    assert committed["value"] == 1