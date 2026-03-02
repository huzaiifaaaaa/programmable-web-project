"""
Authentication utilities for ProBot API.
This module handles JWT generation, decoding, and the auth_required decorator.
"""
import time
from functools import wraps
import jwt
from flask import current_app, request, jsonify

def create_jwt(payload: dict) -> str:
    """
    Generates a signed HS256 JWT for a given user payload.
    """
    now = int(time.time())
    secret = current_app.config["JWT_SECRET"]
    exp = now + int(current_app.config.get("JWT_EXPIRE_SECONDS", 3600))
    claims = {**payload, "iat": now, "exp": exp}
    return jwt.encode(claims, secret, algorithm="HS256")

def decode_jwt(token: str) -> dict:
    """
    Decodes and validates a JWT using the application's secret key.
    """
    secret = current_app.config["JWT_SECRET"]
    return jwt.decode(token, secret, algorithms=["HS256"])

def auth_required(fn):
    """
    Decorator to protect REST endpoints. Requires a valid 'Bearer' token.
    """
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
        except (jwt.InvalidTokenError, jwt.DecodeError):
            # Targeted specific exceptions instead of broad Exception
            return jsonify({"error": "Invalid token"}), 401

        kwargs["claims"] = claims
        return fn(*args, **kwargs)
    return wrapper
