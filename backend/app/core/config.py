import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # AI Configuration
    # OpenAI API key (optional if using local models)
    openai_api_key: Optional[str] = None
    
    # AI Provider: 'openai' or 'lmstudio' or 'openai-compatible'
    ai_provider: str = "openai"
    
    # LM Studio Configuration
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "local-model"
    lm_studio_api_key: str = "not-needed"
    
    # OpenAI-compatible API settings
    openai_base_url: Optional[str] = None
    
    # Model name for openai-compatible providers
    ai_model: str = "gpt-3.5-turbo"
    
    # Model parameters
    ai_temperature: float = 0.1
    ai_max_tokens: int = 1000
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: Optional[str] = None
    
    # CORS
    backend_cors_origins: list = ["http://localhost:3000"]
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        # This tells Pydantic to convert environment variable names
        # For example: AI_PROVIDER -> ai_provider
        case_sensitive = False

settings = Settings()
print(f"AI Provider: {settings.ai_provider}")
print(f"LM Studio URL: {settings.lm_studio_base_url}")