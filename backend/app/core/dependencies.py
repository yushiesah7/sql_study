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
    依存性注入用の共有データベースインスタンスを非同期で提供する。
    
    戻り値:
        Database: グローバルデータベースインスタンス。
    """
    return db


async def get_llm() -> LLMService:
    """
    新しいLocalAIClientで初期化されたLLMServiceインスタンスを非同期で提供する。
    
    戻り値:
        LLMService: 言語モデルサービスのインスタンス。
    """
    llm_client = LocalAIClient()
    return LLMService(llm_client)


async def get_db_service() -> DatabaseService:
    """
    グローバルデータベースで初期化されたDatabaseServiceインスタンスを非同期で提供する。
    """
    return DatabaseService(db)