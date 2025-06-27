"""
回答チェックAPI
ユーザーのSQLを実行して正解と比較し、AIフィードバックを提供
"""

import logging
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db_service, get_llm
from app.core.error_codes import PROBLEM_NOT_FOUND
from app.core.exceptions import DatabaseError, LLMError, NotFoundError
from app.core.validators import validate_sql
from app.schemas import UniversalRequest, UniversalResponse
from app.services.db_service import DatabaseService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


def _compare_results(
    user_result: list[dict[str, Any]], expected_result: list[dict[str, Any]]
) -> bool:
    """
    クエリ結果を比較(カラム順序無視)

    Args:
        user_result: ユーザーの実行結果
        expected_result: 期待される結果

    Returns:
        完全一致するかどうか
    """
    if len(user_result) != len(expected_result):
        return False

    if not user_result and not expected_result:
        return True

    if not user_result or not expected_result:
        return False

    # カラム名の確認
    user_columns = set(user_result[0].keys())
    expected_columns = set(expected_result[0].keys())

    if user_columns != expected_columns:
        return False

    # 行の比較(順序を考慮してソート)
    def normalize_value(value: Any) -> tuple[str, Any]:
        """値を正規化(浮動小数点数の比較を考慮)"""
        if isinstance(value, float):
            return ("float", value)
        return ("other", value)

    def normalize_row(row: dict[str, Any]) -> tuple[tuple[str, tuple[str, Any]], ...]:
        return tuple(sorted((k, normalize_value(v)) for k, v in row.items()))

    def rows_equal(
        row1: tuple[tuple[str, tuple[str, Any]], ...],
        row2: tuple[tuple[str, tuple[str, Any]], ...],
    ) -> bool:
        """行同士を比較(浮動小数点数の近似値比較を含む)"""
        for (k1, (type1, v1)), (k2, (type2, v2)) in zip(row1, row2, strict=False):
            if k1 != k2 or type1 != type2:
                return False
            if type1 == "float":
                if not math.isclose(v1, v2, rel_tol=1e-9, abs_tol=1e-12):
                    return False
            elif v1 != v2:
                return False
        return True

    user_normalized = sorted([normalize_row(row) for row in user_result])
    expected_normalized = sorted([normalize_row(row) for row in expected_result])

    # 全ての行を比較
    if len(user_normalized) != len(expected_normalized):
        return False

    for user_row, expected_row in zip(
        user_normalized, expected_normalized, strict=False
    ):
        if not rows_equal(user_row, expected_row):
            return False

    return True


@router.post("/check-answer", response_model=UniversalResponse)
async def check_answer(
    request: UniversalRequest,
    llm_service: LLMService = Depends(get_llm),
    db_service: DatabaseService = Depends(get_db_service),
) -> UniversalResponse:
    """
    ユーザーのSQL回答をチェック

    Args:
        request: リクエストデータ
            - prompt: 省略可、フィードバック指示
            - context: 必須
                - problem_id: 問題ID
                - user_sql: ユーザーのSQL

    Returns:
        採点結果とフィードバック

    Raises:
        HTTPException: チェック失敗時
    """
    try:
        # リクエスト検証
        if not request.context:
            raise HTTPException(status_code=400, detail="contextが必要です")

        problem_id = request.context.get("problem_id")
        user_sql = request.context.get("user_sql")

        if not problem_id or not user_sql:
            raise HTTPException(
                status_code=400, detail="problem_idとuser_sqlが必要です"
            )

        try:
            problem_id = int(problem_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400, detail="problem_idは数値である必要があります"
            ) from None

        logger.info(f"Checking answer for problem {problem_id}")

        # 1. SQL検証(SELECT文のみ許可)
        is_valid, error_code, error_message = validate_sql(user_sql)
        if not is_valid:
            return UniversalResponse(
                success=False,
                message="SQLが不正です",
                data={
                    "is_correct": False,
                    "error_code": error_code,
                    "error_message": error_message,
                    "hint": "SELECT文のみ実行可能です。SQL構文を確認してください。",
                },
            )

        # 2. 問題情報の取得
        problem = await db_service.get_problem(problem_id)
        if not problem:
            raise NotFoundError(
                message=f"問題ID {problem_id} が見つかりません",
                error_code=PROBLEM_NOT_FOUND,
            )

        expected_result = problem["expected_result"]
        table_schemas = problem["table_schemas"]

        # 3. ユーザーSQLの実行
        try:
            user_result = await db_service.execute_select_query(user_sql, timeout=5)
        except DatabaseError as e:
            # SQL構文エラーの場合は詳細なヒントを提供
            return UniversalResponse(
                success=False,
                message="SQLの実行でエラーが発生しました",
                data={
                    "is_correct": False,
                    "error_message": str(e.detail),
                    "hint": "SQL構文を確認してください。"
                    "テーブル名やカラム名に誤りがないか確認しましょう。",
                },
            )

        # 4. 結果の比較
        is_correct = _compare_results(user_result, expected_result)

        # 5. AIによるフィードバック生成
        feedback_result = await llm_service.check_answer(
            user_sql=user_sql,
            user_result=user_result,
            expected_result=expected_result,
            table_schemas=table_schemas,
        )

        # 6. レスポンス構築
        response_data = {
            "is_correct": is_correct,
            "message": feedback_result.get("feedback", "採点完了"),
            "score": feedback_result.get("score", 100 if is_correct else 0),
        }

        # 不正解の場合は詳細情報を追加
        if not is_correct:
            response_data.update(
                {
                    "user_result": user_result,
                    "expected_result": expected_result,
                    "hint": feedback_result.get(
                        "hint", "結果を比較して、どこが違うか確認してみましょう。"
                    ),
                    "improvement_suggestions": feedback_result.get(
                        "improvement_suggestions", []
                    ),
                }
            )

        logger.info(
            f"Answer check completed for problem {problem_id}: "
            f"{'correct' if is_correct else 'incorrect'}"
        )

        return UniversalResponse(
            success=True, message="回答をチェックしました", data=response_data
        )

    except NotFoundError as e:
        logger.error(f"Problem not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except LLMError as e:
        logger.error(f"LLM error during answer checking: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except DatabaseError as e:
        logger.error(f"Database error during answer checking: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "detail": e.detail,
            },
        ) from None

    except Exception as e:
        logger.error(f"Unexpected error during answer checking: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "ANSWER_CHECK_ERROR",
                "message": "回答チェックに失敗しました",
                "detail": str(e),
            },
        ) from None
