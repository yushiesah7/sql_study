# FastAPI構造詳細設計書

## 概要
このドキュメントでは、FastAPIアプリケーションの具体的な実装構造と各ファイルの詳細を定義します。

## ディレクトリ構造（完全版）

```
backend/
├── app/
│   ├── __init__.py          # 空ファイル（Pythonパッケージ化）
│   ├── main.py              # FastAPIアプリのエントリーポイント
│   ├── schemas.py           # Pydanticモデル（リクエスト/レスポンス）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # ルーター統合
│   │   ├── health.py        # ヘルスチェックエンドポイント
│   │   ├── create_tables.py # テーブル作成API
│   │   ├── table_schemas.py # スキーマ取得API
│   │   ├── generate_problem.py # 問題生成API
│   │   └── check_answer.py  # 回答チェックAPI
│   └── core/
│       ├── __init__.py
│       ├── config.py        # 設定管理（環境変数）
│       ├── db.py           # データベース接続管理
│       ├── dependencies.py  # 依存性注入
│       ├── exceptions.py    # カスタム例外とハンドラー
│       ├── llm_client.py   # LocalAIクライアント
│       └── prompts.py      # プロンプトテンプレート
├── requirements.txt         # Pythonパッケージ一覧
├── Dockerfile              # コンテナイメージ定義
└── .env.example            # 環境変数のサンプル
```

---

## 各ファイルの詳細実装

### 1. app/main.py - アプリケーションエントリーポイント

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import api_router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.db import Database
from app.core.llm_client import LLMClient

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# グローバル変数（ライフサイクル管理用）
# db はapp.core.dbモジュールでグローバルインスタンスとして定義
llm_client: LLMClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    global llm_client
    
    # 起動時
    logger.info("Starting up...")
    
    # データベース初期化
    from app.core.db import db
    await db.connect()
    
    # LLMクライアント初期化
    llm_client = LLMClient(
        base_url=settings.LLM_API_URL,
        model=settings.LLM_MODEL_NAME,
        timeout=settings.LLM_TIMEOUT
    )
    
    yield
    
    # 終了時
    logger.info("Shutting down...")
    await db.disconnect()
    await llm_client.close()

