# APIエンドポイント: [メソッド] [パス]

## 基本情報
| 項目 | 内容 |
|-----|------|
| エンドポイント | /api/xxx |
| HTTPメソッド | POST/GET/PUT/DELETE |
| 認証 | 必要/不要 |
| レート制限 | あり（n回/分）/なし |
| タイムアウト | n秒 |

## 概要
[このAPIの目的と機能を2-3文で説明]

## リクエスト

### Headers
```http
Content-Type: application/json
Authorization: Bearer {token}  # 認証が必要な場合
```

### Path Parameters
| パラメータ名 | 型 | 必須 | 説明 |
|------------|---|-----|------|
| id | string | ○ | リソースID |

### Query Parameters  
| パラメータ名 | 型 | 必須 | デフォルト | 説明 |
|------------|---|-----|----------|------|
| limit | integer | × | 10 | 取得件数 |
| offset | integer | × | 0 | オフセット |

### Request Body
```json
{
  "field1": "string",
  "field2": 123,
  "field3": {
    "nested": "value"
  }
}
```

**フィールド説明**:
| フィールド名 | 型 | 必須 | 説明 | 制約 |
|------------|---|-----|------|------|
| field1 | string | ○ | フィールドの説明 | 最大100文字 |
| field2 | integer | × | フィールドの説明 | 1-1000 |
| field3.nested | string | ○ | ネストしたフィールド | - |

## レスポンス

### 成功時 (200 OK)
```json
{
  "success": true,
  "data": {
    "id": "123",
    "result": "value"
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**フィールド説明**:
| フィールド名 | 型 | 説明 |
|------------|---|------|
| success | boolean | 処理成功フラグ |
| data | object | レスポンスデータ本体 |
| data.id | string | リソースID |
| data.result | string | 処理結果 |
| metadata.timestamp | string | 処理時刻（ISO 8601） |

### エラー時

#### 400 Bad Request
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "field1",
        "issue": "必須項目です"
      }
    ]
  }
}
```

#### 404 Not Found
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "指定されたリソースが見つかりません"
  }
}
```

#### 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "サーバーエラーが発生しました"
  }
}
```

## 処理フロー
```
1. リクエストの受信
   ├─ 認証チェック（必要な場合）
   └─ 入力値検証
2. ビジネスロジック実行
   ├─ データベース操作
   ├─ 外部API呼び出し
   └─ 結果の加工
3. レスポンス生成
   ├─ 正常系: データ整形して返却
   └─ 異常系: エラーレスポンス生成
```

## 実装例

### リクエスト例（curl）
```bash
curl -X POST https://api.example.com/api/xxx \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "test",
    "field2": 123
  }'
```

### 実装コード例（FastAPI）
```python
@router.post("/api/xxx")
async def endpoint_name(
    request: RequestModel,
    db: DatabaseManager = Depends(get_db)
) -> ResponseModel:
    # 実装
    pass
```

## 依存関係
- 内部API: [依存するAPI名]
- 外部サービス: [依存する外部サービス]
- データベース: [使用するテーブル]

## パフォーマンス要件
- 応答時間: 95%tile < 500ms
- 同時接続数: 最大100
- スループット: 1000req/sec

## セキュリティ考慮事項
- [ ] 認証・認可の実装
- [ ] 入力値のサニタイズ
- [ ] SQLインジェクション対策
- [ ] レート制限の実装
- [ ] ログに機密情報を含めない

## 監視項目
- レスポンスタイム
- エラー率
- リクエスト数
- 各HTTPステータスコードの割合

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| YYYY-MM-DD | 1.0.0 | 初版作成 | 作成者名 |