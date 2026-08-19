# services/knowledge_service.py

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "business_profile.json"

class KnowledgeService:
    def __init__(self):
        self.data = self._load_data()

    def _load_data(self) -> dict:
        try:
            if KB_PATH.exists():
                with open(KB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading knowledge base from {KB_PATH}: {e}")
        return {}

    def get_summary_context(self) -> str:
        """
        Returns a concise context string formatted for inclusion in the AI system prompt.
        """
        if not self.data:
            return ""

        services_str = ""
        for s in self.data.get("services", []):
            services_str += f"- **{s['name']}** (Price: {s['price_range']}, Timeline: {s['timeline']})\n"
            services_str += f"  Deliverables: {', '.join(s['deliverables'])}\n"
            services_str += f"  Best for: {s['best_for']}\n\n"

        faq_str = ""
        for f in self.data.get("faq", []):
            faq_str += f"Q: {f['question']}\nA: {f['answer']}\n\n"

        return f"""
BUSINESS CONTEXT:
- Name: {self.data.get('business_name')}
- Tagline: {self.data.get('tagline')}
- Location: {self.data.get('location')}

SERVICES & PRICING:
{services_str}

COMMON FAQS & KNOWLEDGE:
{faq_str}
"""

    def query_faqs(self, query: str) -> str:
        """
        Retrieves matching FAQs for a specific query.
        """
        q_lower = query.lower()
        results = []
        for f in self.data.get("faq", []):
            if any(word in f["question"].lower() or word in f["answer"].lower() for word in q_lower.split()):
                results.append(f"Q: {f['question']}\nA: {f['answer']}")
        
        if results:
            return "\n\n".join(results[:3])
        return "No specific FAQ entry found, consult general business knowledge."

knowledge_service = KnowledgeService()
