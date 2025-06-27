"""
FastAPIアプリケーションのエントリーポイント
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.error_response import ErrorResponseBuilder
from app.schemas import HealthResponse
from app import __version__
from app.api import create_tables, generate_problem, check_answer, table_schemas

# ロガー設定
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info(f"Starting {settings.APP_NAME} v{__version__}")

    # データベース接続
    from app.core.db import db

    await db.connect()
    logger.info("Database connected")

    yield

    # 終了時処理
    await db.disconnect()
    logger.info("Database disconnected")
    logger.info("Shutting down application")


# FastAPIインスタンス作成
app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# グローバルエラーハンドラー
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """アプリケーション例外ハンドラー"""
    logger.error(f"AppException: {exc.error_code} - {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseBuilder.build(
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
            data=exc.data,
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """汎用例外ハンドラー"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponseBuilder.build(
            error_code="INTERNAL_ERROR",
            message="内部エラーが発生しました",
            detail=str(exc) if settings.DEBUG else None,
        ),
    )


# ヘルスチェックエンドポイント
@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """ヘルスチェック"""
    from app.core.db import db
    from app.core.dependencies import get_llm

    # データベース接続チェック
    db_healthy = await db.check_health()

    # LLM接続チェック
    try:
        llm_service = await get_llm()
        llm_healthy = await llm_service.check_health()
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
        llm_healthy = False

    return HealthResponse(
        status="healthy" if db_healthy and llm_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc),
        version=__version__,
        services={
            "database": db_healthy,
            "llm": llm_healthy,
        },
    )


# APIルーター登録
app.include_router(create_tables.router, prefix="/api", tags=["tables"])
app.include_router(generate_problem.router, prefix="/api", tags=["problems"])
app.include_router(check_answer.router, prefix="/api", tags=["answers"])
app.include_router(table_schemas.router, prefix="/api", tags=["schemas"])
