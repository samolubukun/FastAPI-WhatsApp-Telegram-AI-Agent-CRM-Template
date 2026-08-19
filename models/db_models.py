# models/db_models.py

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """
    Represents a WhatsApp contact/client.
    """
    __tablename__ = "users"

    phone_number = Column(String(50), primary_key=True, index=True)
    whatsapp_name = Column(String(100), nullable=True)
    preferred_language = Column(String(20), default="english")  # english, yoruba, hausa, igbo, pidgin
    lead_status = Column(String(30), default="new")  # new, contacted, qualified, booked, cold
    is_ai_paused = Column(Boolean, default=False)  # True = Human Takeover Active
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("ServiceBooking", back_populates="user", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Chronological record of every incoming and outgoing WhatsApp message.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_phone = Column(String(50), ForeignKey("users.phone_number"), index=True, nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'user', 'ai', 'human_agent'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="messages")


class Lead(Base):
    """
    Qualified lead profile captured by the AI agent during conversation.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_phone = Column(String(50), ForeignKey("users.phone_number"), index=True, nullable=False)
    client_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    company_or_niche = Column(String(100), nullable=True)
    service_interested = Column(String(100), nullable=True)
    estimated_budget = Column(String(50), nullable=True)
    intent_score = Column(String(20), default="WARM")  # HOT, WARM, COLD
    language_used = Column(String(20), default="english")
    qualification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="leads")


class ServiceBooking(Base):
    """
    Consultation / Strategy session booked by the AI agent or human.
    """
    __tablename__ = "service_bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_phone = Column(String(50), ForeignKey("users.phone_number"), index=True, nullable=False)
    service_name = Column(String(100), nullable=False)
    preferred_date_time = Column(String(100), nullable=True)
    project_description = Column(Text, nullable=True)
    booking_status = Column(String(30), default="pending")  # pending, confirmed, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="bookings")
