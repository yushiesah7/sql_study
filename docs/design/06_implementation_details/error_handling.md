# エラーハンドリング詳細設計書

## 概要
このドキュメントでは、SQL学習アプリケーションのエラーハンドリング戦略と具体的な実装を定義します。
ユーザーフレンドリーなエラーメッセージと、開発者向けの詳細なログを両立させます。

## エラーコード体系

### エラーコード形式
```
{CATEGORY}_{SPECIFIC_ERROR}
```

### カテゴリ一覧
| カテゴリ | 説明 | HTTPステータス |
|---------|------|---------------|
| VALIDATION | 入力検証エラー | 400 |
| AUTH | 認証・認可エラー | 401/403 |
| NOT_FOUND | リソース未検出 | 404 |
| CONFLICT | 競合・重複 | 409 |
| DATABASE | DB関連エラー | 500 |
| LLM | AI/LLM関連エラー | 500/503 |
| INTERNAL | その他内部エラー | 500 |
| TIMEOUT | タイムアウト | 504 |

---

## エラーコード完全一覧

### VALIDATION エラー（400）
| エラーコード | メッセージ | 詳細 | 発生箇所 |
|------------|----------|------|---------|
| VALIDATION_INVALID_SQL | SELECT文のみ実行可能です | {detected_statement}文は実行できません | check_answer |
| VALIDATION_EMPTY_SQL | SQLが入力されていません | - | check_answer |
| VALIDATION_SQL_TOO_LONG | SQLが長すぎます | 最大文字数: {max_length} | check_answer |
| VALIDATION_INVALID_PROMPT | プロンプトが不正です | 最大文字数: 1000 | 全API |

### NOT_FOUND エラー（404）
| エラーコード | メッセージ | 詳細 | 発生箇所 |
|------------|----------|------|---------|
| NOT_FOUND_PROBLEM | 指定された問題が見つかりません | problem_id: {id} | check_answer |
| NOT_FOUND_TABLES | テーブルが作成されていません | 先に /api/create-tables を実行してください | generate_problem, table_schemas |

### DATABASE エラー（500）
| エラーコード | メッセージ | 詳細 | 発生箇所 |
|------------|----------|------|---------|
| DATABASE_CONNECTION | データベース接続エラー | {error_detail} | 全API |
| DATABASE_EXECUTION | SQL実行エラー | {error_detail} | create_tables, check_answer |
| DATABASE_TIMEOUT | SQL実行タイムアウト | 制限時間: {timeout}秒 | check_answer |
| DATABASE_SYNTAX | SQL構文エラー | {postgres_error} | check_answer |

### LLM エラー（500/503）
| エラーコード | メッセージ | 詳細 | 発生箇所 |
|------------|----------|------|---------|
| LLM_CONNECTION | AI接続エラー | LocalAIサービスに接続できません | 全API |
| LLM_TIMEOUT | AI応答タイムアウト | 制限時間: {timeout}秒 | 全API |
| LLM_INVALID_RESPONSE | AI応答が不正です | 期待される形式: {expected_format} | 全API |
| LLM_GENERATION_FAILED | 生成に失敗しました | {retry_count}回試行しました | create_tables, generate_problem |

### INTERNAL エラー（500）
| エラーコード | メッセージ | 詳細 | 発生箇所 |
|------------|----------|------|---------|
| INTERNAL_ERROR | 内部エラーが発生しました | - | 全API（フォールバック） |

---

## エラーハンドリング実装

### 1. SQL検証関数

