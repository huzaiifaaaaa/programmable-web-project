"""
ProBot User routes.
Handles registration, authentication, and CRUD operations for user profiles.
"""
import hashlib
from flask import Blueprint, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from models import db, User, UserRole
from auth_utils import create_jwt, auth_required

api_bp = Blueprint("api", __name__)

DEFAULT_ROLE_NAME = "user"

def get_json():
    """Extracts JSON from request body safely."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def user_to_dict(u: User):
    """Serializes user model to dictionary with HATEOAS links."""
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
    """Fetches default user role or returns a 500 error tuple."""
    role = UserRole.query.filter_by(role_name=DEFAULT_ROLE_NAME).first()
    if not role:
        msg = f"default role '{DEFAULT_ROLE_NAME}' not found, seed roles first"
        return None, (jsonify({"error": msg}), 500)
    return role, None

def make_user_etag(u: User) -> str:
    base = f"{u.user_key}:{u.updated_at.isoformat() if u.updated_at else ''}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# POST /api/v1/signup/
@api_bp.route("/signup/", methods=["POST"])
def signup():
    """Register a new user account."""
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
    """Authenticate user and return JWT."""
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

    token = create_jwt({
        "user_key": u.user_key,
        "user_id": u.user_id,
        "role_id": u.user_role
    })
    return jsonify({"token": token, "user": user_to_dict(u)}), 200

# GET /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["GET"])
@auth_required
def get_user(user_key: str, claims=None):
    """Retrieve public profile for a specific user."""
    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403

    u = User.query.filter_by(user_key=user_key).first()
    if not u:
        return jsonify({"error": "user not found"}), 404

    etag = make_user_etag(u)
    inm = request.headers.get("If-None-Match")

    if inm == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "private, max-age=60"
        return resp

    resp = jsonify(user_to_dict(u))
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "private, max-age=60"
    return resp, 200

# PUT /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["PUT"])
@auth_required
def update_user(user_key: str, claims=None):
    """Update user profile information."""
    # 1. Consolidate access and existence checks
    user = User.query.filter_by(user_key=user_key).first()
    if not user or claims.get("user_key") != user_key:
        status = 404 if not user else 403
        return jsonify({"error": "user not found" if not user else "forbidden"}), status

    data = get_json()
    if not data:
        return jsonify({"error": "Invalid request or role modification"}), 400
    if "user_role" in data:
        return jsonify({"error": "User role cannot be modified"}), 403
    # 2. Consolidate validation logic into one check
    error = None
    if "name" in data and not (data["name"] or "").strip():
        error = "name cannot be empty"
    elif "email" in data and not (data["email"] or "").strip():
        error = "email cannot be empty"
    elif "password" in data and len(data.get("password", "")) < 6:
        error = "password too short (>=6)"

    if error:
        return jsonify({"error": error}), 400

    # Update logic
    if "name" in data:
        user.name = data["name"].strip()
    if "email" in data:
        user.email = data["email"].strip().lower()
    if "password" in data:
        user.password = generate_password_hash(data["password"])

    # 3. Handle database commit
    try:
        db.session.commit()
        return jsonify({"status": "updated", "user": user_to_dict(user)}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "email already exists"}), 409

# DELETE /api/v1/users/<user_key>/
@api_bp.route("/users/<string:user_key>/", methods=["DELETE"])
@auth_required
def delete_user(user_key: str, claims=None):
    """Remove user account from system."""
    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403

    u = User.query.filter_by(user_key=user_key).first()
    if not u:
        return jsonify({"error": "user not found"}), 404

    db.session.delete(u)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200
