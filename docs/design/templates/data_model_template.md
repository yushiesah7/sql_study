# データモデル設計書: [モデル名]

## 概要
[このデータモデルの目的と役割を2-3文で説明]

## モデル定義

### Pydanticモデル: `ModelName`

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class ModelName(BaseModel):
    """モデルの説明"""
    
    # 必須フィールド
    field1: str = Field(..., description="フィールドの説明")
    field2: int = Field(..., ge=1, le=100, description="1-100の整数")
    
    # オプションフィールド
    field3: Optional[str] = Field(None, max_length=255)
    field4: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 自動設定フィールド
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        # Pydantic設定
        json_schema_extra = {
            "example": {
                "field1": "example value",
                "field2": 42,
                "field3": "optional value"
            }
        }
```

## フィールド仕様

| フィールド名 | 型 | 必須 | デフォルト | 説明 | 制約 |
|------------|---|------|-----------|------|------|
| field1 | str | ○ | - | フィールドの詳細説明 | - |
| field2 | int | ○ | - | 数値フィールド | 1 ≤ n ≤ 100 |
| field3 | str | × | None | オプション文字列 | 最大255文字 |
| field4 | List[Dict] | × | [] | 配列フィールド | - |
| created_at | datetime | × | 現在時刻 | 作成日時 | ISO 8601形式 |

## バリデーション

### フィールドレベル検証
```python
@validator('field1')
def validate_field1(cls, v):
    if not v or v.strip() == '':
        raise ValueError('field1は空にできません')
    return v.strip()
```

### モデルレベル検証
```python
@root_validator
def validate_model(cls, values):
    # 複数フィールドにまたがる検証
    if values.get('field2') > 50 and not values.get('field3'):
        raise ValueError('field2が50を超える場合、field3は必須です')
    return values
```

## 使用例

### インスタンス作成
```python
# 正常な例
model = ModelName(
    field1="test",
    field2=42,
    field3="optional"
)

# 最小構成
model = ModelName(
    field1="test",
    field2=1
)
```

### JSON変換
```python
# モデル → JSON
json_data = model.model_dump_json()

# JSON → モデル
model = ModelName.model_validate_json(json_string)

# 辞書 → モデル  
model = ModelName(**dict_data)
```

## 関連モデル

| モデル名 | 関係 | 説明 |
|---------|------|------|
| RelatedModel1 | 1:N | このモデルが参照される |
| RelatedModel2 | N:1 | このモデルから参照する |

## データベーステーブルマッピング

| DBカラム名 | 型 | Pydanticフィールド | 備考 |
|-----------|---|-------------------|------|
| id | SERIAL | - | 自動生成 |
| field_1 | VARCHAR(255) | field1 | NOT NULL |
| field_2 | INTEGER | field2 | CHECK (1-100) |
| field_3 | TEXT | field3 | NULL可 |
| created_at | TIMESTAMP | created_at | DEFAULT NOW() |

## エラーレスポンス

バリデーションエラー時の形式:
```json
{
  "detail": [
    {
      "loc": ["field1"],
      "msg": "field1は空にできません",
      "type": "value_error"
    }
  ]
}
```

## 拡張性考慮事項
- [ ] 将来的なフィールド追加に備えた設計
- [ ] バージョニング戦略
- [ ] 後方互換性の維持方法

## セキュリティ考慮事項  
- [ ] 機密情報のマスキング
- [ ] 入力値のサニタイズ
- [ ] 最大サイズ制限

## パフォーマンス考慮事項
- [ ] 大量データ時のページネーション
- [ ] 不要なフィールドの除外（response_model_exclude）
- [ ] キャッシュ戦略

## テスト観点
- [ ] 正常系: 全フィールド指定
- [ ] 正常系: 必須フィールドのみ
- [ ] 異常系: 必須フィールド欠落
- [ ] 異常系: 型不一致
- [ ] 異常系: 制約違反
- [ ] 境界値テスト

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| YYYY-MM-DD | 1.0.0 | 初版作成 | 作成者名 |