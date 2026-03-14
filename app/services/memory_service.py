from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone
from app.infra.evermemos_client import EverMemOSClient
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
            memories_raw = res.get("result", {}).get("memories", [])
            pending_messages = res.get("result", {}).get("pending_messages", [])
            
            extracted_texts = []
            
            # Extract from compiled memories
            for mem_group in memories_raw:
                for group_id, memory_items in mem_group.items():
                    for mem in memory_items:
                        text = mem.get("episode") or mem.get("summary") or str(mem)
                        extracted_texts.append(text)
                        
            # Extract from fresh pending messages
            for pm in pending_messages:
                text = pm.get("content") or str(pm)
                extracted_texts.append(text)
                        
            if not extracted_texts:
                return "No recent conversational context."
            return "\n".join(extracted_texts)
        except Exception as e:
            logging.error(f"Error retrieving episodic context from EverMemOS: {e}")
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
            memories_raw = res.get("result", {}).get("memories", [])
            pending_messages = res.get("result", {}).get("pending_messages", [])
            
            extracted_texts = []
            
            # Extract from compiled memories
            for mem_group in memories_raw:
                for group_id, memory_items in mem_group.items():
                    for mem in memory_items:
                        text = mem.get("episode") or mem.get("summary") or str(mem)
                        extracted_texts.append(text)
                        
            # Extract from fresh pending messages
            for pm in pending_messages:
                text = pm.get("content") or str(pm)
                extracted_texts.append(text)
                        
            if not extracted_texts:
                return "No future foresight intents."
            return "\n".join(extracted_texts)
        except Exception as e:
            logging.error(f"Error retrieving foresight context from EverMemOS: {e}")
            return f"Error retrieving foresight: {e}"
