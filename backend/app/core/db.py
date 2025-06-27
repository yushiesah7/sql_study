"""
PostgreSQL接続管理
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class Database:
    """データベース接続管理クラス"""

    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """データベース接続プールを作成"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                max_inactive_connection_lifetime=settings.DB_POOL_TIMEOUT,
                timeout=10,
                command_timeout=settings.SQL_EXECUTION_TIMEOUT,
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise DatabaseError(
                message="データベース接続エラー",
                error_code="DB_CONNECTION_ERROR",
                detail=str(e),
            ) from None

    async def disconnect(self) -> None:
        """データベース接続プールを閉じる"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """接続をコンテキストマネージャーとして取得"""
        if not self.pool:
            raise DatabaseError(
                message="データベースプールが初期化されていません",
                error_code="DB_NOT_INITIALIZED_ERROR",
                detail="Database.connect()を先に実行してください",
            )

        async with self.pool.acquire() as connection:
            yield connection

    async def execute_select(
        self, query: str, *args: Any, query_timeout: float | None = None
    ) -> list[dict[str, Any]]:
        """SELECT文を実行"""
        try:
            async with self.acquire() as conn:
                # タイムアウト設定
                if query_timeout:
                    rows = await asyncio.wait_for(
                        conn.fetch(query, *args), timeout=query_timeout
                    )
                else:
                    rows = await conn.fetch(query, *args)

                # 結果を辞書形式に変換
                return [dict(row) for row in rows]

        except TimeoutError:
            raise DatabaseError(
                message="SQL実行タイムアウト",
                error_code="DB_TIMEOUT_ERROR",
                detail=f"制限時間: {query_timeout}秒",
            ) from None
        except asyncpg.PostgresSyntaxError as e:
            raise DatabaseError(
                message="SQL構文エラー", error_code="DB_SYNTAX_ERROR", detail=str(e)
            ) from None
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise DatabaseError(
                message="SQL実行エラー", error_code="DB_EXECUTION_ERROR", detail=str(e)
            ) from None

    async def execute(self, query: str, *args: Any) -> Any:
        """任意のSQLを実行(CREATE/DROP等)"""
        try:
            async with self.acquire() as conn:
                result = await conn.execute(query, *args)
                return result
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            raise DatabaseError(
                message="SQL実行エラー", error_code="DB_EXECUTION_ERROR", detail=str(e)
            ) from None

    async def get_table_schemas(self) -> list[dict[str, Any]]:
        """現在のテーブルスキーマ情報を取得"""
        query = """
        SELECT
            t.table_name,
            t.table_type,
            obj_description(pgc.oid, 'pg_class') as table_comment
        FROM information_schema.tables t
        JOIN pg_class pgc ON pgc.relname = t.table_name
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name;
        """

        tables = await self.execute_select(query)

        # 各テーブルのカラム情報を取得
        for table in tables:
            column_query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = $1
            ORDER BY ordinal_position;
            """

            columns = await self.execute_select(column_query, table["table_name"])
            table["columns"] = columns

        return tables

    async def drop_all_tables(self) -> None:
        """全てのテーブルを削除(開発用)"""
        try:
            async with self.acquire() as conn:
                # 外部キー制約を一時的に無効化
                await conn.execute("SET session_replication_role = 'replica';")

                # 全テーブル削除
                tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
                )

                for table in tables:
                    await conn.execute(
                        f"DROP TABLE IF EXISTS {table['tablename']} CASCADE;"
                    )

                # 外部キー制約を再有効化
                await conn.execute("SET session_replication_role = 'origin';")

                logger.info(f"Dropped {len(tables)} tables")

        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise DatabaseError(
                message="テーブル削除エラー",
                error_code="DB_DROP_TABLE_ERROR",
                detail=str(e),
            ) from None

    async def check_health(self) -> bool:
        """データベース接続の健全性をチェック"""
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# グローバルデータベースインスタンス
db = Database()
