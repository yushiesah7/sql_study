"""
テーブル構造取得API
現在作成されているテーブルの構造情報を取得
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from app.schemas import UniversalResponse
from app.core.dependencies import get_db_service
from app.services.db_service import DatabaseService
from app.core.exceptions import DatabaseError, NotFoundError
from app.core.error_codes import NO_TABLES, SCHEMA_FETCH_ERROR

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/table-schemas", response_model=UniversalResponse)
async def get_table_schemas(db_service: DatabaseService = Depends(get_db_service)) -> UniversalResponse:
    """
    現在のテーブル構造を取得

    Returns:
        テーブル構造情報

    Raises:
        HTTPException: 取得失敗時
    """
    try:
        logger.info("Getting table schemas")

        # 1. publicスキーマのテーブル構造を取得
        schemas = await db_service.get_table_schemas()

        if not schemas:
            raise NotFoundError(
                message="テーブルが作成されていません。先にテーブルを作成してください。",
                error_code=NO_TABLES,
            )

        # 2. テーブル数をカウント
        table_count = len(schemas)

        # 3. 現在のテーマ情報を取得
        # TODO: セッション管理から取得
        # 暫定的にテーブル名から推測
        theme = "不明"
        table_names = [schema["table_name"] for schema in schemas]

        # 簡単なテーマ推測ロジック
        if any(
            "employee" in name.lower() or "department" in name.lower()
            for name in table_names
        ):
            theme = "社員管理"
        elif any(
            "product" in name.lower()
            or "order" in name.lower()
            or "customer" in name.lower()
            for name in table_names
        ):
            theme = "ECサイト"
        elif any(
            "student" in name.lower()
            or "course" in name.lower()
            or "enrollment" in name.lower()
            for name in table_names
        ):
            theme = "学校管理"
        elif any(
            "book" in name.lower()
            or "author" in name.lower()
            or "library" in name.lower()
            for name in table_names
        ):
            theme = "図書館"

        logger.info(
            f"Successfully retrieved {table_count} table schemas for theme: {theme}"
        )

        return UniversalResponse(
            success=True,
            message=f"{table_count}個のテーブル構造を取得しました",
            data={
                "schemas": schemas,
                "theme": theme,
                "table_count": table_count,
                "table_names": table_names,
            },
        )

    except NotFoundError as e:
        logger.error(f"No tables found: {e}")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        )

    except DatabaseError as e:
        logger.error(f"Database error during schema fetch: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        )

    except Exception as e:
        logger.error(f"Unexpected error during schema fetch: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": SCHEMA_FETCH_ERROR,
                "message": "テーブル構造の取得に失敗しました",
                "detail": str(e),
            },
        )
