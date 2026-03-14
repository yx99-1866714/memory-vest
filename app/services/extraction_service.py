import json
from openai import OpenAI
from pathlib import Path
from typing import List, Dict, Any
from app.config import settings
from app.models.profile import UserProfile
from app.models.position import Position
import logging

class ExtractionService:
    def __init__(self):
        # Allow fallback initialization for tests and environments without keys
        if settings.openrouter_api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "MemoryVest",
                }
            )
        else:
            self.client = None
            
        self.model = settings.llm_model

        prompt_dir = Path(__file__).parent.parent / "prompts"
        with open(prompt_dir / "extract_profile.txt", "r", encoding="utf-8") as f:
            self.profile_prompt_template = f.read()
            
        with open(prompt_dir / "extract_csv.txt", "r", encoding="utf-8") as f:
            self.csv_prompt_template = f.read()

    def generate_welcome_message(self, current_profile: UserProfile, current_positions: list, memory_context: str) -> str:
        """
        Generates a personalized welcome message summarizing the last conversation.
        """
        if not self.client:
            return "Welcome back!"
            
        prompt = f"""You are MemoryVest, a personalized investing companion.
The user is returning to chat. Generate a short, friendly greeting.
If there are memories from previous conversations or current holdings, briefly summarize them and mention any action items (like watching a stock).
IMPORTANT: The Positions provided below are the absolute ground truth for the user's current holdings. Do not invent or refer to positions not listed below.
IMPORTANT: The Profile provided below is the absolute single source of truth for the user's preferences. Do not invent or refer to traits that contradict this profile.
Keep it under 3-4 sentences. Include no markdown. Provide just the text response.

Profile (Source of Truth for User Preferences): {json.dumps(current_profile.model_dump(mode='json')) if current_profile else 'None'}
Positions (Source of Truth for Current Holdings): {json.dumps([p.model_dump(mode='json') for p in current_positions]) if current_positions else 'None'}
Recent Memories:
{memory_context}
"""
        try:
            logging.debug(f"Welcome LLM prompt: \n{prompt}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise, beginner-friendly investing assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error calling welcome LLM: {e}")
            return "Welcome back to MemoryVest!"

    def parse_user_input(self, user_input: str, current_profile: UserProfile = None, current_positions: list = None, current_cash: float = 0.0) -> Dict[str, Any]:
        """
        Parses user input to extract structured properties.
        """
        if not self.client:
            logging.warning("OPENROUTER_API_KEY is not set. Using fallback mock extraction.")
            # For MVP demo or missing API key, returning a very simple mock
            return {
                "intent": "casual_chat",
                "profile_updates": {},
                "positions_to_add": [],
                "positions_to_update": [],
                "cash_update": None,
                "watch_intents": [],
                "memory_note": None,
                "response_message": "I'm offline right now, but I'm here if you need to manually configure your account!"
            }

        profile_json = json.dumps(current_profile.model_dump(mode='json')) if current_profile else "{}"
        positions_json = json.dumps([p.model_dump(mode='json') for p in current_positions]) if current_positions else "[]"

        prompt = self.profile_prompt_template.format(
            current_profile=profile_json,
            current_positions=positions_json,
            current_cash=current_cash,
            user_input=user_input
        )

        try:
            logging.debug(f"Extraction LLM model used: {self.model}")
            logging.debug(f"Extraction LLM prompt: \n{prompt}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful JSON extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            raw_content = response.choices[0].message.content.strip()
            # Strip markdown if present
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
                
            logging.debug(f"Extraction LLM Raw Response: \n{raw_content}")
            return json.loads(raw_content)
        except Exception as e:
            logging.error(f"Extraction error: {e}")
            return {
                "intent": "error",
                "profile_updates": {},
                "positions_to_add": [],
                "positions_to_update": [],
                "cash_update": None,
                "watch_intents": [],
                "memory_note": None,
                "response_message": "I'm sorry, I'm having a little trouble connecting to my AI brain right now."
            }
            
    def parse_csv_portfolio(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parses an arbitrary CSV string via LLM and returns a list of valid positions."""
        if not self.client:
            logging.warning("API key not set. Skipping CSV Extraction.")
            return []
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.csv_prompt_template},
                    {"role": "user", "content": csv_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1 # Keep it deterministic for parsing
            )
            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)
            
            return parsed_json.get("positions", [])
        except Exception as e:
            logging.error(f"CSV Extraction error: {e}")
            return []
