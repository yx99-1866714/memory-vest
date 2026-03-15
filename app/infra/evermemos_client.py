import requests
from typing import Dict, Any, List
from app.config import settings
import logging

class EverMemOSClient:
    def __init__(self):
        self.base_url = settings.evermemos_api_url

        # Build a shared session so auth headers are set once for all requests
        self.session = requests.Session()
        self.session.trust_env = False
        if settings.evermemos_api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {settings.evermemos_api_key}"
            })
            logging.debug("EverMemOS client initialized with API key auth.")
        else:
            logging.debug("EverMemOS client initialized without auth (local mode).")

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

        logging.debug(f"EverMemOS POST /memories Payload: {payload}")
        response = self.session.post(f"{self.base_url}/memories", json=payload, timeout=30.0)
        logging.debug(f"EverMemOS POST /memories Response: {response.status_code}")
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

        logging.debug(f"EverMemOS GET /memories/search Payload: {payload}")
        response = self.session.get(f"{self.base_url}/memories/search", json=payload, timeout=30.0)
        logging.debug(f"EverMemOS GET /memories/search Response ({response.status_code}): {response.text}")
        response.raise_for_status()
        return response.json()

    def delete_all_user_memories(self, user_id: str) -> Dict[str, Any]:
        payload = {
            "event_id": "__all__",
            "group_id": "__all__",
            "user_id": user_id
        }

        logging.debug(f"EverMemOS DELETE /memories Payload: {payload}")
        response = self.session.delete(f"{self.base_url}/memories", json=payload, timeout=30.0)
        logging.debug(f"EverMemOS DELETE /memories Response ({response.status_code}): {response.text}")
        response.raise_for_status()
        return response.json()
