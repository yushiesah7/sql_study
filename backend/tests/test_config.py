"""
設定管理のテスト
"""
import pytest
import os
from app.core.config import Settings


class TestSettings:
    """設定クラスのテスト"""
    
    def test_default_settings(self):
        """
        Test that the Settings class initializes with the correct default values for all configuration parameters.
        """
        settings = Settings()
        
        # アプリケーション設定
        assert settings.APP_NAME == "SQL Learning App"
        assert settings.DEBUG is False
        
        # データベース設定
        assert "postgresql://" in settings.DATABASE_URL
        assert settings.DB_POOL_SIZE == 10
        assert settings.DB_MAX_OVERFLOW == 20
        assert settings.DB_POOL_TIMEOUT == 30.0
        
        # LLM設定
        assert "llm:8080" in settings.LLM_API_URL
        assert settings.LLM_MODEL_NAME == "gpt-3.5-turbo"
        assert settings.LLM_TIMEOUT == 30.0
        assert settings.LLM_MAX_RETRIES == 3
        assert settings.LLM_TEMPERATURE == 0.7
        assert settings.LLM_MAX_TOKENS == 2000
        
        # CORS設定
        assert isinstance(settings.ALLOWED_ORIGINS, list)
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
        
        # セキュリティ設定
        assert settings.SQL_EXECUTION_TIMEOUT == 5.0
        assert settings.MAX_RESULT_ROWS == 100
    
    def test_cors_string_parsing(self):
        """
        Tests that the Settings class correctly parses a comma-separated string from the ALLOWED_ORIGINS environment variable into a list of origins.
        """
        # 環境変数をモック
        os.environ["ALLOWED_ORIGINS"] = "http://test1.com,http://test2.com,http://test3.com"
        
        settings = Settings()
        
        assert len(settings.ALLOWED_ORIGINS) == 3
        assert "http://test1.com" in settings.ALLOWED_ORIGINS
        assert "http://test2.com" in settings.ALLOWED_ORIGINS
        assert "http://test3.com" in settings.ALLOWED_ORIGINS
        
        # クリーンアップ
        del os.environ["ALLOWED_ORIGINS"]
    
    def test_cors_list_format(self):
        """
        Test that ALLOWED_ORIGINS is correctly set when provided as a list to the Settings class.
        """
        settings = Settings(ALLOWED_ORIGINS=["http://example.com", "http://test.com"])
        
        assert len(settings.ALLOWED_ORIGINS) == 2
        assert "http://example.com" in settings.ALLOWED_ORIGINS
        assert "http://test.com" in settings.ALLOWED_ORIGINS
    
    def test_cors_with_spaces(self):
        """
        Test that the Settings class correctly trims spaces from CORS origins provided via the ALLOWED_ORIGINS environment variable.
        """
        os.environ["ALLOWED_ORIGINS"] = " http://test1.com , http://test2.com , http://test3.com "
        
        settings = Settings()
        
        # スペースが正しく削除されているか確認
        assert "http://test1.com" in settings.ALLOWED_ORIGINS
        assert "http://test2.com" in settings.ALLOWED_ORIGINS
        assert "http://test3.com" in settings.ALLOWED_ORIGINS
        assert " http://test1.com " not in settings.ALLOWED_ORIGINS
        
        # クリーンアップ
        del os.environ["ALLOWED_ORIGINS"]
    
    def test_environment_variable_override(self):
        """
        Test that environment variables correctly override default settings in the Settings class.
        
        This test sets environment variables for several configuration options, instantiates the Settings class, and verifies that the overridden values are reflected. Environment variables are cleaned up after the test.
        """
        # 環境変数を設定
        os.environ["APP_NAME"] = "Test App"
        os.environ["DEBUG"] = "true"
        os.environ["DB_POOL_SIZE"] = "20"
        os.environ["LLM_TIMEOUT"] = "60.0"
        
        settings = Settings()
        
        assert settings.APP_NAME == "Test App"
        assert settings.DEBUG is True
        assert settings.DB_POOL_SIZE == 20
        assert settings.LLM_TIMEOUT == 60.0
        
        # クリーンアップ
        del os.environ["APP_NAME"]
        del os.environ["DEBUG"]
        del os.environ["DB_POOL_SIZE"]
        del os.environ["LLM_TIMEOUT"]
    
    def test_numeric_type_conversion(self):
        """
        Test that numeric configuration parameters are correctly assigned and typed in the Settings instance.
        """
        settings = Settings(
            DB_POOL_SIZE=25,
            DB_MAX_OVERFLOW=50,
            DB_POOL_TIMEOUT=45.5,
            LLM_MAX_RETRIES=5,
            LLM_TEMPERATURE=0.8,
            SQL_EXECUTION_TIMEOUT=10.0,
            MAX_RESULT_ROWS=200
        )
        
        assert isinstance(settings.DB_POOL_SIZE, int)
        assert isinstance(settings.DB_MAX_OVERFLOW, int)
        assert isinstance(settings.DB_POOL_TIMEOUT, float)
        assert isinstance(settings.LLM_MAX_RETRIES, int)
        assert isinstance(settings.LLM_TEMPERATURE, float)
        assert isinstance(settings.SQL_EXECUTION_TIMEOUT, float)
        assert isinstance(settings.MAX_RESULT_ROWS, int)
        
        assert settings.DB_POOL_SIZE == 25
        assert settings.DB_MAX_OVERFLOW == 50
        assert settings.DB_POOL_TIMEOUT == 45.5
        assert settings.LLM_MAX_RETRIES == 5
        assert settings.LLM_TEMPERATURE == 0.8
        assert settings.SQL_EXECUTION_TIMEOUT == 10.0
        assert settings.MAX_RESULT_ROWS == 200
    
    def test_boolean_conversion(self):
        """
        Test that string representations of boolean values in the DEBUG environment variable are correctly converted to boolean types in the Settings instance.
        """
        # 文字列からブール値への変換
        os.environ["DEBUG"] = "True"
        settings1 = Settings()
        assert settings1.DEBUG is True
        
        os.environ["DEBUG"] = "false"
        settings2 = Settings()
        assert settings2.DEBUG is False
        
        os.environ["DEBUG"] = "1"
        settings3 = Settings()
        assert settings3.DEBUG is True
        
        os.environ["DEBUG"] = "0"
        settings4 = Settings()
        assert settings4.DEBUG is False
        
        # クリーンアップ
        del os.environ["DEBUG"]
    
    def test_url_format_validation(self):
        """
        Test that the URL settings for the database and LLM API have the expected format.
        
        Validates that `DATABASE_URL` uses the PostgreSQL scheme and contains typical URL components, and that `LLM_API_URL` starts with "http://" and includes a port separator.
        """
        settings = Settings()
        
        # DATABASE_URL
        assert settings.DATABASE_URL.startswith("postgresql://")
        assert "@" in settings.DATABASE_URL
        assert ":" in settings.DATABASE_URL
        
        # LLM_API_URL
        assert settings.LLM_API_URL.startswith("http://")
        assert ":" in settings.LLM_API_URL