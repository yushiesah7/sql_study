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
        アプリケーション設定から設定パラメータを使用してLocalAIClientを初期化する。
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
        LocalAIチャット完了APIに非同期でチャットメッセージを送信し、検証済みレスポンスを返す。
        
        引数:
            messages (List[Dict[str, str]]): モデルに送信するチャットメッセージオブジェクトのリスト。
            temperature (Optional[float]): レスポンス生成のサンプリング温度。指定されない場合、設定されたデフォルト値を使用。
            max_tokens (Optional[int]): 生成されるレスポンスの最大トークン数。指定されない場合、設定されたデフォルト値を使用。
        
        戻り値:
            Dict[str, Any]: OpenAI互換形式のLocalAIサービスからの検証済みレスポンス。
        
        例外:
            LLMError: 接続問題、タイムアウト、無効なレスポンス、またはすべてのリトライ試行後の反復エラーによりAPI呼び出しが失敗した場合。
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
        LLMレスポンスが期待されるOpenAIチャット完了形式に適合することを検証する。
        
        引数:
            response (Dict[str, Any]): LLMサービスからの生レスポンス。
        
        戻り値:
            Dict[str, Any]: 検証済みレスポンス辞書。
        
        例外:
            LLMError: レスポンス構造が無効または必要なフィールドが欠如している場合。
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
        検証済みLLMレスポンスの最初の選択肢のメッセージから生成されたテキストコンテンツを抽出して返す。
        
        引数:
            response (Dict[str, Any]): LLMチャット完了APIからの検証済みレスポンス。
        
        戻り値:
            str: LLMによって生成されたトリム済みテキストコンテンツ。
        """
        return response["choices"][0]["message"]["content"].strip()
    
    async def check_health(self) -> bool:
        """
        LLMサービスが到達可能で応答性があるかを確認する。
        
        戻り値:
            bool: サービスがテストチャット完了リクエストに正常に応答する場合True、そうでなければFalse。
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