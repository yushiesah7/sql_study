"""
カスタム例外クラス定義
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """アプリケーション基底例外"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail
        self.data = data
        super().__init__(self.message)


class ValidationError(AppException):
    """入力検証エラー"""
    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        detail: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            detail=detail
        )


class NotFoundError(AppException):
    """リソース未検出エラー"""
    def __init__(
        self,
        message: str,
        error_code: str = "NOT_FOUND",
        detail: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            detail=detail
        )


class DatabaseError(AppException):
    """データベース関連エラー"""
    def __init__(
        self,
        message: str,
        error_code: str = "DATABASE_ERROR",
        detail: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            detail=detail
        )


class LLMError(AppException):
    """LLM関連エラー"""
    def __init__(
        self,
        message: str,
        error_code: str = "LLM_ERROR",
        detail: Optional[str] = None,
        status_code: int = 500
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            detail=detail
        )