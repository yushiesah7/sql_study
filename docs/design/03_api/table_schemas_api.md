# APIエンドポイント: GET /api/table-schemas

## 基本情報
| 項目 | 内容 |
|-----|------|
| エンドポイント | /api/table-schemas |
| HTTPメソッド | GET |
| 認証 | 不要（MVP版） |
| レート制限 | なし（MVP版） |
| タイムアウト | 5秒 |

## 概要
現在作成されているテーブルの構造（スキーマ）情報を取得します。
ユーザーがSQL作成時にテーブル構造を参照できるようにするためのAPIです。

## リクエスト

### Headers
```http
Content-Type: application/json
```

### Path Parameters
なし

### Query Parameters
なし

### Request Body
なし（GETメソッドのため）

## レスポンス

### 成功時 (200 OK)
```json
{
  "schemas": [
    {
      "table_name": "employees",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "nullable": false,
          "is_primary_key": true
        },
        {
          "name": "name",
          "type": "VARCHAR(100)",
          "nullable": false,
          "is_primary_key": false
        },
        {
          "name": "department_id",
          "type": "INTEGER",
          "nullable": true,
          "is_primary_key": false,
          "foreign_key": {
            "table": "departments",
            "column": "id"
          }
        },
        {
          "name": "salary",
          "type": "INTEGER",
          "nullable": false,
          "is_primary_key": false
        },
        {
          "name": "hire_date",
          "type": "DATE",
          "nullable": false,
          "is_primary_key": false
        }
      ]
    },
    {
      "table_name": "departments",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "nullable": false,
          "is_primary_key": true
        },
        {
          "name": "name",
          "type": "VARCHAR(50)",
          "nullable": false,
          "is_primary_key": false
        },
        {
          "name": "location",
          "type": "VARCHAR(100)",
          "nullable": true,
          "is_primary_key": false
        }
      ]
    }
  ],
  "theme": "社員管理",
  "table_count": 2
}
```

**フィールド説明**:
| フィールド名 | 型 | 説明 |
|------------|---|------|
| schemas | array | テーブル情報の配列 |
| schemas[].table_name | string | テーブル名 |
| schemas[].columns | array | カラム情報の配列 |
| schemas[].columns[].name | string | カラム名 |
| schemas[].columns[].type | string | データ型 |
| schemas[].columns[].nullable | boolean | NULL許可 |
| schemas[].columns[].is_primary_key | boolean | 主キーかどうか |
| schemas[].columns[].foreign_key | object | 外部キー情報（省略可） |
| schemas[].columns[].foreign_key.table | string | 参照先テーブル |
| schemas[].columns[].foreign_key.column | string | 参照先カラム |
| theme | string | 現在のテーマ（省略可） |
| table_count | integer | テーブル数（省略可） |

### エラー時

#### 404 Not Found
```json
{
  "error": {
    "code": "NO_TABLES",
    "message": "テーブルが作成されていません",
    "detail": "先に /api/create-tables を実行してください"
  }
}
```

#### 500 Internal Server Error
```json
{
  "error": {
    "code": "SCHEMA_FETCH_ERROR",
    "message": "テーブル情報の取得に失敗しました",
    "detail": "データベース接続エラー"
  }
}
```

## 処理フロー
```
1. リクエスト受信
   └─ 特に検証なし（GETのため）

2. データベース接続
   └─ 接続プールから取得

3. テーブル一覧の取得
   └─ information_schemaから取得
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'

4. 各テーブルのカラム情報取得
   └─ information_schema.columnsから取得
      - カラム名
      - データ型
      - NULL制約
      - デフォルト値

5. 制約情報の取得
   ├─ 主キー制約
   └─ 外部キー制約

6. セッション情報の取得
   └─ 現在のテーマ（あれば）

7. レスポンス生成
   └─ 取得した情報を整形
```

## 実装例

### リクエスト例（curl）
```bash
curl -X GET http://localhost:8000/api/table-schemas \
  -H "Content-Type: application/json"
```

### 実装コード例（FastAPI）
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

router = APIRouter()

