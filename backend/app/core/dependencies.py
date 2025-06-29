"""
依存性注入の設定
"""

from functools import lru_cache

from app.core.db import Database, db
from app.core.llm_client import LLMClient
from app.services.db_service import DatabaseService
from app.services.llm_service import LLMService


async def get_db() -> Database:
    """データベースインスタンスを取得"""
    return db


@lru_cache(maxsize=1)
def _get_llm_client() -> LLMClient:
    """LLMクライアントのシングルトンインスタンスを取得"""
    return LLMClient()


async def get_llm() -> LLMService:
    """LLMサービスを取得"""
    return LLMService(_get_llm_client())


async def get_db_service() -> DatabaseService:
    """データベースサービスを取得"""
    return DatabaseService(db)
