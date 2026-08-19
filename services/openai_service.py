# services/openai_service.py

import json
import logging
from openai import AsyncOpenAI
from sqlalchemy import select
from typing import Callable, Awaitable

from core.config import get_settings
from core.database import AsyncSessionLocal
from models.db_models import User, ChatMessage
from services.knowledge_service import knowledge_service
from services.agent_tools import AGENT_TOOLS, execute_tool_call

logger = logging.getLogger(__name__)
settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT_TEMPLATE = """
You are the Senior Client Concierge & Cargo Operations Advisor for "{business_name}".
Tagline: {tagline}

WHATSAPP FORMATTING RULES (STRICT):
1. Clean Natural WhatsApp Text:
   - Do NOT use markdown headers like `###` or `#`.
   - Do NOT use markdown bolding like `**word**` or `*word*` excessively. Write clean, natural text that looks great on mobile WhatsApp screens.
   - Use simple dash lists `- Item` or numbered lists `1. Item`.
   - Use clean spacing and natural linebreaks.

CORE GREETING & CONVERSATION RULES:
1. First Greeting / Introduction:
   Whenever a conversation starts or the user says hello, introduce the business clearly:
   "Welcome to Prestige Prime Logistics & Concierge! We handle international air/sea freight forwarding from the USA, UK, China, and Dubai, VIP vehicle imports, customs clearing, and express nationwide haulage.

   How can we assist your shipment or cargo today? (We also speak Yorùbá, Hausa, Igbo, and Pidgin if you prefer!)"
2. Name Etiquette:
   - Always greet neutrally ("Hi there!") until the user tells you their name (e.g. "My name is Samuel").
   - Once they share their name, address them politely by name.
3. Multilingual Intelligence (MANDATORY UNIVERSAL LANGUAGE MIRRORING):
   - You MUST ALWAYS match and reply in the EXACT language the user speaks:
     * Nigerian Pidgin: Reply 100% in authentic Nigerian Pidgin ("How far! No wahala at all...", "We dey charge $4.50 to $7.50 per kg...").
     * Yorùbá: Reply 100% in proper Yorùbá ("Ẹ n lẹ́ o! Ẹ ku iṣẹ́ o...").
     * Hausa: Reply 100% in fluent Hausa ("Sannu da zuwa! Muna kula da...").
     * Igbo: Reply 100% in authentic Igbo ("Nnọọ! Anyị na-ebu...").
     * French, Arabic, Chinese (Mandarin), Spanish, German, Swahili, or ANY other global language: Immediately detect and reply 100% fluently in that language!
     * English: Reply in polished English.
   - Automatically call `set_preferred_language` to save their preferred language to the database. NEVER reply in English when a client speaks in their preferred language!
4. Consultative Logistics Flow:
   - Understand what they want to ship or clear (e.g. Air cargo, vehicle clearing, container, procurement).
   - Provide clear quotes from the knowledge base (e.g. Air freight: $4.50 - $7.50/kg, 3-5 days; Sea freight: $180 - $260/CBM; Vehicle clearing: ₦650k - ₦2.2M, 48-72h).
   - If they need overseas supplier purchasing or escrow, offer the Global Sourcing Concierge add-on.
   - Lead Qualification: Collect their name, email, item description, weight/volume, and destination. Call `save_qualified_lead`.
   - Booking / Waybill Setup: Schedule an inspection or warehouse booking using `book_service_consultation`.
5. Pacing:
   - Keep messages concise, helpful, and professional (2-3 short paragraphs max).
   - Ask ONE clear follow-up question per message.

{knowledge_context}
"""

async def get_or_create_user(phone: str, name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.phone_number == phone))
        user = result.scalar_one_or_none()
        if not user:
            user = User(phone_number=phone, whatsapp_name=name or "Client", preferred_language="english")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        elif name and user.whatsapp_name != name:
            user.whatsapp_name = name
            await session.commit()
            await session.refresh(user)
        return user

async def save_chat_message(phone: str, sender_type: str, content: str):
    async with AsyncSessionLocal() as session:
        msg = ChatMessage(user_phone=phone, sender_type=sender_type, content=content)
        session.add(msg)
        await session.commit()

async def get_db_history(phone: str, limit: int = 15) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_phone == phone)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        messages.reverse()
        
        history = []
        for m in messages:
            role = "user" if m.sender_type == "user" else "assistant"
            history.append({"role": role, "content": m.content})
        return history

async def generate_reply(
    user_id: str,
    user_text: str,
    contact_name: str = "Client",
    send_message_callback: Callable[[str, str], Awaitable[None]] = None
) -> str:
    """
    Multilingual AI Consultant agent with tool calling and persistent database history.
    """
    try:
        # 1. Fetch / initialize user state
        user = await get_or_create_user(user_id, contact_name)

        # 2. Record incoming message to DB
        await save_chat_message(user_id, "user", user_text)

        # 3. Build system prompt with live business knowledge
        kb_context = knowledge_service.get_summary_context()
        display_name = user.whatsapp_name if user.whatsapp_name and user.whatsapp_name not in ["Client", "Unknown"] else "there"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            business_name=knowledge_service.data.get("business_name", "Apex Growth"),
            tagline=knowledge_service.data.get("tagline", "AI & Web Solutions"),
            preferred_language=user.preferred_language or "english",
            contact_name=display_name,
            phone_number=user_id,
            knowledge_context=kb_context
        )

        # 4. Fetch history from DB
        history = await get_db_history(user_id, limit=settings.MEMORY_HISTORY_LIMIT)

        messages = [{"role": "system", "content": system_prompt}] + history

        # 5. First OpenAI API Call
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            temperature=0.7,
            tools=AGENT_TOOLS,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # 6. Process Tool Calls if any
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                tool_result = await execute_tool_call(func_name, func_args, user_id)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": str(tool_result)
                })

            # Second call to get final conversational response
            second_response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=messages,
                temperature=0.7
            )
            final_reply = second_response.choices[0].message.content
        else:
            final_reply = response_message.content

        # 7. Record AI reply in DB
        if final_reply:
            await save_chat_message(user_id, "ai", final_reply)

        return final_reply

    except Exception as e:
        logger.error(f"Error in generate_reply: {e}", exc_info=True)
        fallback = "Thank you for reaching out! A senior consultant has been notified and will assist you shortly."
        await save_chat_message(user_id, "ai", fallback)
        return fallback
