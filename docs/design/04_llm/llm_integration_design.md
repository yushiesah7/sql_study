# LLM統合設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションにおけるLLM（LocalAI）の統合設計を定義します。
LocalAIを使用して、テーブル生成、問題作成、フィードバック生成を実現します。

## LocalAI選定理由

| 観点 | LocalAI | OpenAI API | 
|-----|---------|------------|
| コスト | 無料（自己ホスト） | 従量課金 |
| プライバシー | データが外部に出ない | APIにデータ送信 |
| カスタマイズ | モデル選択可能 | 制限あり |
| レスポンス速度 | ローカル実行 | ネットワーク遅延 |
| Docker統合 | 容易 | 外部依存 |

## システム構成

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│   LocalAI   │────▶│  LLMモデル  │
│  (Backend)  │     │   (Local)   │     │ (日本語対応)│
└─────────────┘     └─────────────┘     └─────────────┘
      │                     │
      │ HTTP Request       │ OpenAI互換API
      └────────────────────┘
```

## LocalAI接続設定

### 環境変数
```env
# LocalAI接続設定
LLM_API_URL=http://llm:8080/v1
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_API_KEY=dummy-key  # LocalAIでは不要だが互換性のため
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=3

# プロンプト設定
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### 接続パラメータ
| パラメータ | 値 | 説明 |
|-----------|---|------|
| base_url | http://llm:8080/v1 | LocalAIのエンドポイント |
| model | gpt-3.5-turbo | 使用するモデル（LocalAI内で設定） |
| timeout | 30秒 | API呼び出しタイムアウト |
| max_retries | 3回 | リトライ回数 |

## 日本語対応モデルの選定

### 推奨モデル
1. **Japanese-GPT-1B** 
   - 軽量で高速
   - 日本語特化
   - CPU実行可能

2. **ELYZA-japanese-Llama-2-7b**
   - 高品質な日本語生成
   - やや重い

3. **OpenCalm-7B**
   - バランス型
   - 安定した性能

### モデル設定（models/gpt-3.5-turbo.yaml）
```yaml
name: gpt-3.5-turbo
parameters:
  model: japanese-gpt-1b.ggml
  temperature: 0.7
  top_k: 40
  top_p: 0.95
context_size: 2048
f16: true
threads: 4
```

## API クライアント設計

### ファイル: backend/app/core/llm_client.py

```python
from typing import Optional, Dict, Any, List
import httpx
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """LLMレスポンスの共通フォーマット"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None

class LLMClient:
    """LocalAI APIクライアント"""
    
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        プロンプトを送信してレスポンスを取得
        
        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            temperature: 生成の多様性（0.0-1.0）
            max_tokens: 最大トークン数
            
        Returns:
            LLMResponse: LLMからの応答
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = await self._call_api(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return self._parse_response(response)
            except Exception as e:
                logger.error(f"LLM API call failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数バックオフ
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> httpx.Response:
        """LocalAI APIを呼び出す"""
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
        )
        response.raise_for_status()
        return response
    
    def _parse_response(self, response: httpx.Response) -> LLMResponse:
        """レスポンスをパース"""
        data = response.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=data.get("usage")
        )
    
    async def close(self):
        """クライアントをクローズ"""
        await self.client.aclose()
```

## エラーハンドリング戦略

### エラーの種類と対処

| エラー種別 | 原因 | 対処法 |
|-----------|------|--------|
| ConnectionError | LocalAI未起動 | ヘルスチェック実装 |
| TimeoutError | 処理時間超過 | タイムアウト延長/簡易化 |
| ValidationError | レスポンス形式エラー | フォールバック処理 |
| ModelError | モデル未ロード | 起動時チェック |

### リトライ戦略
```python
class RetryConfig:
    max_attempts = 3
    base_delay = 1.0  # 秒
    max_delay = 10.0
    exponential_base = 2
    
    @staticmethod
    def should_retry(error: Exception) -> bool:
        """リトライ可能なエラーかチェック"""
        return isinstance(error, (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError
        ))
```

## プロンプト管理設計

