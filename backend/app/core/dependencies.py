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
    """データベースインスタンスを取得"""
    return db


async def get_llm() -> LLMService:
    """LLMサービスを取得"""
    llm_client = LocalAIClient()
    return LLMService(llm_client)


async def get_db_service() -> DatabaseService:
    """データベースサービスを取得"""
    return DatabaseService(db)