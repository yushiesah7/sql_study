"""
LocalAIクライアント実装
OpenAI API互換のHTTPクライアント
"""

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.error_codes import (
    LLM_CONNECTION,
    LLM_GENERATION_FAILED,
    LLM_INVALID_RESPONSE,
    LLM_TIMEOUT,
)
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LocalAIClient:
    """LocalAI HTTPクライアント"""

    def __init__(self) -> None:
        self.base_url = settings.LLM_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        チャット補完APIを呼び出し

        Args:
            messages: チャットメッセージのリスト
            temperature: サンプリング温度(オプション)
            max_tokens: 最大トークン数(オプション)

        Returns:
            LLMからのレスポンス

        Raises:
            LLMError: API呼び出し失敗時
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }

        # リトライ機能付きで実行
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, read=self.timeout)) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return self._validate_response(result)

                    logger.warning(
                        f"LLM API error (attempt {attempt + 1}): "
                        f"{response.status_code} - {response.text}"
                    )
                    if attempt == self.max_retries - 1:
                        raise LLMError(
                            message=f"LLM API エラー: {response.status_code}",
                            error_code=LLM_CONNECTION,
                            detail=response.text,
                        )

            except TimeoutError:
                logger.warning(f"LLM API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM API タイムアウト",
                        error_code=LLM_TIMEOUT,
                        detail=f"制限時間: {self.timeout}秒",
                    ) from None

            except httpx.ConnectError:
                logger.warning(f"LLM connection error (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM接続エラー",
                        error_code=LLM_CONNECTION,
                        detail="LocalAIサービスに接続できません",
                    ) from None

            except Exception as e:
                logger.error(f"Unexpected LLM error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM処理エラー",
                        error_code=LLM_GENERATION_FAILED,
                        detail=str(e),
                    ) from None

            # リトライ前に少し待機
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)

        # ここには到達しないはず
        raise LLMError(
            message="LLM生成に失敗しました",
            error_code=LLM_GENERATION_FAILED,
            detail=f"{self.max_retries}回試行しました",
        )

    def _validate_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        LLMレスポンスの検証

        Args:
            response: LLMからの生レスポンス

        Returns:
            検証済みレスポンス

        Raises:
            LLMError: レスポンス形式が不正な場合
        """
        try:
            # OpenAI API形式の検証
            if "choices" not in response:
                raise ValueError("'choices' field missing")

            if not response["choices"]:
                raise ValueError("Empty choices array")

            choice = response["choices"][0]
            if "message" not in choice:
                raise ValueError("'message' field missing in choice")

            message = choice["message"]
            if "content" not in message:
                raise ValueError("'content' field missing in message")

            return response

        except (KeyError, ValueError, IndexError) as e:
            logger.error(f"Invalid LLM response format: {e}")
            raise LLMError(
                message="LLM応答が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail=f"期待される形式: OpenAI chat completions. エラー: {e!s}",
            ) from None

    def extract_content(self, response: dict[str, Any]) -> str:
        """
        レスポンスからコンテンツを抽出

        Args:
            response: 検証済みLLMレスポンス

        Returns:
            生成されたテキストコンテンツ
        """
        content: str = response["choices"][0]["message"]["content"]
        return content.strip()

    async def check_health(self) -> bool:
        """
        LLM接続の健全性をチェック

        Returns:
            接続可能かどうか
        """
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            
            logger.debug(f"LLM health check - URL: {self.base_url}, Model: {self.model_name}")

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": test_messages,
                        "max_tokens": 5,
                    },
                    headers={"Content-Type": "application/json"},
                )
                
                logger.info(f"LLM health check response - Status: {response.status_code}, "
                           f"Headers: {dict(response.headers)}")
                
                if response.status_code != 200:
                    logger.warning(f"LLM health check failed - Status: {response.status_code}, "
                                 f"Body: {response.text[:500]}")
                else:
                    logger.info("LLM health check successful")
                
                return response.status_code == 200

        except Exception as e:
            logger.error(f"LLM health check failed with exception: {type(e).__name__}: {e}")
            return False


# グローバルクライアントインスタンス
llm_client = LocalAIClient()
