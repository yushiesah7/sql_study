"""
データベース操作サービス
"""

import json
import logging
from datetime import date, datetime
from typing import Any

from app.core.db import Database
from app.core.error_codes import DB_EXECUTION_ERROR, DB_SCHEMA_ERROR
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class DateJSONEncoder(json.JSONEncoder):
    """日付型データをJSON変換可能にするカスタムエンコーダー"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class DatabaseService:
    """データベース操作サービスクラス"""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def initialize_system_schema(self) -> None:
        """
        システム用スキーマとテーブルを初期化

        Raises:
            DatabaseError: 初期化失敗時
        """
        try:
            # app_systemスキーマ作成
            await self.db.execute("""
                CREATE SCHEMA IF NOT EXISTS app_system
            """)

            # problemsテーブル作成
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS app_system.problems (
                    id SERIAL PRIMARY KEY,
                    theme VARCHAR(255) NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    correct_sql TEXT NOT NULL,
                    expected_result JSONB NOT NULL,
                    hint TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    table_schemas JSONB NOT NULL
                )
            """)

            logger.info("System schema initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize system schema: {e}")
            raise DatabaseError(
                message="システムスキーマの初期化に失敗しました",
                error_code=DB_SCHEMA_ERROR,
                detail=str(e),
            ) from None

    async def drop_all_user_tables(self) -> None:
        """
        publicスキーマのユーザーテーブルを全削除

        Raises:
            DatabaseError: 削除失敗時
        """
        try:
            # publicスキーマのテーブル一覧を取得
            tables = await self.db.execute_select("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)

            if tables:
                table_names = [table["table_name"] for table in tables]

                # CASCADEで全削除
                for table_name in table_names:
                    await self.db.execute(
                        f'DROP TABLE IF EXISTS "{table_name}" CASCADE'
                    )

                logger.info(f"Dropped {len(table_names)} user tables: {table_names}")

        except Exception as e:
            logger.error(f"Failed to drop user tables: {e}")
            raise DatabaseError(
                message="ユーザーテーブルの削除に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e),
            ) from None

    async def execute_sql_statements(self, sql_statements: list[str]) -> None:
        """
        SQL文を順次実行

        Args:
            sql_statements: 実行するSQL文のリスト

        Raises:
            DatabaseError: 実行失敗時
        """
        try:
            for sql in sql_statements:
                if sql.strip():
                    await self.db.execute(sql)

            logger.info(f"Executed {len(sql_statements)} SQL statements")

        except Exception as e:
            logger.error(f"Failed to execute SQL statements: {e}")
            raise DatabaseError(
                message="SQL文の実行に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e),
            ) from None

    async def get_table_schemas(self) -> list[dict[str, Any]]:
        """
        publicスキーマのテーブル構造を取得

        Returns:
            テーブル構造のリスト

        Raises:
            DatabaseError: 取得失敗時
        """
        try:
            # テーブル一覧を取得
            tables = await self.db.execute_select("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)

            schemas = []
            for table in tables:
                table_name = table["table_name"]

                # カラム情報を取得
                columns = await self.db.execute_select(
                    """
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = $1
                    ORDER BY ordinal_position
                """,
                    table_name,
                )

                # 主キー情報を取得
                primary_keys = await self.db.execute_select(
                    """
                    SELECT column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = $1
                    AND tc.constraint_type = 'PRIMARY KEY'
                """,
                    table_name,
                )

                pk_columns = {pk["column_name"] for pk in primary_keys}

                # 外部キー情報を取得
                foreign_keys = await self.db.execute_select(
                    """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.constraint_column_usage ccu
                        ON kcu.constraint_name = ccu.constraint_name
                    JOIN information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = $1
                    AND tc.constraint_type = 'FOREIGN KEY'
                """,
                    table_name,
                )

                fk_dict = {
                    fk["column_name"]: {
                        "table": fk["foreign_table_name"],
                        "column": fk["foreign_column_name"],
                    }
                    for fk in foreign_keys
                }

                # カラム情報を整形
                formatted_columns = []
                for col in columns:
                    column_info = {
                        "column_name": col["column_name"],
                        "data_type": col["data_type"].upper(),
                        "is_nullable": col["is_nullable"] == "YES",
                        "is_primary_key": col["column_name"] in pk_columns,
                    }

                    if col["column_name"] in fk_dict:
                        column_info["foreign_key"] = fk_dict[col["column_name"]]

                    formatted_columns.append(column_info)

                schemas.append({"table_name": table_name, "columns": formatted_columns})

            return schemas

        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            raise DatabaseError(
                message="テーブル構造の取得に失敗しました",
                error_code=DB_SCHEMA_ERROR,
                detail=str(e),
            ) from None

    async def execute_select_query(
        self, sql: str, query_timeout: int = 5
    ) -> list[dict[str, Any]]:
        """
        SELECT文を実行して結果を取得

        Args:
            sql: 実行するSELECT文
            query_timeout: タイムアウト秒数

        Returns:
            クエリ結果

        Raises:
            DatabaseError: 実行失敗時
        """
        try:
            # タイムアウト付きで実行
            result = await self.db.execute_select(sql, query_timeout=query_timeout)

            # すでに辞書形式なのでそのまま返す
            return result

        except Exception as e:
            logger.error(f"Failed to execute SELECT query: {e}")
            raise DatabaseError(
                message="SELECT文の実行に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e),
            ) from None

    async def save_problem(
        self,
        theme: str,
        difficulty: str,
        correct_sql: str,
        expected_result: list[dict[str, Any]],
        table_schemas: list[dict[str, Any]],
        hint: str | None = None,
    ) -> int:
        """
        問題をデータベースに保存

        Args:
            theme: テーマ
            difficulty: 難易度
            correct_sql: 正解SQL
            expected_result: 期待結果
            table_schemas: テーブル構造
            hint: ヒント

        Returns:
            問題ID

        Raises:
            DatabaseError: 保存失敗時
        """
        try:
            results = await self.db.execute_select(
                """
                INSERT INTO app_system.problems
                (theme, difficulty, correct_sql, expected_result, table_schemas, hint)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """,
                theme,
                difficulty,
                correct_sql,
                json.dumps(expected_result, ensure_ascii=False, cls=DateJSONEncoder),
                json.dumps(table_schemas, ensure_ascii=False, cls=DateJSONEncoder),
                hint,
            )

            if not results:
                raise DatabaseError(
                    message="問題のIDが返されませんでした",
                    error_code=DB_EXECUTION_ERROR,
                    detail="INSERT文のRETURNINGが失敗しました",
                )
            problem_id: int = results[0]["id"]
            logger.info(f"Saved problem with ID: {problem_id}")
            return problem_id

        except Exception as e:
            logger.error(f"Failed to save problem: {e}")
            raise DatabaseError(
                message="問題の保存に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e),
            ) from None

    async def get_problem(self, problem_id: int) -> dict[str, Any] | None:
        """
        問題を取得

        Args:
            problem_id: 問題ID

        Returns:
            問題情報(存在しない場合はNone)

        Raises:
            DatabaseError: 取得失敗時
        """
        try:
            results = await self.db.execute_select(
                """
                SELECT id, theme, difficulty, correct_sql, expected_result,
                       table_schemas, hint, created_at
                FROM app_system.problems
                WHERE id = $1
            """,
                problem_id,
            )

            if not results:
                return None

            problem = results[0]
            # Parse JSON fields back to Python objects
            if isinstance(problem["expected_result"], str):
                problem["expected_result"] = json.loads(problem["expected_result"])
            if isinstance(problem["table_schemas"], str):
                problem["table_schemas"] = json.loads(problem["table_schemas"])

            return problem

        except Exception as e:
            logger.error(f"Failed to get problem {problem_id}: {e}")
            raise DatabaseError(
                message="問題の取得に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e),
            ) from None
