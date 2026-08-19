# services/agent_tools.py

import logging
from sqlalchemy import select, update
from core.database import AsyncSessionLocal
from models.db_models import User, Lead, ServiceBooking
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

# OpenAI Tool Specifications
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_qualified_lead",
            "description": "Save qualified lead information to the database when the user expresses interest in a service, shares their contact details, budget, or business problem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Client's name if provided."},
                    "email": {"type": "string", "description": "Client's email address if provided."},
                    "company_or_niche": {"type": "string", "description": "Company name or industry/niche."},
                    "service_interested": {"type": "string", "description": "The specific service package they need."},
                    "estimated_budget": {"type": "string", "description": "Their budget range or timeline."},
                    "intent_score": {
                        "type": "string", 
                        "enum": ["HOT", "WARM", "COLD"],
                        "description": "HOT = Ready to buy / high intent / urgent. WARM = Considering options or asking price. COLD = Casual query."
                    },
                    "qualification_notes": {"type": "string", "description": "Short summary of client's requirements and key conversation points."}
                },
                "required": ["service_interested", "intent_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_service_consultation",
            "description": "Schedule a strategy session or service consultation for the client in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of service package or Consultation."},
                    "preferred_date_time": {"type": "string", "description": "Client's preferred day, date, or time (e.g. 'Tomorrow 2 PM' or 'Next Monday morning')."},
                    "project_description": {"type": "string", "description": "Brief description of what will be discussed during the session."}
                },
                "required": ["service_name", "preferred_date_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_preferred_language",
            "description": "Update the user's preferred spoken language in their profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["english", "yoruba", "hausa", "igbo", "pidgin"],
                        "description": "The language the user wants to communicate in."
                    }
                },
                "required": ["language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Query specific FAQs, guarantees, pricing breakdown, or deliverables from the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search topic or question."}
                },
                "required": ["query"]
            }
        }
    }
]

async def execute_tool_call(tool_name: str, tool_args: dict, user_phone: str) -> str:
    """
    Executes a tool call asynchronously against the database.
    """
    logger.info(f"Executing tool '{tool_name}' for user {user_phone} with args: {tool_args}")
    
    async with AsyncSessionLocal() as session:
        try:
            if tool_name == "save_qualified_lead":
                lead = Lead(
                    user_phone=user_phone,
                    client_name=tool_args.get("client_name"),
                    email=tool_args.get("email"),
                    company_or_niche=tool_args.get("company_or_niche"),
                    service_interested=tool_args.get("service_interested"),
                    estimated_budget=tool_args.get("estimated_budget"),
                    intent_score=tool_args.get("intent_score", "WARM"),
                    qualification_notes=tool_args.get("qualification_notes")
                )
                session.add(lead)

                # Also update user's lead status
                await session.execute(
                    update(User)
                    .where(User.phone_number == user_phone)
                    .values(lead_status=tool_args.get("intent_score", "WARM").lower())
                )
                await session.commit()
                return f"Lead successfully registered for {tool_args.get('service_interested')} with status {tool_args.get('intent_score')}."

            elif tool_name == "book_service_consultation":
                booking = ServiceBooking(
                    user_phone=user_phone,
                    service_name=tool_args.get("service_name"),
                    preferred_date_time=tool_args.get("preferred_date_time"),
                    project_description=tool_args.get("project_description"),
                    booking_status="pending"
                )
                session.add(booking)
                await session.execute(
                    update(User)
                    .where(User.phone_number == user_phone)
                    .values(lead_status="booked")
                )
                await session.commit()
                return f"Consultation session booked for {tool_args.get('preferred_date_time')}. Our senior team will reach out to confirm."

            elif tool_name == "set_preferred_language":
                lang = tool_args.get("language", "english").lower()
                await session.execute(
                    update(User)
                    .where(User.phone_number == user_phone)
                    .values(preferred_language=lang)
                )
                await session.commit()
                return f"Language preference set to {lang}."

            elif tool_name == "search_knowledge_base":
                return knowledge_service.query_faqs(tool_args.get("query", ""))

            return "Tool executed successfully."

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return f"Error executing tool: {str(e)}"
