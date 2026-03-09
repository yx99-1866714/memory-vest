from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    evermemos_api_url: str = "http://localhost:1995/api/v1"
    db_path: str = "memoryvest.db"
    openrouter_api_key: Optional[str] = None
    llm_model: str = "openai/gpt-5.4" # Or "x-ai/grok-4"
    
    # Optional parameters for external APIs
    market_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    
    # Delivery Service Setup
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_pass: str = ""
    sender_email: str = "reports@memoryvest.local"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
