from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone
from app.infra.evermemos_client import EverMemOSClient

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
            # Extrapolate context string
            memories = res.get("result", {}).get("memories", [])
            if not memories:
                return "No recent conversational context."
            return "\n".join(memories)
        except Exception as e:
            return f"Error retrieving context: {e}"

    def search_foresight_context(self, user_id: str) -> str:
        """
        Searches foresight memory.
        """
        try:
            res = self.client.search_memories(
                query="What future actions or alerts does the user want?",
                user_id=user_id,
                memory_types=["foresight"],
                retrieve_method="hybrid",
                top_k=5
            )
            memories = res.get("result", {}).get("memories", [])
            if not memories:
                return "No future foresight intents."
            return "\n".join(memories)
        except Exception as e:
            return f"Error retrieving foresight: {e}"