# FastAPIアプリケーション作成
app = FastAPI(
    title="SQL学習アプリケーション API",
    description="AIを活用したSQL学習支援システム",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 例外ハンドラー設定
setup_exception_handlers(app)

# ルーター登録
app.include_router(api_router, prefix="/api")

# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "SQL Learning App API", "version": "1.0.0"}
```

### 2. app/core/config.py - 設定管理

```python
import json
from typing import List, Any
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # 基本設定
    APP_NAME: str = "SQL Learning App"
    DEBUG: bool = False
    
    # データベース
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    
    # LocalAI
    LLM_API_URL: str = "http://llm:8080/v1"
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"
    LLM_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 3
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://frontend:3000"]
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> List[str]:
        """
        CORS設定をパース
        - JSON形式: '["http://localhost:3000","http://frontend:3000"]'
        - カンマ区切り: 'http://localhost:3000,http://frontend:3000'
        - リスト形式: ["http://localhost:3000", "http://frontend:3000"]
        """
        if isinstance(v, str):
            # まずJSON形式を試す
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                # JSON形式でない場合は、カンマ区切りとして処理
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        else:
            return []
    
    # セキュリティ
    SQL_EXECUTION_TIMEOUT: float = 5.0
    MAX_RESULT_ROWS: int = 100
    
    model_config = {"env_file": ".env", "case_sensitive": True}

# シングルトンインスタンス
settings = Settings()
```

### 3. app/core/dependencies.py - 依存性注入

```python
from typing import Generator
from fastapi import Depends

from app.core.db import db
from app.core.llm_client import LLMClient
from app.main import llm_client

async def get_db():
    """データベースインスタンスの依存性注入"""
    return db

async def get_llm() -> LLMClient:
    """LLMクライアントの依存性注入"""
    if not llm_client:
        raise RuntimeError("LLM client not initialized")
    return llm_client
```

### 4. app/core/exceptions.py - 例外処理

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)

class AppException(Exception):
    """アプリケーション基底例外"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: str = None
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(self.message)

class DatabaseError(AppException):
    """データベース関連エラー"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            message=message,
            detail=detail
        )

class LLMError(AppException):
    """LLM関連エラー"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="LLM_ERROR",
            message=message,
            detail=detail
        )

class ValidationError(AppException):
    """検証エラー"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            message=message,
            detail=detail
        )

class NotFoundError(AppException):
    """リソース未検出エラー"""
    def __init__(self, message: str, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message,
            detail=detail
        )

async def app_exception_handler(request: Request, exc: AppException):
    """AppException用のハンドラー"""
    logger.error(f"AppException: {exc.error_code} - {exc.message}")
    
    content = {
        "error": {
            "code": exc.error_code,
            "message": exc.message
        }
    }
    
    if exc.detail:
        content["error"]["detail"] = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """一般的な例外のハンドラー"""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "内部エラーが発生しました"
            }
        }
    )

def setup_exception_handlers(app: FastAPI):
    """例外ハンドラーの設定"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

### 5. app/api/routes.py - ルーター統合

```python
from fastapi import APIRouter

from app.api import health, create_tables, table_schemas, generate_problem, check_answer

api_router = APIRouter()

# 各エンドポイントのルーターを登録
api_router.include_router(health.router, tags=["health"])
api_router.include_router(create_tables.router, tags=["tables"])
api_router.include_router(table_schemas.router, tags=["tables"])
api_router.include_router(generate_problem.router, tags=["problems"])
api_router.include_router(check_answer.router, tags=["problems"])
```

### 6. app/api/health.py - ヘルスチェック

```python
from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio
from datetime import datetime

from app.core.dependencies import get_db, get_llm
from app.core.db import Database
from app.core.llm_client import LLMClient

router = APIRouter()

@router.get("/health")
async def health_check(
    db: Database = Depends(get_db),
    llm: LLMClient = Depends(get_llm)
) -> Dict[str, Any]:
    """
    システムヘルスチェック
    
    各コンポーネントの状態を確認します。
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # データベースチェック
    try:
        await db.execute_select("SELECT 1", timeout=2.0)
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # LLMチェック
    try:
        response = await llm.complete(
            prompt="Hello",
            max_tokens=10,
            temperature=0.1
        )
        health_status["components"]["llm"] = {
            "status": "healthy",
            "message": "LLM connection OK",
            "model": response.model
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["llm"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    return health_status
```

### 7. 環境変数ファイル（.env.example）

```env
# Application
APP_NAME="SQL Learning App"
DEBUG=false

# Database
DATABASE_URL=postgresql://postgres:changethis@db:5432/mydb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30.0

# LocalAI
LLM_API_URL=http://llm:8080/v1
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=3
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://frontend:3000"]

# Security
SQL_EXECUTION_TIMEOUT=5.0
MAX_RESULT_ROWS=100
```

---

## 起動設定

### 開発環境での起動
```bash
# backend ディレクトリで
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Dockerでの起動（Dockerfile）
```dockerfile
FROM python:3.11-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係を先にコピーしてキャッシュを活用
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY ./app ./app

# 非rootユーザーで実行（セキュリティ対策）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 実装時の注意点

1. **インポート順序**
   - 標準ライブラリ
   - サードパーティ
   - ローカルモジュール

2. **非同期処理**
   - 全てのDB操作は `async/await`
   - LLM呼び出しも非同期

3. **エラーハンドリング**
   - 各APIで適切な例外を投げる
   - 詳細なログを残す

4. **型ヒント**
   - 全ての関数に型ヒントを付ける
   - Pydanticモデルで厳密な型定義

---

## 動作確認チェックリスト

- [ ] `uvicorn app.main:app` で起動する
- [ ] http://localhost:8000/docs でSwagger UIが表示される
- [ ] /api/health でヘルスチェックが通る
- [ ] 環境変数が正しく読み込まれる
- [ ] ログが適切に出力される