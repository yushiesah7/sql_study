"""
例外処理のテスト
"""
import pytest
from app.core.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    DatabaseError,
    LLMError
)
from app.core.error_codes import (
    VALIDATION_INVALID_SQL,
    NOT_FOUND_PROBLEM,
    DATABASE_CONNECTION,
    LLM_TIMEOUT
)


class TestAppException:
    """AppException基底クラスのテスト"""
    
    def test_app_exception_creation(self):
        """AppException作成のテスト"""
        exc = AppException(
            message="テストエラー",
            error_code="TEST_ERROR",
            status_code=500,
            detail="詳細情報",
            data={"key": "value"}
        )
        
        assert exc.message == "テストエラー"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 500
        assert exc.detail == "詳細情報"
        assert exc.data == {"key": "value"}
        assert str(exc) == "テストエラー"
    
    def test_app_exception_minimal(self):
        """最小構成のAppExceptionテスト"""
        exc = AppException(
            message="最小エラー",
            error_code="MIN_ERROR",
            status_code=400
        )
        
        assert exc.message == "最小エラー"
        assert exc.error_code == "MIN_ERROR"
        assert exc.status_code == 400
        assert exc.detail is None
        assert exc.data is None


class TestValidationError:
    """ValidationErrorのテスト"""
    
    def test_validation_error_with_code(self):
        """エラーコード指定ありのValidationError"""
        exc = ValidationError(
            message="不正なSQL",
            error_code=VALIDATION_INVALID_SQL,
            detail="SELECT文のみ許可されています"
        )
        
        assert exc.message == "不正なSQL"
        assert exc.error_code == VALIDATION_INVALID_SQL
        assert exc.status_code == 400
        assert exc.detail == "SELECT文のみ許可されています"
    
    def test_validation_error_default_code(self):
        """デフォルトエラーコードのValidationError"""
        exc = ValidationError(message="一般的な検証エラー")
        
        assert exc.message == "一般的な検証エラー"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.detail is None


class TestNotFoundError:
    """NotFoundErrorのテスト"""
    
    def test_not_found_error_with_code(self):
        """エラーコード指定ありのNotFoundError"""
        exc = NotFoundError(
            message="問題が見つかりません",
            error_code=NOT_FOUND_PROBLEM,
            detail="problem_id: 123"
        )
        
        assert exc.message == "問題が見つかりません"
        assert exc.error_code == NOT_FOUND_PROBLEM
        assert exc.status_code == 404
        assert exc.detail == "problem_id: 123"
    
    def test_not_found_error_default_code(self):
        """デフォルトエラーコードのNotFoundError"""
        exc = NotFoundError(message="リソースが見つかりません")
        
        assert exc.message == "リソースが見つかりません"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404


class TestDatabaseError:
    """DatabaseErrorのテスト"""
    
    def test_database_error_with_code(self):
        """エラーコード指定ありのDatabaseError"""
        exc = DatabaseError(
            message="データベース接続エラー",
            error_code=DATABASE_CONNECTION,
            detail="Connection refused"
        )
        
        assert exc.message == "データベース接続エラー"
        assert exc.error_code == DATABASE_CONNECTION
        assert exc.status_code == 500
        assert exc.detail == "Connection refused"
    
    def test_database_error_default_code(self):
        """デフォルトエラーコードのDatabaseError"""
        exc = DatabaseError(message="一般的なDBエラー")
        
        assert exc.message == "一般的なDBエラー"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500


class TestLLMError:
    """LLMErrorのテスト"""
    
    def test_llm_error_with_code(self):
        """エラーコード指定ありのLLMError"""
        exc = LLMError(
            message="LLMタイムアウト",
            error_code=LLM_TIMEOUT,
            detail="30秒でタイムアウト",
            status_code=503
        )
        
        assert exc.message == "LLMタイムアウト"
        assert exc.error_code == LLM_TIMEOUT
        assert exc.status_code == 503
        assert exc.detail == "30秒でタイムアウト"
    
    def test_llm_error_default_values(self):
        """デフォルト値のLLMError"""
        exc = LLMError(message="一般的なLLMエラー")
        
        assert exc.message == "一般的なLLMエラー"
        assert exc.error_code == "LLM_ERROR"
        assert exc.status_code == 500
        assert exc.detail is None


class TestExceptionInheritance:
    """例外の継承関係のテスト"""
    
    def test_inheritance_chain(self):
        """継承チェーンのテスト"""
        validation_error = ValidationError("テスト")
        
        assert isinstance(validation_error, ValidationError)
        assert isinstance(validation_error, AppException)
        assert isinstance(validation_error, Exception)
    
    def test_exception_can_be_raised(self):
        """例外が正しく発生するかのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("テストエラー", VALIDATION_INVALID_SQL)
        
        assert exc_info.value.message == "テストエラー"
        assert exc_info.value.error_code == VALIDATION_INVALID_SQL
        assert exc_info.value.status_code == 400