```python
# app/core/validators.py
import re
from typing import Tuple, Optional

# 危険なSQL文のパターン
DANGEROUS_PATTERNS = [
    r'\b(DROP|CREATE|ALTER|TRUNCATE|DELETE|UPDATE|INSERT)\b',
    r'\b(GRANT|REVOKE|EXECUTE|EXEC)\b',
    r';\s*\w+',  # 複数ステートメント
]

# 許可するSQL文のパターン  
ALLOWED_PATTERNS = [
    r'^\s*SELECT\s+',
    r'^\s*WITH\s+.+\s+SELECT\s+',
    r'^\s*\(\s*SELECT\s+',  # サブクエリ
]

def validate_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """
    SQLの安全性を検証
    
    Returns:
        (is_valid, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQLが入力されていません"
    
    sql_upper = sql.upper().strip()
    
    # 長さチェック
    if len(sql) > 5000:
        return False, f"SQLが長すぎます（最大5000文字）"
    
    # 危険なパターンチェック
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper):
            match = re.search(pattern, sql_upper)
            statement = match.group(1) if match else "不明"
            return False, f"{statement}文は実行できません"
    
    # 許可パターンチェック
    valid = any(re.match(pattern, sql_upper) for pattern in ALLOWED_PATTERNS)
    if not valid:
        return False, "SELECT文のみ実行可能です"
    
    return True, None
```

### 2. エラーレスポンスBuilder

```python
# app/core/error_response.py
from typing import Dict, Any, Optional
from datetime import datetime

class ErrorResponseBuilder:
    """エラーレスポンスの構築"""
    
    @staticmethod
    def build(
        error_code: str,
        message: str,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        統一されたエラーレスポンスを構築
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if detail:
            response["error"]["detail"] = detail
            
        if data:
            response["error"]["data"] = data
            
        return response
```

### 3. API実装例（check_answer.py）

```python
# app/api/check_answer.py
from fastapi import APIRouter, Depends
import asyncpg
import logging

from app.schemas import UniversalRequest, CheckAnswerResponse
from app.core.dependencies import get_db, get_llm
from app.core.exceptions import ValidationError, NotFoundError, DatabaseError
from app.core.validators import validate_sql
from app.core.error_response import ErrorResponseBuilder

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/check-answer", response_model=CheckAnswerResponse)
async def check_answer(
    request: UniversalRequest,
    db = Depends(get_db),
    llm = Depends(get_llm)
):
    """SQL回答をチェック"""
    
    # 1. 入力検証
    if not request.context:
        raise ValidationError(
            message="contextが必要です",
            detail="problem_idとuser_sqlを含むcontextを送信してください"
        )
    
    problem_id = request.context.get("problem_id")
    user_sql = request.context.get("user_sql", "").strip()
    
    if not problem_id:
        raise ValidationError(message="problem_idが必要です")
    
    # SQL検証
    is_valid, error_msg = validate_sql(user_sql)
    if not is_valid:
        raise ValidationError(
            message=error_msg,
            detail=f"入力されたSQL: {user_sql[:100]}..."
        )
    
    # 2. 問題情報取得
    try:
        problem = await db.get_problem(problem_id)
        if not problem:
            raise NotFoundError(
                message="指定された問題が見つかりません",
                detail=f"problem_id: {problem_id}"
            )
    except Exception as e:
        logger.error(f"Problem fetch error: {e}")
        raise DatabaseError(
            message="問題情報の取得に失敗しました",
            detail=str(e)
        )
    
    # 3. ユーザーSQLの実行
    try:
        user_result = await db.execute_select(
            user_sql,
            timeout=settings.SQL_EXECUTION_TIMEOUT
        )
    except asyncpg.PostgresSyntaxError as e:
        # SQL構文エラー
        logger.info(f"SQL syntax error: {e}")
        return CheckAnswerResponse(
            is_correct=False,
            message="SQL構文にエラーがあります",
            error_type="syntax",
            error_message=str(e),
            hint=await generate_syntax_hint(str(e), user_sql, llm)
        )
    except asyncio.TimeoutError:
        # タイムアウト
        raise DatabaseError(
            message="SQL実行がタイムアウトしました",
            detail=f"制限時間: {settings.SQL_EXECUTION_TIMEOUT}秒"
        )
    except Exception as e:
        # その他のDBエラー
        logger.error(f"SQL execution error: {e}")
        raise DatabaseError(
            message="SQL実行中にエラーが発生しました",
            detail=str(e)
        )
    
    # 以下、正常処理...
```

