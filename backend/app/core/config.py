"""
アプリケーション設定
"""

import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Application
    APP_NAME: str = Field(default="SQL Learning App")
    DEBUG: bool = Field(default=False)

    # Database
    DATABASE_URL: str = Field(default="postgresql://postgres:changethis@db:5432/mydb")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: float = Field(default=30.0)

    # LocalAI
    LLM_API_URL: str = Field(default="http://llm:8080/v1")
    LLM_MODEL_NAME: str = Field(default="gpt-3.5-turbo")
    LLM_TIMEOUT: float = Field(default=30.0)
    LLM_MAX_RETRIES: int = Field(default=3)
    LLM_TEMPERATURE: float = Field(default=0.7)
    LLM_MAX_TOKENS: int = Field(default=2000)

    # CORS
    ALLOWED_ORIGINS: str | list[str] = Field(
        default=["http://localhost:3000", "http://frontend:3000"]
    )

    # Security
    SQL_EXECUTION_TIMEOUT: float = Field(default=5.0)
    MAX_RESULT_ROWS: int = Field(default=100)

    def get_allowed_origins(self) -> list[str]:
        """CORS許可オリジンのリストを返す"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            # JSON形式を試す
            try:
                parsed = json.loads(self.ALLOWED_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                # カンマ区切りとして処理
                return [i.strip() for i in self.ALLOWED_ORIGINS.split(",")]
        elif isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        else:
            return []

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        # 環境変数から複雑な型を読み込む際にJSON解析をスキップ
        env_parse_none_str="null",
        # validatorでカスタム解析を行う
    )


# グローバル設定インスタンス
settings = Settings()
