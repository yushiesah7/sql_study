"""
依存性注入の設定
"""
from typing import AsyncGenerator
from app.core.db import db
from app.core.db import Database


async def get_db() -> Database:
    """データベースインスタンスを取得"""
    return db


# TODO: LLMクライアントの依存性注入を実装
async def get_llm():
    """LLMクライアントを取得"""
    # Phase 3で実装予定
    pass