### 4. グローバルエラーログ

```python
# app/core/logging.py
import logging
import json
from typing import Dict, Any
from datetime import datetime

class StructuredLogger:
    """構造化ログ出力"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_error(
        self,
        error_code: str,
        message: str,
        context: Dict[str, Any] = None,
        exc_info: Exception = None
    ):
        """エラーログを構造化して出力"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "error_code": error_code,
            "message": message,
            "context": context or {}
        }
        
        if exc_info:
            log_data["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": logging.traceback.format_exc()
            }
        
        self.logger.error(json.dumps(log_data, ensure_ascii=False))
```

---

## エラー時のユーザー体験

### 1. フロントエンド表示例

```typescript
// エラー表示コンポーネント
const ErrorDisplay: React.FC<{ error: ApiError }> = ({ error }) => {
  const getErrorIcon = (code: string) => {
    if (code.startsWith('VALIDATION')) return '⚠️';
    if (code.startsWith('DATABASE')) return '🗄️';
    if (code.startsWith('LLM')) return '🤖';
    return '❌';
  };
  
  const getErrorColor = (code: string) => {
    if (code.startsWith('VALIDATION')) return 'yellow';
    if (code.startsWith('NOT_FOUND')) return 'orange';
    return 'red';
  };
  
  return (
    <div className={`error-box error-${getErrorColor(error.code)}`}>
      <span className="error-icon">{getErrorIcon(error.code)}</span>
      <div className="error-content">
        <p className="error-message">{error.message}</p>
        {error.detail && (
          <p className="error-detail">{error.detail}</p>
        )}
      </div>
    </div>
  );
};
```

### 2. ユーザーフレンドリーなメッセージ変換

```python
# app/core/user_messages.py
USER_FRIENDLY_MESSAGES = {
    "Connection refused": "サービスに接続できません。しばらくしてから再度お試しください。",
    "timeout": "処理に時間がかかりすぎました。もう一度お試しください。",
    "syntax error": "SQL文に誤りがあります。構文を確認してください。",
    "relation .* does not exist": "指定されたテーブルが存在しません。",
    "column .* does not exist": "指定されたカラムが存在しません。",
}

def make_user_friendly(technical_message: str) -> str:
    """技術的なメッセージをユーザーフレンドリーに変換"""
    lower_msg = technical_message.lower()
    
    for pattern, friendly_msg in USER_FRIENDLY_MESSAGES.items():
        if pattern in lower_msg:
            return friendly_msg
    
    return "エラーが発生しました。もう一度お試しください。"
```

---

## テスト戦略

### エラーケーステスト

```python
# tests/test_error_handling.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_invalid_sql_error(client: AsyncClient):
    """不正なSQL文のエラーテスト"""
    response = await client.post(
        "/api/check-answer",
        json={
            "context": {
                "problem_id": 1,
                "user_sql": "DROP TABLE employees"
            }
        }
    )
    
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_INVALID_SQL"
    assert "DROP文は実行できません" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_problem_not_found(client: AsyncClient):
    """存在しない問題IDのテスト"""
    response = await client.post(
        "/api/check-answer",
        json={
            "context": {
                "problem_id": 99999,
                "user_sql": "SELECT * FROM employees"
            }
        }
    )
    
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND_PROBLEM"
```

---

## 運用時の監視

### エラー監視ダッシュボード項目
1. **エラー率**: 総リクエスト数に対するエラーの割合
2. **エラーコード分布**: どのエラーが多いか
3. **エラー発生推移**: 時系列でのエラー発生状況
4. **ユーザー別エラー**: 特定ユーザーで多発していないか

### アラート設定
- エラー率が5%を超えたら警告
- 同一エラーが1分間に10回以上発生したら通知
- DATABASE_CONNECTION エラーは即座に通知

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |