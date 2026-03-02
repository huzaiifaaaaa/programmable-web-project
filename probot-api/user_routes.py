"""
ProBot User routes.
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from models import db, User, UserRole
from auth_utils import create_jwt, auth_required

api_bp = Blueprint("api", __name__)

DEFAULT_ROLE_NAME = "user"

def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def user_to_dict(u: User):
    user_uri = f"/api/v1/users/{u.user_key}/"
    
    return {
        "user_id": u.user_id,
        "user_key": u.user_key,
        "user_role": u.user_role,
        "role_name": u.role_info.role_name if u.role_info else None,
        "name": u.name,
        "email": u.email,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "links": [
            {"rel": "self", "href": user_uri},
            {"rel": "chats", "href": f"{user_uri}chats/"}
        ]
    }

def get_default_role_or_500():
    role = UserRole.query.filter_by(role_name=DEFAULT_ROLE_NAME).first()
    if not role:
        return None, (jsonify({"error": f"default role '{DEFAULT_ROLE_NAME}' not found, seed roles first"}), 500)
    return role, None


# POST /api/v1/signup/
@api_bp.route("/signup/", methods=["POST"])
def signup():
    data = get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, password are required"}), 400

    role, err = get_default_role_or_500()
    if err:
        return err

    u = User(
        user_role=role.role_id,
        name=name,
        email=email,
        password=generate_password_hash(password),
        is_active=True,
    )

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "email already exists"}), 409

    return jsonify({"status": "created", "user": user_to_dict(u)}), 201


# POST /api/v1/login/
@api_bp.route("/login/", methods=["POST"])
def login():
    data = get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password, password):
        return jsonify({"error": "invalid credentials"}), 401
    if not u.is_active:
        return jsonify({"error": "user is inactive"}), 403

    token = create_jwt({"user_key": u.user_key, "user_id": u.user_id, "role_id": u.user_role})
    return jsonify({"token": token, "user": user_to_dict(u)}), 200


# GET /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["GET"])
@auth_required
def get_user(user_key: str, claims=None):

    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403

    u = User.query.filter_by(user_key=user_key).first()
    if not u:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user_to_dict(u)), 200


# PUT /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["PUT"])
@auth_required
def update_user(user_key: str, claims=None):
    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403

    u = User.query.filter_by(user_key=user_key).first()
    if not u:
        return jsonify({"error": "user not found"}), 404

    data = get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    if "user_role" in data:
        return jsonify({"error": "user_role cannot be modified"}), 403

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty"}), 400
        u.name = name

    if "email" in data:
        email = (data["email"] or "").strip().lower()
        if not email:
            return jsonify({"error": "email cannot be empty"}), 400
        u.email = email

    if "password" in data:
        pwd = data["password"] or ""
        if len(pwd) < 6:
            return jsonify({"error": "password too short (>=6)"}), 400
        u.password = generate_password_hash(pwd)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "email already exists"}), 409

    return jsonify({"status": "updated", "user": user_to_dict(u)}), 200


# DELETE /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["DELETE"])
@auth_required
def delete_user(user_key: str, claims=None):
    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403

    u = User.query.filter_by(user_key=user_key).first()
    if not u:
        return jsonify({"error": "user not found"}), 404

    db.session.delete(u)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200