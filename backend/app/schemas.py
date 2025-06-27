"""
Pydantic入出力モデル定義
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UniversalRequest(BaseModel):
    """汎用リクエストモデル"""

    prompt: str | None = Field(None, description="ユーザーからのプロンプト")
    context: dict[str, Any] | None = Field(None, description="追加のコンテキスト情報")


class UniversalResponse(BaseModel):
    """汎用レスポンスモデル"""

    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="ユーザー向けメッセージ")
    data: dict[str, Any] | None = Field(None, description="レスポンスデータ")


class CreateTablesResponse(BaseModel):
    """テーブル作成レスポンス"""

    success: bool = Field(..., description="作成成功フラグ")
    theme: str = Field(..., description="AIが選択したテーマ")
    message: str | None = Field(None, description="ユーザー向けメッセージ")
    tables: list[str] | None = Field(
        None, description="作成したテーブル名リスト（将来実装）"
    )
    details: dict[str, Any] | None = Field(None, description="詳細情報（将来実装）")


class GenerateProblemResponse(BaseModel):
    """問題生成レスポンス"""

    problem_id: int = Field(..., description="問題ID")
    difficulty: str = Field(..., description="難易度（easy/medium/hard）")
    expected_result: list[dict[str, Any]] = Field(..., description="期待される実行結果")
    hint: str | None = Field(None, description="ヒント")
    created_at: datetime = Field(..., description="作成日時")


class CheckAnswerResponse(BaseModel):
    """回答チェックレスポンス"""

    is_correct: bool = Field(..., description="正解フラグ")
    message: str = Field(..., description="判定結果メッセージ")
    user_result: list[dict[str, Any]] | None = Field(
        None, description="ユーザーSQLの実行結果"
    )
    expected_result: list[dict[str, Any]] | None = Field(
        None, description="期待される実行結果"
    )
    error_type: str | None = Field(
        None, description="エラータイプ（syntax/logic/none）"
    )
    error_message: str | None = Field(None, description="エラーメッセージ")
    hint: str | None = Field(None, description="ヒント")
    execution_time: float = Field(..., description="実行時間（秒）")


class TableSchemasResponse(BaseModel):
    """テーブルスキーマ情報レスポンス"""

    tables: list[dict[str, Any]] = Field(..., description="テーブルスキーマ情報")
    total_count: int = Field(..., description="テーブル総数")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str = Field(..., description="サービスステータス")
    timestamp: datetime = Field(..., description="レスポンス時刻")
    version: str = Field(..., description="APIバージョン")
    services: dict[str, bool] = Field(..., description="依存サービスの状態")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    error: dict[str, Any] = Field(..., description="エラー情報")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "VALIDATION_INVALID_SQL",
                    "message": "SELECT文のみ実行可能です",
                    "detail": "DROP文は実行できません",
                    "timestamp": "2024-12-22T10:00:00Z",
                }
            }
        }
    }
