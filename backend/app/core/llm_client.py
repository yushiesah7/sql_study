"""
LocalAIクライアント実装
OpenAI API互換のHTTPクライアント
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.error_codes import (
    LLM_CONNECTION,
    LLM_TIMEOUT,
    LLM_INVALID_RESPONSE,
    LLM_GENERATION_FAILED
)

logger = logging.getLogger(__name__)


class LocalAIClient:
    """LocalAI HTTPクライアント"""
    
    def __init__(self):
        """
        Initializes the LocalAIClient with configuration parameters from application settings.
        """
        self.base_url = settings.LLM_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously sends chat messages to the LocalAI chat completion API and returns the validated response.
        
        Parameters:
            messages (List[Dict[str, str]]): List of chat message objects to send to the model.
            temperature (Optional[float]): Sampling temperature for response generation. If not provided, uses the default configured value.
            max_tokens (Optional[int]): Maximum number of tokens in the generated response. If not provided, uses the default configured value.
        
        Returns:
            Dict[str, Any]: The validated response from the LocalAI service in OpenAI-compatible format.
        
        Raises:
            LLMError: If the API call fails due to connection issues, timeouts, invalid responses, or repeated errors after all retry attempts.
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False
        }
        
        # リトライ機能付きで実行
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return self._validate_response(result)
                    else:
                        logger.warning(f"LLM API error (attempt {attempt + 1}): {response.status_code} - {response.text}")
                        if attempt == self.max_retries - 1:
                            raise LLMError(
                                message=f"LLM API エラー: {response.status_code}",
                                error_code=LLM_CONNECTION,
                                detail=response.text
                            )
                        
            except asyncio.TimeoutError:
                logger.warning(f"LLM API timeout (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM API タイムアウト",
                        error_code=LLM_TIMEOUT,
                        detail=f"制限時間: {self.timeout}秒"
                    )
                    
            except httpx.ConnectError:
                logger.warning(f"LLM connection error (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM接続エラー",
                        error_code=LLM_CONNECTION,
                        detail="LocalAIサービスに接続できません"
                    )
                    
            except Exception as e:
                logger.error(f"Unexpected LLM error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise LLMError(
                        message="LLM処理エラー",
                        error_code=LLM_GENERATION_FAILED,
                        detail=str(e)
                    )
            
            # リトライ前に少し待機
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)
        
        # ここには到達しないはず
        raise LLMError(
            message="LLM生成に失敗しました",
            error_code=LLM_GENERATION_FAILED,
            detail=f"{self.max_retries}回試行しました"
        )
    
    def _validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the LLM response conforms to the expected OpenAI chat completion format.
        
        Parameters:
            response (Dict[str, Any]): The raw response from the LLM service.
        
        Returns:
            Dict[str, Any]: The validated response dictionary.
        
        Raises:
            LLMError: If the response structure is invalid or missing required fields.
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
                detail=f"期待される形式: OpenAI chat completions. エラー: {str(e)}"
            )
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extracts and returns the generated text content from the first choice's message in a validated LLM response.
        
        Parameters:
            response (Dict[str, Any]): A validated response from the LLM chat completion API.
        
        Returns:
            str: The trimmed text content generated by the LLM.
        """
        return response["choices"][0]["message"]["content"].strip()
    
    async def check_health(self) -> bool:
        """
        Check if the LLM service is reachable and responsive.
        
        Returns:
            bool: True if the service responds successfully to a test chat completion request, otherwise False.
        """
        try:
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model_name,
                        "messages": test_messages,
                        "max_tokens": 5
                    },
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code == 200
                
        except Exception:
            return False


# グローバルクライアントインスタンス
llm_client = LocalAIClient()