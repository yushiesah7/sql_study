"""
FastAPIアプリケーションのテスト
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.core.exceptions import DatabaseError


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""
    
    def setup_method(self):
        """
        Initializes a new TestClient instance for each test method.
        """
        self.client = TestClient(app)
    
    @patch('app.core.db.db.check_health', new_callable=AsyncMock)
    @patch('app.core.dependencies.get_llm', new_callable=AsyncMock)
    def test_health_check_success(self, mock_get_llm, mock_check_health):
        """
        Test that the health check endpoint returns a healthy status and correct response structure when all services are healthy.
        """
        # モック設定
        mock_check_health.return_value = True
        mock_llm_service = AsyncMock()
        mock_llm_service.check_health.return_value = True
        mock_get_llm.return_value = mock_llm_service
        
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        assert data["services"]["database"] is True
        assert data["services"]["llm"] is True
    
    @patch('app.core.db.db.check_health', new_callable=AsyncMock)
    @patch('app.core.dependencies.get_llm', new_callable=AsyncMock)
    def test_health_check_database_failure(self, mock_get_llm, mock_check_health):
        """
        Test that the health check endpoint reports an unhealthy status when the database health check fails but the LLM service is healthy.
        """
        # モック設定
        mock_check_health.return_value = False
        mock_llm_service = AsyncMock()
        mock_llm_service.check_health.return_value = True
        mock_get_llm.return_value = mock_llm_service
        
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["services"]["database"] is False
        assert data["services"]["llm"] is True
    
    def test_health_check_response_format(self):
        """
        Test that the health check endpoint returns a response with the correct structure and data types.
        
        Verifies the presence of required fields (`status`, `timestamp`, `version`, `services`) in the response, ensures that `services` contains both `database` and `llm`, and checks that all fields have the expected types.
        """
        with patch('app.core.db.db.check_health', new_callable=AsyncMock) as mock_check_health, \
             patch('app.core.dependencies.get_llm', new_callable=AsyncMock) as mock_get_llm:
            mock_check_health.return_value = True
            mock_llm_service = AsyncMock()
            mock_llm_service.check_health.return_value = True
            mock_get_llm.return_value = mock_llm_service
            
            response = self.client.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # 必須フィールドの確認
            required_fields = ["status", "timestamp", "version", "services"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # services内の必須フィールド
            services_fields = ["database", "llm"]
            for field in services_fields:
                assert field in data["services"], f"Missing services field: {field}"
            
            # 型の確認
            assert isinstance(data["status"], str)
            assert isinstance(data["timestamp"], str)
            assert isinstance(data["version"], str)
            assert isinstance(data["services"], dict)
            assert isinstance(data["services"]["database"], bool)
            assert isinstance(data["services"]["llm"], bool)


class TestErrorHandling:
    """エラーハンドリングのテスト"""
    
    def setup_method(self):
        """
        Initializes a new TestClient instance for each test method.
        """
        self.client = TestClient(app)
    
    def test_404_not_found(self):
        """
        Test that a GET request to a nonexistent endpoint returns a 404 Not Found response.
        """
        response = self.client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """
        Test that sending a DELETE request to the /api/health endpoint returns HTTP 405 Method Not Allowed.
        """
        response = self.client.delete("/api/health")
        
        assert response.status_code == 405


class TestCORS:
    """CORS設定のテスト"""
    
    def setup_method(self):
        """
        Initializes a new TestClient instance for each test method.
        """
        self.client = TestClient(app)
    
    def test_cors_preflight(self):
        """
        Test that a CORS preflight (OPTIONS) request to the health endpoint returns a valid status code.
        
        Sends an OPTIONS request with appropriate CORS headers and asserts that the response status code is either 200 or 204, indicating correct CORS configuration.
        """
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        
        response = self.client.options("/api/health", headers=headers)
        
        # CORS設定により200または204が返される
        assert response.status_code in [200, 204]
    
    def test_cors_actual_request(self):
        """
        Tests that an actual CORS GET request to the health endpoint returns a successful response and includes the appropriate CORS headers.
        """
        headers = {
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json",
        }
        
        with patch('app.core.db.db.check_health', new_callable=AsyncMock) as mock_check_health, \
             patch('app.core.dependencies.get_llm', new_callable=AsyncMock) as mock_get_llm:
            mock_check_health.return_value = True
            mock_llm_service = AsyncMock()
            mock_llm_service.check_health.return_value = True
            mock_get_llm.return_value = mock_llm_service
            
            response = self.client.get("/api/health", headers=headers)
            
            assert response.status_code == 200
            # CORSヘッダーの確認
            assert "access-control-allow-origin" in response.headers


class TestApplicationLifecycle:
    """アプリケーションライフサイクルのテスト"""
    
    def test_app_creation(self):
        """
        Test that the FastAPI application instance is created and has the correct title.
        """
        assert app is not None
        assert app.title == "SQL Learning App"
    
    def test_middleware_setup(self):
        """
        Test that the CORS middleware is correctly included in the application's middleware stack.
        """
        # CORSミドルウェアが正しく設定されているかテスト
        middlewares = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middlewares
    
    def test_exception_handlers_registered(self):
        """
        Test that custom exception handlers for AppException and the base Exception are registered in the FastAPI application.
        """
        # 例外ハンドラーが登録されているかテスト
        exception_handlers = app.exception_handlers
        
        # カスタム例外ハンドラーが登録されているか確認
        from app.core.exceptions import AppException
        assert AppException in exception_handlers
        assert Exception in exception_handlers


class TestOpenAPISchema:
    """OpenAPIスキーマのテスト"""
    
    def setup_method(self):
        """
        Initializes a new TestClient instance for each test method.
        """
        self.client = TestClient(app)
    
    def test_openapi_schema_accessible(self):
        """
        Test that the OpenAPI schema is accessible and contains the expected metadata.
        
        Asserts that the `/openapi.json` endpoint returns a 200 status code, includes the required OpenAPI fields, and that the API title matches "SQL Learning App".
        """
        response = self.client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "SQL Learning App"
    
    def test_docs_accessible(self):
        """
        Test that the Swagger UI documentation endpoint (/docs) is accessible and returns HTML content.
        """
        response = self.client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_accessible(self):
        """
        Test that the ReDoc documentation endpoint is accessible and returns HTML content.
        """
        response = self.client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]