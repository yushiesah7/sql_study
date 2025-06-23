"""
依存性注入の設定
"""
from typing import AsyncGenerator
from app.core.db import db
from app.core.db import Database
from app.core.llm_client import LocalAIClient
from app.services.llm_service import LLMService
from app.services.db_service import DatabaseService


async def get_db() -> Database:
    """
    Asynchronously provides the shared database instance for dependency injection.
    
    Returns:
        Database: The global database instance.
    """
    return db


async def get_llm() -> LLMService:
    """
    Asynchronously provides an instance of the LLMService initialized with a new LocalAIClient.
    
    Returns:
        LLMService: An instance of the language model service.
    """
    llm_client = LocalAIClient()
    return LLMService(llm_client)


async def get_db_service() -> DatabaseService:
    """
    Asynchronously provides a DatabaseService instance initialized with the global database.
    """
    return DatabaseService(db)