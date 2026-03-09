import httpx
from typing import Dict, Any, List
from app.config import settings

class EverMemOSClient:
    def __init__(self):
        self.base_url = settings.evermemos_api_url
    
    def store_user_message(self, message_id: str, create_time: str, sender: str, content: str, user_id: str, group_id: str = None) -> Dict[str, Any]:
        payload = {
            "message_id": message_id,
            "create_time": create_time,
            "sender": sender,
            "content": content,
            "user_id": user_id
        }
        if group_id:
            payload["group_id"] = group_id
            
        with httpx.Client() as client:
            response = client.post(f"{self.base_url}/memories", json=payload)
            response.raise_for_status()
            return response.json()

    def search_memories(self, query: str, user_id: str, memory_types: List[str] = None, retrieve_method: str = "hybrid", top_k: int = 10) -> Dict[str, Any]:
        if memory_types is None:
            memory_types = ["episodic_memory", "foresight", "event_log"]
            
        payload = {
            "query": query,
            "user_id": user_id,
            "memory_types": memory_types,
            "retrieve_method": retrieve_method,
            "top_k": top_k
        }
        
        with httpx.Client() as client:
            response = client.get(f"{self.base_url}/memories/search", json=payload)
            response.raise_for_status()
            return response.json()
