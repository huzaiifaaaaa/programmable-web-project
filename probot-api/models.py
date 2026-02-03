from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class UserRole(db.Model):
    __tablename__ = 'user_role'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", backref="role_info", lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    user_key = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    user_role = db.Column(db.Integer, db.ForeignKey('user_role.role_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chats = db.relationship("Chat", backref="owner", lazy=True)

class Model(db.Model):
    __tablename__ = 'models'
    model_id = db.Column(db.Integer, primary_key=True)
    model_key = db.Column(db.String(50), unique=True, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    conversations = db.relationship("Conversation", backref="model_info", lazy=True)

class Chat(db.Model):
    __tablename__ = 'chats'
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_key = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exchanges = db.relationship("Conversation", backref="parent_chat", lazy=True)

class Conversation(db.Model):
    __tablename__ = 'conversation'
    conversation_id = db.Column(db.Integer, primary_key=True)
    conversation_key = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('models.model_id'), nullable=False)
    request = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)