@router.get("/api/table-schemas")
async def get_table_schemas(
    db: DatabaseManager = Depends(get_db)
) -> Dict[str, Any]:
    try:
        # 1. publicスキーマのテーブル一覧を取得
        tables = await db.get_public_tables()
        
        if not tables:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NO_TABLES",
                        "message": "テーブルが作成されていません",
                        "detail": "先に /api/create-tables を実行してください"
                    }
                }
            )
        
        # 2. 各テーブルの詳細情報を取得
        schemas = []
        for table_name in tables:
            columns = await db.get_table_columns(table_name)
            constraints = await db.get_table_constraints(table_name)
            
            # カラム情報を整形
            column_info = []
            for col in columns:
                col_dict = {
                    "name": col["column_name"],
                    "type": col["data_type"].upper(),
                    "nullable": col["is_nullable"] == "YES",
                    "is_primary_key": col["column_name"] in constraints["primary_keys"]
                }
                
                # 外部キー情報があれば追加
                if col["column_name"] in constraints["foreign_keys"]:
                    fk_info = constraints["foreign_keys"][col["column_name"]]
                    col_dict["foreign_key"] = {
                        "table": fk_info["referenced_table"],
                        "column": fk_info["referenced_column"]
                    }
                
                column_info.append(col_dict)
            
            schemas.append({
                "table_name": table_name,
                "columns": column_info
            })
        
        # 3. セッション情報を取得
        theme = await db.get_session_value("current_theme")
        
        # 4. レスポンス生成
        return {
            "schemas": schemas,
            "theme": theme,
            "table_count": len(schemas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch schemas: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SCHEMA_FETCH_ERROR",
                    "message": "テーブル情報の取得に失敗しました",
                    "detail": str(e)
                }
            }
        )

# DatabaseManagerの実装例
class DatabaseManager:
    async def get_public_tables(self) -> List[str]:
        """publicスキーマのテーブル一覧を取得"""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        result = await self.fetch(query)
        return [row["table_name"] for row in result]
    
    async def get_table_columns(self, table_name: str) -> List[Dict]:
        """テーブルのカラム情報を取得"""
        query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
              AND table_name = $1
            ORDER BY ordinal_position;
        """
        result = await self.fetch(query, table_name)
        
        # データ型を整形（例: character varying(100) → VARCHAR(100)）
        for row in result:
            if row["character_maximum_length"]:
                if row["data_type"] == "character varying":
                    row["data_type"] = f"VARCHAR({row['character_maximum_length']})"
                elif row["data_type"] == "character":
                    row["data_type"] = f"CHAR({row['character_maximum_length']})"
        
        return result
    
    async def get_table_constraints(self, table_name: str) -> Dict:
        """テーブルの制約情報を取得"""
        # 主キー取得
        pk_query = """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = 'public'
              AND table_name = $1
              AND constraint_name = (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                  AND table_name = $1
                  AND constraint_type = 'PRIMARY KEY'
              );
        """
        pk_result = await self.fetch(pk_query, table_name)
        primary_keys = [row["column_name"] for row in pk_result]
        
        # 外部キー取得
        fk_query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.constraint_column_usage ccu
                ON kcu.constraint_name = ccu.constraint_name
            WHERE kcu.table_schema = 'public'
              AND kcu.table_name = $1
              AND kcu.constraint_name IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                  AND table_name = $1
                  AND constraint_type = 'FOREIGN KEY'
              );
        """
        fk_result = await self.fetch(fk_query, table_name)
        foreign_keys = {
            row["column_name"]: {
                "referenced_table": row["referenced_table"],
                "referenced_column": row["referenced_column"]
            }
            for row in fk_result
        }
        
        return {
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys
        }
```

## 依存関係
- 内部API: なし
- 外部サービス: なし
- データベース: information_schemaへの読み取りアクセス

## パフォーマンス要件
- 応答時間: 通常1秒以内
- キャッシュ: 可能（テーブル構造は頻繁に変わらない）

## セキュリティ考慮事項
- [x] publicスキーマのみ表示（システムテーブルは非表示）
- [x] 読み取り専用操作
- [x] 機密情報を含まない

## 監視項目
- API呼び出し頻度
- 平均応答時間
- エラー率

## UI表示例

フロントエンドでの表示イメージ：

```
【テーブル構造】
■ employees
  - id (INTEGER) [PK]
  - name (VARCHAR(100)) NOT NULL
  - department_id (INTEGER) → departments.id
  - salary (INTEGER) NOT NULL
  - hire_date (DATE) NOT NULL

■ departments  
  - id (INTEGER) [PK]
  - name (VARCHAR(50)) NOT NULL
  - location (VARCHAR(100))
```

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |