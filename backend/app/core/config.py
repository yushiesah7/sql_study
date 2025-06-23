"""
アプリケーション設定
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # Application
    APP_NAME: str = Field(default="SQL Learning App")
    DEBUG: bool = Field(default=False)
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:changethis@db:5432/mydb")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: float = Field(default=30.0)
    
    # LocalAI
    LLM_API_URL: str = Field(default="http://llm:8080/v1")
    LLM_MODEL_NAME: str = Field(default="gpt-3.5-turbo")
    LLM_TIMEOUT: float = Field(default=30.0)
    LLM_MAX_RETRIES: int = Field(default=3)
    LLM_TEMPERATURE: float = Field(default=0.7)
    LLM_MAX_TOKENS: int = Field(default=2000)
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://frontend:3000"])
    
    # Security
    SQL_EXECUTION_TIMEOUT: float = Field(default=5.0)
    MAX_RESULT_ROWS: int = Field(default=100)
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """
        Parse the CORS allowed origins value into a list of strings.
        
        If the input is a comma-separated string, splits it into a list and trims whitespace from each origin. If already a list, returns it unchanged.
        
        Parameters:
            v: The value to parse, either a string or a list.
        
        Returns:
            A list of allowed origin strings.
        """
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# グローバル設定インスタンス
settings = Settings()