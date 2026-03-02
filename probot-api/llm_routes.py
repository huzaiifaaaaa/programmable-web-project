from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime, UTC
from google import genai

from models import db, User, Chat, Conversation, Model
from auth_utils import auth_required

llm_bp = Blueprint("llm", __name__)

def get_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def chat_to_dict(chat: Chat):
    return {
        "chat_id": chat.chat_id,
        "chat_key": chat.chat_key,
        "user_id": chat.user_id,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
    }

def conversation_to_dict(conv: Conversation):
    return {
        "conversation_id": conv.conversation_id,
        "conversation_key": conv.conversation_key,
        "chat_id": conv.chat_id,
        "model_id": conv.model_id,
        "model_key": conv.model_info.model_key if conv.model_info else None,
        "request": conv.request,
        "response": conv.response,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


def _canonical_model_key(model_key: str) -> str:
    """Ensure model key matches expected Google GenAI resource name."""
    key = model_key.strip()
    if not key:
        return key
    if not key.startswith("models/"):
        key = f"models/{key}"
    return key

def _limit_words(text: str, max_words: int = 150) -> str:
    parts = text.split()
    return " ".join(parts[:max_words])


def get_gemini_response(prompt: str, model_key: str) -> tuple[str | None, str | None]:
    """Call Gemini API to get a response for the given prompt.

    Returns (response_text, error_message). Only one will be non-None.
    """
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None, "Gemini API key not configured"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=_canonical_model_key(model_key),
            contents=prompt,
        )
        return _limit_words(response.text or ""), None
    except Exception as e:
        return None, str(e)


# POST /api/v1/chats/
@llm_bp.route("/chats/", methods=["POST"])
@auth_required
def create_chat(claims=None):
    """Create a new chat thread for a user."""
    user_id = claims.get("user_id")
    
    # Verify user exists
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    # Create new chat
    new_chat = Chat(user_id=user_id)
    db.session.add(new_chat)
    
    try:
        db.session.commit()
        return jsonify({"status": "created", "chat": chat_to_dict(new_chat)}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "failed to create chat"}), 500


# GET /api/v1/users/<user_key>/chats/
@llm_bp.route("/users/<string:user_key>/chats/", methods=["GET"])
@auth_required
def list_user_chats(user_key: str, claims=None):
    """List all chat threads for a user."""
    # Verify the requesting user matches the user_key
    if claims.get("user_key") != user_key:
        return jsonify({"error": "forbidden"}), 403
    
    user = User.query.filter_by(user_key=user_key).first()
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    # Get all chats for this user, ordered by most recent first
    chats = Chat.query.filter_by(user_id=user.user_id).order_by(Chat.updated_at.desc()).all()
    
    return jsonify({
        "chats": [chat_to_dict(chat) for chat in chats],
        "count": len(chats)
    }), 200


# POST /api/v1/chats/<chat_key>/messages/
@llm_bp.route("/chats/<string:chat_key>/messages/", methods=["POST"])
@auth_required
def send_message(chat_key: str, claims=None):
    """Send a new message to an existing chat."""
    # Find the chat
    chat = Chat.query.filter_by(chat_key=chat_key).first()
    if not chat:
        return jsonify({"error": "chat not found"}), 404
    
    # Verify the chat belongs to the requesting user
    if chat.user_id != claims.get("user_id"):
        return jsonify({"error": "forbidden"}), 403
    
    data = get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    
    message = (data.get("message") or "").strip()
    default_model = current_app.config.get("GEMINI_MODEL") or "gemini-3-flash-preview"
    model_key = (data.get("model_key") or default_model).strip()
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    
    # Find the model
    model = Model.query.filter_by(model_key=model_key, is_active=True).first()
    if not model:
        return jsonify({"error": f"model '{model_key}' not found or inactive"}), 404
    
    # Get response from Gemini
    llm_response, llm_error = get_gemini_response(message, model_key)
    if llm_error:
        return jsonify({"error": f"llm_error: {llm_error}"}), 502
    
    # Create conversation record
    conversation = Conversation(
        chat_id=chat.chat_id,
        model_id=model.model_id,
        request=message,
        response=llm_response
    )
    
    # Update chat's updated_at timestamp
    chat.updated_at = datetime.now(UTC)
    
    db.session.add(conversation)
    
    try:
        db.session.commit()
        return jsonify({
            "status": "message_sent",
            "conversation": conversation_to_dict(conversation)
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "failed to save conversation"}), 500


# GET /api/v1/chats/<chat_key>/messages/
@llm_bp.route("/chats/<string:chat_key>/messages/", methods=["GET"])
@auth_required
def get_message_history(chat_key: str, claims=None):
    """Get all messages in a chat thread."""
    # Find the chat
    chat = Chat.query.filter_by(chat_key=chat_key).first()
    if not chat:
        return jsonify({"error": "chat not found"}), 404
    
    # Verify the chat belongs to the requesting user
    if chat.user_id != claims.get("user_id"):
        return jsonify({"error": "forbidden"}), 403
    
    # Get all conversations for this chat, ordered chronologically
    conversations = Conversation.query.filter_by(chat_id=chat.chat_id).order_by(Conversation.created_at.asc()).all()
    
    return jsonify({
        "chat": chat_to_dict(chat),
        "messages": [conversation_to_dict(conv) for conv in conversations],
        "count": len(conversations)
    }), 200


# DELETE /api/v1/chats/<chat_key>/
@llm_bp.route("/chats/<string:chat_key>/", methods=["DELETE"])
@auth_required
def delete_chat(chat_key: str, claims=None):
    """Delete a specific chat and all its messages."""
    # Find the chat
    chat = Chat.query.filter_by(chat_key=chat_key).first()
    if not chat:
        return jsonify({"error": "chat not found"}), 404
    
    # Verify the chat belongs to the requesting user
    if chat.user_id != claims.get("user_id"):
        return jsonify({"error": "forbidden"}), 403
    
    # Delete the chat (conversations will be deleted via cascade if configured)
    db.session.delete(chat)
    
    try:
        db.session.commit()
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "failed to delete chat"}), 500
