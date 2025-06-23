"""
Pydantic入出力モデル定義
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class UniversalRequest(BaseModel):
    """汎用リクエストモデル"""
    prompt: Optional[str] = Field(None, description="ユーザーからのプロンプト")
    context: Optional[Dict[str, Any]] = Field(None, description="追加のコンテキスト情報")


class UniversalResponse(BaseModel):
    """汎用レスポンスモデル"""
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="ユーザー向けメッセージ")
    data: Optional[Dict[str, Any]] = Field(None, description="レスポンスデータ")


class CreateTablesResponse(BaseModel):
    """テーブル作成レスポンス"""
    success: bool = Field(..., description="作成成功フラグ")
    theme: str = Field(..., description="AIが選択したテーマ")
    message: Optional[str] = Field(None, description="ユーザー向けメッセージ")
    tables: Optional[List[str]] = Field(None, description="作成したテーブル名リスト（将来実装）")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細情報（将来実装）")


class GenerateProblemResponse(BaseModel):
    """問題生成レスポンス"""
    problem_id: int = Field(..., description="問題ID")
    difficulty: str = Field(..., description="難易度（easy/medium/hard）")
    expected_result: List[Dict[str, Any]] = Field(..., description="期待される実行結果")
    hint: Optional[str] = Field(None, description="ヒント")
    created_at: datetime = Field(..., description="作成日時")


class CheckAnswerResponse(BaseModel):
    """回答チェックレスポンス"""
    is_correct: bool = Field(..., description="正解フラグ")
    message: str = Field(..., description="判定結果メッセージ")
    user_result: Optional[List[Dict[str, Any]]] = Field(None, description="ユーザーSQLの実行結果")
    expected_result: Optional[List[Dict[str, Any]]] = Field(None, description="期待される実行結果")
    error_type: Optional[str] = Field(None, description="エラータイプ（syntax/logic/none）")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    hint: Optional[str] = Field(None, description="ヒント")
    execution_time: float = Field(..., description="実行時間（秒）")


class TableSchemasResponse(BaseModel):
    """テーブルスキーマ情報レスポンス"""
    tables: List[Dict[str, Any]] = Field(..., description="テーブルスキーマ情報")
    total_count: int = Field(..., description="テーブル総数")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="サービスステータス")
    timestamp: datetime = Field(..., description="レスポンス時刻")
    version: str = Field(..., description="APIバージョン")
    services: Dict[str, bool] = Field(..., description="依存サービスの状態")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: Dict[str, Any] = Field(..., description="エラー情報")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "VALIDATION_INVALID_SQL",
                    "message": "SELECT文のみ実行可能です",
                    "detail": "DROP文は実行できません",
                    "timestamp": "2024-12-22T10:00:00Z"
                }
            }
        }
    }