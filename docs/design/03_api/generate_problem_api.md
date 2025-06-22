# APIエンドポイント: POST /api/generate-problem

## 基本情報
| 項目 | 内容 |
|-----|------|
| エンドポイント | /api/generate-problem |
| HTTPメソッド | POST |
| 認証 | 不要（MVP版） |
| レート制限 | なし（MVP版） |
| タイムアウト | 10秒 |

## 概要
現在のテーブル構造に基づいて、SQL学習用の問題を生成します。
AIがSQLを内部で実行し、その結果のみを返すことで、ユーザーは結果から逆算してSQLを考える学習方式を実現します。

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
  "prompt": "JOINを使った問題を出して"
}
```

**フィールド説明**:
| フィールド名 | 型 | 必須 | 説明 | 制約 |
|------------|---|-----|------|------|
| prompt | string | × | 問題の種類や難易度の指示 | 最大1000文字 |
| context | object | × | 将来の拡張用 | 最大10KB |

## レスポンス

### 成功時 (200 OK)
```json
{
  "problem_id": 42,
  "result": [
    {
      "name": "田中太郎",
      "department": "営業部",
      "salary": 350000
    },
    {
      "name": "佐藤花子",
      "department": "営業部", 
      "salary": 400000
    },
    {
      "name": "鈴木一郎",
      "department": "営業部",
      "salary": 320000
    }
  ],
  "row_count": 3,
  "column_names": ["name", "department", "salary"]
}
```

**フィールド説明**:
| フィールド名 | 型 | 説明 |
|------------|---|------|
| problem_id | integer | 問題の一意識別子（回答時に使用） |
| result | array | SQLの実行結果（配列of辞書） |
| row_count | integer | 結果の行数（省略可、resultから計算可能） |
| column_names | array | カラム名のリスト（省略可、resultから取得可能） |
| created_at | string | 問題作成時刻（ISO 8601形式）（将来実装） |
| difficulty | integer | 難易度（1-10）（将来実装） |
| category | string | カテゴリ（将来実装） |

### エラー時

#### 400 Bad Request
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
    "code": "PROBLEM_GENERATION_ERROR",
    "message": "問題の生成に失敗しました",
    "detail": "AI応答エラー"
  }
}
```

## 処理フロー
```
1. リクエスト受信
   └─ 入力値検証

2. 現在の状態確認
   ├─ テーブルの存在確認
   └─ 前回の問題情報取得（難易度調整用）

3. 難易度の自動調整
   ├─ 初回: 難易度1（簡単なSELECT）
   ├─ 正答率高: 難易度+1
   └─ 正答率低: 難易度維持

4. 問題SQLの生成
   └─ AIに現在のスキーマと要件を渡す
      - テーブル構造
      - 難易度レベル
      - ユーザーのprompt（あれば）
      - 結果が3-10行になる条件

5. SQLの実行と検証
   ├─ 生成されたSQLを実行
   ├─ 結果の行数確認（多すぎる場合は再生成）
   └─ エラーの場合は再試行（最大3回）

6. 問題の保存
   └─ app_system.problemsテーブルに保存
      - 正解SQL
      - 実行結果
      - 難易度
      - カテゴリ

7. レスポンス生成
   └─ 結果のみを返す（SQLは非公開）
```

## 実装例

### リクエスト例（curl）
```bash
# 最小構成（自動難易度調整）
curl -X POST http://localhost:8000/api/generate-problem \
  -H "Content-Type: application/json" \
  -d '{}'

# カテゴリ指定
curl -X POST http://localhost:8000/api/generate-problem \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "GROUP BYを使った集計問題"
  }'
```

### 実装コード例（FastAPI）
```python
@router.post("/api/generate-problem", response_model=GenerateProblemResponse)
async def generate_problem(
    request: UniversalRequest,
    db: DatabaseManager = Depends(get_db)
):
    # 1. テーブルの存在確認
    schemas = await db.get_table_schemas()
    if not schemas:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "NO_TABLES",
                    "message": "テーブルが作成されていません"
                }
            }
        )
    
    # 2. 難易度の決定
    difficulty = await calculate_difficulty(db)
    
    # 3. 問題SQLの生成
    problem_sql = await generate_problem_sql(
        schemas=schemas,
        difficulty=difficulty,
        user_prompt=request.prompt
    )
    
    # 4. SQLの実行
    try:
        result = await db.execute_select(problem_sql, timeout=5.0)
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        # 再生成を試みる
        problem_sql = await regenerate_simpler_sql(schemas, difficulty)
        result = await db.execute_select(problem_sql)
    
    # 5. 結果の検証
    if len(result) == 0:
        raise HTTPException(500, detail="問題生成に失敗しました（結果が空）")
    if len(result) > 100:
        result = result[:100]  # 最大100行に制限
    
    # 6. 問題の保存
    problem_id = await db.save_problem(
        sql=problem_sql,
        result=result,
        difficulty=difficulty
    )
    
    # 7. レスポンス生成
    column_names = list(result[0].keys()) if result else []
    
    return GenerateProblemResponse(
        problem_id=problem_id,
        result=result,
        row_count=len(result),
        column_names=column_names
    )
```

## 依存関係
- 内部API: なし
- 外部サービス: LocalAI（SQL生成）
- データベース: 現在のテーブル構造を参照

## パフォーマンス要件
- 応答時間: 通常2-5秒
- 最大実行時間: 10秒
- SQL実行タイムアウト: 5秒

## セキュリティ考慮事項
- [x] 生成されるSQLはSELECT文のみ
- [x] SQLは内部実行のみ（ユーザーに公開しない）
- [x] 実行結果のサイズ制限（最大100行）
- [x] タイムアウト設定でDoS攻撃を防止

## 監視項目
- 問題生成の成功率
- 平均難易度の推移
- カテゴリ別の生成頻度
- SQL実行時間の分布

## AIプロンプト設計

### 問題SQL生成プロンプト
```
現在のテーブル構造:
{schemas}

以下の条件でSQL学習用の問題となるSELECT文を生成してください：

難易度: {difficulty}/10
{user_prompt if user_prompt else ""}

要件：
1. 結果が3-10行になること
2. 実用的で意味のある問い合わせ
3. 現在の難易度に適した複雑さ

難易度の目安：
- 1-2: 単純なSELECT、WHERE
- 3-4: 複数条件、ORDER BY、LIMIT
- 5-6: JOIN（INNER JOIN）
- 7-8: 複数JOIN、集計関数、GROUP BY
- 9-10: サブクエリ、HAVING、ウィンドウ関数

生成するSQL文のみを返してください。説明は不要です。
```

### 難易度自動調整ロジック
```python
async def calculate_difficulty(db: DatabaseManager) -> int:
    # 最近の正答率を取得
    recent_results = await db.get_recent_results(limit=5)
    
    if not recent_results:
        return 1  # 初回は最も簡単
    
    correct_rate = sum(r.is_correct for r in recent_results) / len(recent_results)
    current_difficulty = recent_results[-1].difficulty
    
    if correct_rate > 0.8:
        return min(current_difficulty + 1, 10)
    elif correct_rate < 0.4:
        return max(current_difficulty - 1, 1)
    else:
        return current_difficulty
```

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |