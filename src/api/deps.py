# src/api/deps.py - Fixed to avoid conflicts

from sqlalchemy.orm import Session
from config.database import get_db  # Import the existing get_db function
from src.models.user import User

# Your existing user management function
def get_or_create_user(session_id: str, db: Session) -> User:
    """Get or create a user based on session_id"""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# You can add other dependency functions here as needed