from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone
from app.infra.evermemos_client import EverMemOSClient
from app.config import settings
import logging

class MemoryService:
    def __init__(self):
        self.client = EverMemOSClient()

    def store_user_message(self, user_id: str, content: str) -> Dict[str, Any]:
        """
        Stores a literal user message into EverMemOS as episodic memory.
        """
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        create_time = datetime.now(timezone.utc).isoformat()
        
        return self.client.store_user_message(
            message_id=message_id,
            create_time=create_time,
            sender=user_id,
            content=content,
            user_id=user_id,
            group_id=f"memoryvest_{user_id}"
        )
        
    def store_system_event(self, user_id: str, content: str) -> Dict[str, Any]:
        """
        Stores a system-generated event (like report sent).
        """
        message_id = f"evt_{uuid.uuid4().hex[:8]}"
        create_time = datetime.now(timezone.utc).isoformat()
        
        return self.client.store_user_message(
            message_id=message_id,
            create_time=create_time,
            sender="memoryvest_system",
            content=content,
            user_id=user_id,
            group_id=f"memoryvest_{user_id}"
        )

    def _extract_texts_from_result(self, res: Dict[str, Any]) -> List[str]:
        """
        Parses memory search results from both cloud and local EverMemOS response formats.

        Cloud API returns memories as a flat list of objects:
          {"result": {"memories": [{"summary": "...", "memory_type": "episodic_memory", ...}]}}

        Local API returns memories as a list of group dicts:
          {"result": {"memories": [{"group_id": [...memories...]}]}}
        """
        extracted_texts = []
        result = res.get("result", {})
        memories_raw = result.get("memories", [])
        pending_messages = result.get("pending_messages", [])

        for item in memories_raw:
            if not isinstance(item, dict):
                continue
            # Cloud format: flat object with 'summary' or 'content' at top level
            if "summary" in item or "content" in item or "memory_type" in item:
                text = item.get("summary") or item.get("content") or item.get("episode") or str(item)
                extracted_texts.append(text)
            else:
                # Local format: keys are group_ids mapping to lists of memory items
                for group_id, memory_items in item.items():
                    if not isinstance(memory_items, list):
                        continue
                    for mem in memory_items:
                        text = mem.get("episode") or mem.get("summary") or mem.get("content") or str(mem)
                        extracted_texts.append(text)

        # Fresh pending messages (present in both formats)
        for pm in pending_messages:
            text = pm.get("content") or str(pm)
            extracted_texts.append(text)

        return extracted_texts

    def search_episodic_context(self, user_id: str, query: str = "What are the user's recent concerns and holdings?") -> str:
        """
        Searches episodic memory for context.
        """
        try:
            res = self.client.search_memories(
                query=query,
                user_id=user_id,
                memory_types=["episodic_memory"],
                retrieve_method="hybrid",
                top_k=5
            )
            extracted_texts = self._extract_texts_from_result(res)
            if not extracted_texts:
                return "No recent conversational context."
            return "\n".join(extracted_texts)
        except Exception as e:
            logging.error(f"Error retrieving episodic context from EverMemOS: {e}")
            return f"Error retrieving context: {e}"

    def search_foresight_context(self, user_id: str) -> str:
        """
        Searches foresight memory. Skipped gracefully on cloud API (not supported).
        """
        # Cloud EverMemOS does not support foresight search — skip to avoid 422
        if settings.evermemos_api_key:
            logging.debug("Skipping foresight search: not supported by cloud EverMemOS API.")
            return "No future foresight intents."

        try:
            res = self.client.search_memories(
                query="What future actions or alerts does the user want?",
                user_id=user_id,
                memory_types=["foresight"],
                retrieve_method="hybrid",
                top_k=5
            )
            extracted_texts = self._extract_texts_from_result(res)
            if not extracted_texts:
                return "No future foresight intents."
            return "\n".join(extracted_texts)
        except Exception as e:
            logging.error(f"Error retrieving foresight context from EverMemOS: {e}")
            return f"Error retrieving foresight: {e}"
