# データモデル設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションのAPI通信で使用するデータモデル（Pydanticスキーマ）を定義します。
シンプルさと拡張性を重視し、初期段階では最小限の構成で、将来的に機能追加可能な設計としています。

## 設計方針

1. **統一されたリクエスト形式**: 全てのエンドポイントで同じリクエストモデルを使用
2. **オプショナルな設計**: ほとんどのフィールドはOptionalで、AIが適切に補完
3. **段階的な拡張**: 初期は`{}`だけで動作し、必要に応じてフィールドを活用

## 汎用リクエストモデル

### UniversalRequest

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class UniversalRequest(BaseModel):
    """全てのAPIエンドポイントで使用する汎用リクエストモデル"""
    
    prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "最小構成（テーブル作成・問題生成）",
                    "value": {}
                },
                {
                    "description": "プロンプト指定",
                    "value": {
                        "prompt": "JOINを使った中級レベルの問題"
                    }
                },
                {
                    "description": "回答チェック",
                    "value": {
                        "context": {
                            "problem_id": 1,
                            "user_sql": "SELECT * FROM employees"
                        }
                    }
                }
            ]
        }
```

## 各エンドポイントでの使用方法

| エンドポイント | 必須フィールド | オプション | 使用例 |
|------------|------------|----------|-------|
| POST /api/create-tables | なし | prompt | `{}` |
| POST /api/generate-problem | なし | prompt | `{}` |
| POST /api/check-answer | context.problem_id, context.user_sql | prompt | 下記参照 |

### 使用例詳細

#### 1. テーブル作成
```json
// 最小構成（AIが全て決定）
{}

// テーマ指定（将来）
{
  "prompt": "ECサイトのテーブルを作成"
}

// 詳細指定（将来）
{
  "prompt": "商品数1000件、注文数5000件の大規模ECサイト"
}
```

#### 2. 問題生成
```json
// 最小構成（AIが自動で難易度調整）
{}

// カテゴリ指定
{
  "prompt": "集計関数を使う問題"
}

// 複雑な指示
{
  "prompt": "GROUP BYとHAVINGを組み合わせた問題で、結果が3-5行になるもの"
}
```

#### 3. 回答チェック
```json
// 必須構成
{
  "context": {
    "problem_id": 42,
    "user_sql": "SELECT name, salary FROM employees WHERE department_id = 10"
  }
}

// フィードバック方法を指定（将来）
{
  "prompt": "ヒントを多めに、初心者向けの説明で",
  "context": {
    "problem_id": 42,
    "user_sql": "SELECT * FROM employees"
  }
}
```

## レスポンスモデル

### CreateTablesResponse

```python
class CreateTablesResponse(BaseModel):
    """テーブル作成APIのレスポンス"""
    
    success: bool
    theme: str  # AIが選択したテーマ（例: "社員管理"）
    message: Optional[str] = None  # ユーザー向けメッセージ
    
    # 将来の拡張用
    tables: Optional[List[str]] = None  # 作成したテーブル名リスト
    details: Optional[Dict[str, Any]] = None  # 詳細情報
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "theme": "社員管理",
                "message": "社員管理システムのテーブルを3つ作成しました"
            }
        }
```

### GenerateProblemResponse

```python
from datetime import datetime
from typing import List, Dict, Any

class GenerateProblemResponse(BaseModel):
    """問題生成APIのレスポンス"""
    
    problem_id: int  # 問題の一意識別子
    result: List[Dict[str, Any]]  # SQLの実行結果
    
    # 自動計算可能だが、利便性のため含める
    row_count: Optional[int] = None
    column_names: Optional[List[str]] = None
    
    # メタ情報
    created_at: Optional[datetime] = None
    difficulty: Optional[int] = None  # 1-10
    category: Optional[str] = None  # "join", "aggregate" など
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_id": 42,
                "result": [
                    {"name": "田中太郎", "department": "営業部", "salary": 350000},
                    {"name": "佐藤花子", "department": "営業部", "salary": 400000}
                ],
                "row_count": 2,
                "column_names": ["name", "department", "salary"]
            }
        }
```

### CheckAnswerResponse

```python
class CheckAnswerResponse(BaseModel):
    """回答チェックAPIのレスポンス"""
    
    is_correct: bool
    message: str  # AIが生成したフィードバック
    
    # 詳細情報（オプション）
    user_result: Optional[List[Dict[str, Any]]] = None  # ユーザーのSQL実行結果
    expected_result: Optional[List[Dict[str, Any]]] = None  # 期待される結果（不正解時）
    
    # 追加のフィードバック
    advice: Optional[str] = None  # 改善のアドバイス
    hint: Optional[str] = None  # ヒント（不正解時）
    alternative_solutions: Optional[List[str]] = None  # 別解
    
    # エラー情報
    error_type: Optional[str] = None  # "syntax", "logic", "timeout"
    error_message: Optional[str] = None  # エラーの詳細
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "正解の場合",
                    "value": {
                        "is_correct": True,
                        "message": "正解です！JOINを使った良い解答です。"
                    }
                },
                {
                    "description": "不正解の場合",
                    "value": {
                        "is_correct": False,
                        "message": "惜しいです！結果の行数が異なります。",
                        "hint": "WHERE句の条件を確認してみましょう。"
                    }
                }
            ]
        }
```

### エラーレスポンス

```python
class ErrorResponse(BaseModel):
    """全APIで共通のエラーレスポンス"""
    
    error: ErrorDetail
    
class ErrorDetail(BaseModel):
    code: str  # エラーコード（例: "INVALID_SQL"）
    message: str  # ユーザー向けメッセージ
    detail: Optional[str] = None  # 技術的な詳細
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "SQL_SYNTAX_ERROR",
                    "message": "SQL構文にエラーがあります",
                    "detail": "1行目: 'FORM' は 'FROM' の誤りです"
                }
            }
        }
```

## 拡張ポイント

### 将来追加可能な機能

1. **ユーザー管理**
   ```python
   context: {
       "user_id": "abc123",  # ユーザー別の進捗管理
       "session_id": "xyz789"  # セッション管理
   }
   ```

2. **詳細な制御**
   ```python
   context: {
       "max_execution_time": 3.0,  # SQL実行タイムアウト
       "result_limit": 50,  # 結果の最大行数
       "language": "ja"  # 多言語対応
   }
   ```

3. **学習履歴**
   ```python
   context: {
       "track_progress": true,  # 進捗を記録
       "adaptive_difficulty": true  # 自動難易度調整
   }
   ```

## セキュリティ考慮事項

- [ ] user_sqlフィールドは必ずSELECT文のみ許可
- [ ] promptフィールドの最大長制限（1000文字）
- [ ] contextの最大サイズ制限（10KB）
- [ ] problem_idの妥当性検証

## バリデーション

```python
from pydantic import validator

class UniversalRequest(BaseModel):
    prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if v and len(v) > 1000:
            raise ValueError('プロンプトは1000文字以内で入力してください')
        return v
    
    @validator('context')
    def validate_context(cls, v):
        if v and 'user_sql' in v:
            sql = v['user_sql'].strip().upper()
            if not sql.startswith('SELECT'):
                raise ValueError('SELECT文のみ実行可能です')
        return v
```

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |