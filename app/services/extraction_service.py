import json
from openai import OpenAI
from pathlib import Path
from typing import Dict, Any
from app.config import settings
from app.models.profile import UserProfile
from app.models.position import Position
import logging

class ExtractionService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.llm_model
        if self.api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        else:
            self.client = None
            
        prompt_path = Path(__file__).parent.parent / "prompts" / "extract_profile.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

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
                "memory_note": None
            }

        profile_json = json.dumps(current_profile.model_dump(mode='json')) if current_profile else "{}"
        positions_json = json.dumps([p.model_dump(mode='json') for p in current_positions]) if current_positions else "[]"

        prompt = self.prompt_template.format(
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
            logging.error(f"Error calling extraction LLM: {e}")
            return {
                "intent": "error",
                "profile_updates": {},
                "positions_to_add": [],
                "positions_to_update": [],
                "cash_update": None,
                "watch_intents": [],
                "memory_note": None
            }
