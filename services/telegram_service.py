# services/telegram_service.py

import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)

class TelegramService:
    """
    Asynchronous client for interacting with the Telegram Bot API.
    """
    def __init__(self):
        self.settings = get_settings()

    @property
    def base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(self, to: str, text: str):
        """
        Sends a message to a Telegram chat/user.
        Parameter 'to' is the chat_id (e.g. '12345678' or 'tg_12345678').
        """
        chat_id = to.replace("tg_", "") if to.startswith("tg_") else to
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.error(f"Telegram API Error ({response.status_code}): {response.text}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {chat_id}: {e}", exc_info=True)
            raise

telegram_service = TelegramService()

async def send_telegram_message(to: str, text: str):
    """
    Helper function matching the signature expected by agent services.
    """
    return await telegram_service.send_message(to=to, text=text)
