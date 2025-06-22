# APIエンドポイント: POST /api/create-tables

## 基本情報
| 項目 | 内容 |
|-----|------|
| エンドポイント | /api/create-tables |
| HTTPメソッド | POST |
| 認証 | 不要（MVP版） |
| レート制限 | なし（MVP版） |
| タイムアウト | 30秒（テーブル作成に時間がかかるため） |

## 概要
学習用のデータベーステーブルとサンプルデータを作成します。
既存の学習用テーブルは全て削除され、新しいテーマでテーブルが再作成されます。

## リクエスト

### Headers
```http
Content-Type: application/json
```

### Request Body
```json
{}
```

または

```json
{
  "prompt": "ECサイトのテーブルを作成してください"
}
```

**フィールド説明**:
| フィールド名 | 型 | 必須 | 説明 | 制約 |
|------------|---|-----|------|------|
| prompt | string | × | テーブル作成の指示（省略時はAIが自動選択） | 最大1000文字 |
| context | object | × | 将来の拡張用 | 最大10KB |

## レスポンス

### 成功時 (200 OK)
```json
{
  "success": true,
  "theme": "社員管理",
  "message": "社員管理システムのテーブルを3つ作成しました"
}
```

**フィールド説明**:
| フィールド名 | 型 | 説明 |
|------------|---|------|
| success | boolean | 処理成功フラグ |
| theme | string | AIが選択したテーマ |
| message | string | ユーザー向けメッセージ（省略可） |
| tables | array | 作成したテーブル名リスト（将来実装） |
| details | object | 詳細情報（将来実装） |

### エラー時

#### 500 Internal Server Error
```json
{
  "error": {
    "code": "TABLE_CREATION_ERROR",
    "message": "テーブルの作成に失敗しました",
    "detail": "データベース接続エラー"
  }
}
```

## 処理フロー
```
1. リクエスト受信
   └─ 入力値検証（promptの長さチェック）

2. 既存テーブルの削除
   ├─ publicスキーマの全テーブルを取得
   └─ CASCADE削除で依存関係も含めて削除

3. テーマの決定
   ├─ promptがある場合: AIに解釈させる
   └─ promptがない場合: AIがランダム選択
      - 社員管理
      - 図書館
      - ECサイト
      - 学校
      - 病院

4. テーブル構造の生成
   └─ AIにテーブル定義を生成させる
      - 3-5テーブル
      - 適切なリレーション
      - 現実的なカラム構成

5. テーブルとデータの作成
   ├─ CREATE TABLE文の実行
   ├─ 外部キー制約の設定
   └─ サンプルデータの投入（100-1000行）

6. セッション状態の更新
   └─ 現在のテーマを保存

7. レスポンス生成
```

## 実装例

### リクエスト例（curl）
```bash
# 最小構成
curl -X POST http://localhost:8000/api/create-tables \
  -H "Content-Type: application/json" \
  -d '{}'

# テーマ指定
curl -X POST http://localhost:8000/api/create-tables \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "オンライン書店のデータベースを作成して。在庫管理も含めて"
  }'
```

### 実装コード例（FastAPI）
```python
from fastapi import APIRouter, Depends
from app.schemas import UniversalRequest, CreateTablesResponse
from app.core.db import DatabaseManager
from app.api.generative import generate_table_schema

router = APIRouter()

@router.post("/api/create-tables", response_model=CreateTablesResponse)
async def create_tables(
    request: UniversalRequest,
    db: DatabaseManager = Depends(get_db)
):
    try:
        # 1. 既存テーブルを削除
        await db.drop_all_public_tables()
        
        # 2. テーマを決定
        theme = await determine_theme(request.prompt)
        
        # 3. テーブル構造を生成
        schema = await generate_table_schema(theme)
        
        # 4. テーブルを作成
        await db.create_tables_from_schema(schema)
        
        # 5. サンプルデータを投入
        await db.insert_sample_data(schema)
        
        # 6. セッション状態を更新
        await db.update_session_state("current_theme", theme)
        
        return CreateTablesResponse(
            success=True,
            theme=theme,
            message=f"{theme}のテーブルを作成しました"
        )
        
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "TABLE_CREATION_ERROR",
                    "message": "テーブルの作成に失敗しました",
                    "detail": str(e)
                }
            }
        )
```

## 依存関係
- 内部API: なし
- 外部サービス: LocalAI（テーブル構造生成）
- データベース: PostgreSQL（DDL実行権限必要）

## パフォーマンス要件
- 応答時間: 通常10-20秒（データ生成を含む）
- 最大実行時間: 30秒
- 同時実行: 1（テーブル削除・作成のため）

## セキュリティ考慮事項
- [x] publicスキーマのみ操作（システムテーブルは触らない）
- [x] DROP文はpublicスキーマに限定
- [x] SQL実行は管理者権限で実行
- [ ] 将来: API認証の実装

## 監視項目
- テーブル作成の成功率
- 平均実行時間
- テーマ別の利用頻度
- エラー発生率

## AIプロンプト設計

### テーマ決定プロンプト
```
ユーザーの指示: {prompt if prompt else "指定なし"}

上記の指示から、SQL学習に適したデータベーステーマを1つ選んでください。
指示がない場合は、以下からランダムに選択してください：
- 社員管理システム
- 図書館システム
- ECサイト
- 学校管理システム
- 病院管理システム

選択したテーマ名のみを返してください。
```

### テーブル構造生成プロンプト
```
{theme}のデータベースを設計してください。

要件：
1. 3-5個のテーブル
2. 適切な正規化
3. 外部キー制約でリレーションを表現
4. 現実的なカラム構成
5. 日本語のデータに対応

以下の形式でDDLを生成してください：
- CREATE TABLE文
- 外部キー制約
- 必要なインデックス
```

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |