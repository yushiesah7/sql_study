"""
問題生成API
現在のテーブル構造に基づいてSQL学習問題を生成
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db_service, get_llm
from app.core.error_codes import NO_TABLES, PROBLEM_GENERATION_ERROR
from app.core.exceptions import DatabaseError, LLMError, NotFoundError
from app.schemas import UniversalRequest, UniversalResponse
from app.services.db_service import DatabaseService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate-problem", response_model=UniversalResponse)
async def generate_problem(
    request: UniversalRequest,
    llm_service: LLMService = Depends(get_llm),
    db_service: DatabaseService = Depends(get_db_service),
) -> UniversalResponse:
    """
    SQL学習問題を生成

    Args:
        request: リクエストデータ(prompt: 省略可、最大1000文字)

    Returns:
        問題ID、実行結果、メタデータ

    Raises:
        HTTPException: 生成失敗時
    """
    try:
        # プロンプトの取得(最大1000文字)
        prompt = request.prompt
        if prompt and len(prompt) > 1000:
            raise HTTPException(
                status_code=400, detail="プロンプトは1000文字以内で入力してください"
            )

        logger.info(
            f"Generating problem with prompt: {prompt[:50] if prompt else 'None'}..."
        )

        # 1. テーブルの存在確認
        table_schemas = await db_service.get_table_schemas()
        if not table_schemas:
            raise NotFoundError(
                message="テーブルが作成されていません。先にテーブルを作成してください。",
                error_code=NO_TABLES,
            )

        # 2. LLMに問題を生成させる
        # TODO: 前回の正答率から難易度を自動調整(1-10レベル)
        problem_info = await llm_service.generate_problem(table_schemas, prompt)

        # 3. 生成されたSQLを実行して結果を取得
        correct_sql = problem_info["correct_sql"]
        try:
            expected_result = await db_service.execute_select_query(
                correct_sql, query_timeout=10
            )
        except DatabaseError:
            logger.exception(f"Generated SQL failed to execute: {correct_sql}")
            raise DatabaseError(
                message="生成された問題のSQLが実行できませんでした",
                error_code=PROBLEM_GENERATION_ERROR,
                detail=f"SQL: {correct_sql[:100]}...",
            ) from None

        # 結果の行数チェック(3-10行でなければ再生成)
        if not (3 <= len(expected_result) <= 10):
            logger.warning(
                f"Generated problem has {len(expected_result)} rows, outside range 3-10"
            )
            # TODO: 再生成ロジックの実装

        # 4. 問題をデータベースに保存
        # 難易度のデフォルト値を型安全に設定
        default_difficulty: Literal["easy", "medium", "hard"] = "medium"
        difficulty = problem_info.get("difficulty", default_difficulty)

        problem_id = await db_service.save_problem(
            theme="未設定",  # TODO: セッション管理から取得
            difficulty=difficulty,
            correct_sql=correct_sql,
            expected_result=expected_result,
            table_schemas=table_schemas,
            hint=problem_info.get("hint"),
        )

        # 5. 結果のメタデータを準備
        column_names = list(expected_result[0].keys()) if expected_result else []

        logger.info(f"Successfully generated problem with ID: {problem_id}")

        return UniversalResponse(
            success=True,
            message="問題を生成しました",
            data={
                "problem_id": problem_id,
                "result": expected_result,
                "row_count": len(expected_result),
                "column_names": column_names,
                "difficulty": problem_info.get("difficulty", "medium"),
            },
        )

    except NotFoundError as e:
        logger.error(f"Tables not found: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except LLMError as e:
        logger.error(f"LLM error during problem generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except DatabaseError as e:
        logger.error(f"Database error during problem generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except Exception as e:
        logger.error(f"Unexpected error during problem generation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": PROBLEM_GENERATION_ERROR,
                "message": "問題生成に失敗しました",
                "detail": str(e),
            },
        ) from None
