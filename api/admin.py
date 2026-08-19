# api/admin.py

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, update, func
from typing import Optional

from core.database import AsyncSessionLocal
from models.db_models import User, ChatMessage, Lead, ServiceBooking
from services.whatsapp_service import send_whatsapp_message
from services.openai_service import save_chat_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# --- Models ---
class SendMessageRequest(BaseModel):
    message: str

class ToggleAIRequest(BaseModel):
    pause_ai: bool

# --- Endpoints ---

@router.get("/stats")
async def get_dashboard_stats():
    """
    Returns high-level statistics for the admin dashboard.
    """
    async with AsyncSessionLocal() as session:
        total_users = await session.scalar(select(func.count(User.phone_number)))
        total_leads = await session.scalar(select(func.count(Lead.id)))
        hot_leads = await session.scalar(select(func.count(Lead.id)).where(Lead.intent_score == "HOT"))
        total_bookings = await session.scalar(select(func.count(ServiceBooking.id)))
        active_takeovers = await session.scalar(select(func.count(User.phone_number)).where(User.is_ai_paused == True))

        return {
            "total_users": total_users or 0,
            "total_leads": total_leads or 0,
            "hot_leads": hot_leads or 0,
            "total_bookings": total_bookings or 0,
            "active_takeovers": active_takeovers or 0
        }

@router.get("/chats")
async def list_chats():
    """
    Lists all active conversations with the latest message preview, lead badge, and AI takeover status.
    """
    async with AsyncSessionLocal() as session:
        users_result = await session.execute(select(User).order_by(User.updated_at.desc()))
        users = users_result.scalars().all()

        chat_list = []
        for u in users:
            # Get latest message
            latest_msg_result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.user_phone == u.phone_number)
                .order_by(ChatMessage.created_at.desc())
                .limit(1)
            )
            latest_msg = latest_msg_result.scalar_one_or_none()

            # Get active lead record if any
            lead_result = await session.execute(
                select(Lead)
                .where(Lead.user_phone == u.phone_number)
                .order_by(Lead.created_at.desc())
                .limit(1)
            )
            lead = lead_result.scalar_one_or_none()

            chat_list.append({
                "phone_number": u.phone_number,
                "whatsapp_name": u.whatsapp_name or "Client",
                "preferred_language": u.preferred_language or "english",
                "lead_status": u.lead_status or "new",
                "is_ai_paused": u.is_ai_paused,
                "intent_score": lead.intent_score if lead else None,
                "service_interested": lead.service_interested if lead else None,
                "last_message": latest_msg.content if latest_msg else "No messages yet",
                "last_sender": latest_msg.sender_type if latest_msg else "none",
                "last_activity": latest_msg.created_at.isoformat() if latest_msg else u.created_at.isoformat()
            })

        return chat_list

@router.get("/chats/{phone_number}")
async def get_chat_transcript(phone_number: str):
    """
    Fetches full chronological chat transcript and lead details for a specific user.
    """
    async with AsyncSessionLocal() as session:
        user_result = await session.execute(select(User).where(User.phone_number == phone_number))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Messages
        msgs_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_phone == phone_number)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = msgs_result.scalars().all()

        # Lead profile
        lead_result = await session.execute(
            select(Lead).where(Lead.user_phone == phone_number).order_by(Lead.created_at.desc())
        )
        leads = lead_result.scalars().all()

        # Bookings
        booking_result = await session.execute(
            select(ServiceBooking).where(ServiceBooking.user_phone == phone_number).order_by(ServiceBooking.created_at.desc())
        )
        bookings = booking_result.scalars().all()

        return {
            "user": {
                "phone_number": user.phone_number,
                "whatsapp_name": user.whatsapp_name,
                "preferred_language": user.preferred_language,
                "lead_status": user.lead_status,
                "is_ai_paused": user.is_ai_paused,
                "created_at": user.created_at.isoformat()
            },
            "messages": [
                {
                    "id": m.id,
                    "sender_type": m.sender_type,
                    "content": m.content,
                    "created_at": m.created_at.isoformat()
                }
                for m in messages
            ],
            "leads": [
                {
                    "id": l.id,
                    "client_name": l.client_name,
                    "email": l.email,
                    "service_interested": l.service_interested,
                    "estimated_budget": l.estimated_budget,
                    "intent_score": l.intent_score,
                    "notes": l.qualification_notes,
                    "created_at": l.created_at.isoformat()
                }
                for l in leads
            ],
            "bookings": [
                {
                    "id": b.id,
                    "service_name": b.service_name,
                    "preferred_date_time": b.preferred_date_time,
                    "status": b.booking_status,
                    "created_at": b.created_at.isoformat()
                }
                for b in bookings
            ]
        }

@router.post("/chats/{phone_number}/toggle-ai")
async def toggle_ai_takeover(phone_number: str, payload: ToggleAIRequest):
    """
    Enables or disables Human Takeover mode for a specific chat.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(User)
            .where(User.phone_number == phone_number)
            .values(is_ai_paused=payload.pause_ai)
            .returning(User.is_ai_paused)
        )
        await session.commit()
        updated_state = result.scalar_one_or_none()
        if updated_state is None:
            raise HTTPException(status_code=404, detail="User not found")

        mode_str = "Human Takeover (AI Paused)" if updated_state else "Autonomous AI Active"
        logger.info(f"Chat {phone_number} mode changed to: {mode_str}")
        return {"phone_number": phone_number, "is_ai_paused": updated_state, "mode": mode_str}

from services.telegram_service import send_telegram_message

@router.post("/chats/{phone_number}/send")
async def admin_send_manual_message(phone_number: str, payload: SendMessageRequest):
    """
    Allows the human admin to send a manual reply to the client via WhatsApp Cloud API or Telegram.
    """
    text = payload.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # 1. Send to appropriate channel
        if phone_number.startswith("tg_"):
            await send_telegram_message(to=phone_number, text=text)
        else:
            await send_whatsapp_message(to=phone_number, text=text)

        # 2. Record to DB as human_agent
        await save_chat_message(phone_number, "human_agent", text)

        return {"status": "sent", "phone_number": phone_number, "content": text}
    except Exception as e:
        logger.error(f"Error sending admin manual message to {phone_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
