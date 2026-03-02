"""
ProBot Authentication utils.
"""
import time
import jwt
from functools import wraps
from flask import current_app, request, jsonify

def create_jwt(payload: dict) -> str:
    now = int(time.time())
    secret = current_app.config["JWT_SECRET"]
    exp = now + int(current_app.config.get("JWT_EXPIRE_SECONDS", 3600))
    claims = {**payload, "iat": now, "exp": exp}
    return jwt.encode(claims, secret, algorithm="HS256")

def decode_jwt(token: str) -> dict:
    secret = current_app.config["JWT_SECRET"]
    return jwt.decode(token, secret, algorithms=["HS256"])

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            claims = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        kwargs["claims"] = claims
        return fn(*args, **kwargs)
    return wrapper