### プロンプトテンプレート管理
```python
class PromptTemplate:
    """プロンプトテンプレートの基底クラス"""
    
    def __init__(self, template: str, system_prompt: Optional[str] = None):
        self.template = template
        self.system_prompt = system_prompt
    
    def format(self, **kwargs) -> str:
        """変数を埋め込んでプロンプトを生成"""
        return self.template.format(**kwargs)
    
    def validate_variables(self, variables: Dict[str, Any]) -> bool:
        """必要な変数が含まれているかチェック"""
        # 実装
        pass
```

### プロンプトのバージョン管理
```python
PROMPT_VERSIONS = {
    "table_generation": {
        "v1": "シンプルなテーブル生成",
        "v2": "リレーション考慮版",
        "current": "v2"
    },
    "problem_generation": {
        "v1": "基本的な問題生成",
        "v2": "難易度調整版",
        "current": "v2"
    }
}
```

## パフォーマンス最適化

### 1. 接続プーリング
```python
class LLMConnectionPool:
    """接続プールの管理"""
    def __init__(self, pool_size: int = 5):
        self.pool = asyncio.Queue(maxsize=pool_size)
        self.pool_size = pool_size
```

### 2. レスポンスキャッシュ
```python
from functools import lru_cache
import hashlib

class PromptCache:
    """プロンプトのキャッシュ管理"""
    
    @lru_cache(maxsize=100)
    def get_cached_response(self, prompt_hash: str) -> Optional[str]:
        """キャッシュからレスポンスを取得"""
        pass
    
    def generate_hash(self, prompt: str) -> str:
        """プロンプトのハッシュを生成"""
        return hashlib.md5(prompt.encode()).hexdigest()
```

### 3. バッチ処理
```python
async def batch_generate(
    client: LLMClient,
    prompts: List[str],
    batch_size: int = 5
) -> List[LLMResponse]:
    """複数のプロンプトをバッチ処理"""
    results = []
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i + batch_size]
        tasks = [client.complete(prompt) for prompt in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    return results
```

## モニタリング設計

### メトリクス収集
```python
class LLMMetrics:
    """LLM使用状況のメトリクス"""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    average_response_time: float = 0.0
    
    def record_request(self, success: bool, response_time: float, tokens: int):
        """リクエストを記録"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_tokens_used += tokens
        # 移動平均の更新
        self.average_response_time = (
            self.average_response_time * (self.total_requests - 1) + response_time
        ) / self.total_requests
```

### ログ設計
```python
import structlog

logger = structlog.get_logger()

# 構造化ログの例
logger.info(
    "llm_request",
    prompt_type="table_generation",
    model="japanese-gpt-1b",
    temperature=0.7,
    response_time=2.3,
    tokens_used=450,
    success=True
)
```

## セキュリティ考慮事項

### 1. プロンプトインジェクション対策
```python
def sanitize_user_input(input_text: str) -> str:
    """ユーザー入力をサニタイズ"""
    # 特殊文字のエスケープ
    # プロンプト区切り文字の除去
    # 長さ制限
    return cleaned_text
```

### 2. レート制限
```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)
    
    async def acquire(self):
        await self.semaphore.acquire()
    
    def release(self):
        self.semaphore.release()
```

### 3. 機密情報の保護
- プロンプトにユーザー情報を含めない
- レスポンスログから個人情報を除外
- SQLクエリの実行結果をマスキング

## ヘルスチェック実装

```python
async def check_llm_health(client: LLMClient) -> Dict[str, Any]:
    """LLMサービスのヘルスチェック"""
    try:
        start_time = asyncio.get_event_loop().time()
        response = await client.complete(
            prompt="Hello",
            max_tokens=10
        )
        response_time = asyncio.get_event_loop().time() - start_time
        
        return {
            "status": "healthy",
            "model": response.model,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

## 実装優先順位

1. **基本的なLLMClient実装**
   - 接続設定
   - 基本的なAPI呼び出し
   - エラーハンドリング

2. **プロンプトテンプレート実装**
   - 各機能のプロンプト定義
   - 変数埋め込み機能

3. **最適化機能**
   - リトライメカニズム
   - タイムアウト処理
   - キャッシング（オプション）

4. **モニタリング**
   - メトリクス収集
   - ログ出力
   - ヘルスチェック

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |