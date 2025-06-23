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
        """
        Initialize an AppException with a message, error code, HTTP status code, optional detail, and additional data.
        
        Parameters:
            message (str): The main error message.
            error_code (str): A string identifier for the error type.
            status_code (int, optional): HTTP status code associated with the error. Defaults to 500.
            detail (str, optional): Additional details about the error.
            data (dict, optional): Extra data relevant to the error.
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail
        self.data = data
        super().__init__(self.message)


class ValidationError(AppException):
    """入力検証エラー"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR", detail: Optional[str] = None):
        """
        Initialize a ValidationError for input validation failures.
        
        Parameters:
            message (str): Description of the validation error.
            error_code (str, optional): Application-specific error code. Defaults to "VALIDATION_ERROR".
            detail (str, optional): Additional details about the validation error.
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            detail=detail
        )


class NotFoundError(AppException):
    """リソース未検出エラー"""
    def __init__(self, message: str, error_code: str = "NOT_FOUND", detail: Optional[str] = None):
        """
        Initialize a NotFoundError for signaling that a requested resource could not be found.
        
        Parameters:
            message (str): Description of the missing resource or context of the error.
            error_code (str, optional): Custom error code identifier. Defaults to "NOT_FOUND".
            detail (str, optional): Additional details about the error.
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            detail=detail
        )


class DatabaseError(AppException):
    """データベース関連エラー"""
    def __init__(self, message: str, error_code: str = "DATABASE_ERROR", detail: Optional[str] = None):
        """
        Initialize a DatabaseError for representing database-related failures.
        
        Parameters:
            message (str): Description of the database error.
            error_code (str, optional): Application-specific error code. Defaults to "DATABASE_ERROR".
            detail (str, optional): Additional details about the error.
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            detail=detail
        )


class LLMError(AppException):
    """LLM関連エラー"""
    def __init__(self, message: str, error_code: str = "LLM_ERROR", detail: Optional[str] = None, status_code: int = 500):
        """
        Initialize an LLMError for errors related to large language model operations.
        
        Parameters:
            message (str): Description of the error.
            error_code (str, optional): Identifier for the error type. Defaults to "LLM_ERROR".
            detail (str, optional): Additional details about the error.
            status_code (int, optional): HTTP status code associated with the error. Defaults to 500.
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            detail=detail
        )