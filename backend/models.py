from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ai_sessions = relationship("AISession", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class AISession(Base):
    __tablename__ = "ai_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    language = Column(String, default="en")
    duration_minutes = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    meeting_id = Column(String, nullable=True)
    meeting_platform = Column(String, nullable=True)  # 'zoom' or 'google_meet'
    status = Column(String, default="active")  # active, completed, terminated
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="ai_sessions")
    messages = relationship("SessionMessage", back_populates="session")

class SessionMessage(Base):
    __tablename__ = "session_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    language = Column(String, default="en")
    audio_duration = Column(Float, nullable=True)  # Duration in seconds for voice messages
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("AISession", back_populates="messages")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stripe_payment_id = Column(String, unique=True, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd")
    plan_type = Column(String, nullable=False)  # 'premium', 'enterprise'
    status = Column(String, default="pending")  # pending, completed, failed, refunded
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    display_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)  # JSON string of interests/tags
    emotional_needs = Column(Text, nullable=True)  # JSON string of emotional support needs
    timezone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
