"""
テーブル作成API
学習用のデータベーステーブルとサンプルデータを作成
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db_service, get_llm
from app.core.error_codes import TABLE_CREATION_ERROR
from app.core.exceptions import DatabaseError, LLMError
from app.schemas import UniversalRequest, UniversalResponse
from app.services.db_service import DatabaseService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create-tables", response_model=UniversalResponse)
async def create_tables(
    request: UniversalRequest,
    llm_service: LLMService = Depends(get_llm),
    db_service: DatabaseService = Depends(get_db_service),
) -> UniversalResponse:
    """
    学習用テーブルとサンプルデータを作成

    Args:
        request: リクエストデータ(prompt: 省略可、最大1000文字)

    Returns:
        作成結果とテーマ情報

    Raises:
        HTTPException: 作成失敗時
    """
    try:
        # プロンプトの取得(最大1000文字)
        prompt = request.prompt
        if prompt and len(prompt) > 1000:
            raise HTTPException(
                status_code=400, detail="プロンプトは1000文字以内で入力してください"
            )

        logger.info(
            f"Creating tables with prompt: {prompt[:50] if prompt else 'None'}..."
        )

        # 1. 既存のpublicスキーマのテーブルを全削除
        await db_service.drop_all_user_tables()

        # 2. システムスキーマの初期化
        await db_service.initialize_system_schema()

        # 3. LLMにテーブル構造を生成させる
        table_info = await llm_service.generate_tables(prompt)

        # 4. CREATE TABLE文とサンプルデータを実行
        sql_statements = table_info["sql_statements"]
        await db_service.execute_sql_statements(sql_statements)

        # 5. セッション状態を更新(今後実装)
        # TODO: セッション管理機能の実装

        theme = table_info.get("theme", "Unknown")
        description = table_info.get("description", "テーブルを作成しました")

        logger.info(f"Successfully created tables for theme: {theme}")

        return UniversalResponse(
            success=True,
            message=description,
            data={
                "theme": theme,
                "table_count": len(
                    [
                        stmt
                        for stmt in sql_statements
                        if stmt.strip().upper().startswith("CREATE TABLE")
                    ]
                ),
            },
        )

    except LLMError as e:
        logger.error(f"LLM error during table creation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except DatabaseError as e:
        logger.error(f"Database error during table creation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except Exception as e:
        logger.error(f"Unexpected error during table creation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": TABLE_CREATION_ERROR,
                "message": "テーブル作成に失敗しました",
                "detail": str(e),
            },
        ) from None
