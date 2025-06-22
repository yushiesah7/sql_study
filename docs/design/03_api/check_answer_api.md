# APIエンドポイント: POST /api/check-answer

## 基本情報
| 項目 | 内容 |
|-----|------|
| エンドポイント | /api/check-answer |
| HTTPメソッド | POST |
| 認証 | 不要（MVP版） |
| レート制限 | なし（MVP版） |
| タイムアウト | 10秒 |

## 概要
ユーザーが入力したSQLを実行し、問題の正解と比較して採点します。
正誤判定だけでなく、AIによる適切なフィードバックとアドバイスを提供します。

## リクエスト

### Headers
```http
Content-Type: application/json
```

### Request Body
```json
{
  "context": {
    "problem_id": 42,
    "user_sql": "SELECT e.name, d.name as department, e.salary FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = '営業部'"
  }
}
```

または（フィードバック方法を指定）

```json
{
  "prompt": "初心者向けに詳しく説明して",
  "context": {
    "problem_id": 42,
    "user_sql": "SELECT * FROM employees"
  }
}
```

**フィールド説明**:
| フィールド名 | 型 | 必須 | 説明 | 制約 |
|------------|---|-----|------|------|
| prompt | string | × | フィードバックの方法を指示 | 最大1000文字 |
| context | object | ○ | 必須情報を含むオブジェクト | - |
| context.problem_id | integer | ○ | 問題ID | 1以上の整数 |
| context.user_sql | string | ○ | ユーザーが入力したSQL | SELECT文のみ |

## レスポンス

### 成功時 (200 OK) - 正解の場合
```json
{
  "is_correct": true,
  "message": "正解です！JOINを使った良い解答です。別解として、サブクエリを使う方法もあります。"
}
```

### 成功時 (200 OK) - 不正解の場合
```json
{
  "is_correct": false,
  "message": "惜しいです！結果の行数が異なります。WHERE句の条件を確認してみましょう。",
  "user_result": [
    {"name": "田中太郎", "salary": 350000},
    {"name": "佐藤花子", "salary": 400000}
  ],
  "expected_result": [
    {"name": "田中太郎", "department": "営業部", "salary": 350000},
    {"name": "佐藤花子", "department": "営業部", "salary": 400000},
    {"name": "鈴木一郎", "department": "営業部", "salary": 320000}
  ],
  "hint": "departmentカラムも選択する必要があります。また、営業部の従業員は3人います。"
}
```

### 成功時 (200 OK) - SQLエラーの場合
```json
{
  "is_correct": false,
  "message": "SQL構文にエラーがあります。",
  "error_type": "syntax",
  "error_message": "column \"dept\" does not exist",
  "hint": "テーブル名は 'departments' です。'dept' というテーブルは存在しません。"
}
```

**フィールド説明**:
| フィールド名 | 型 | 説明 |
|------------|---|------|
| is_correct | boolean | 正誤判定 |
| message | string | AIが生成したメインフィードバック |
| user_result | array | ユーザーのSQL実行結果（不正解時、省略可） |
| expected_result | array | 期待される結果（不正解時、省略可） |
| advice | string | 改善のアドバイス（省略可） |
| hint | string | ヒント（不正解時、省略可） |
| alternative_solutions | array | 別解のSQL（将来実装） |
| error_type | string | エラーの種類（syntax/logic/timeout） |
| error_message | string | エラーメッセージ |

### エラー時

#### 400 Bad Request
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "SELECT文のみ実行可能です",
    "detail": "UPDATE文は実行できません"
  }
}
```

#### 404 Not Found
```json
{
  "error": {
    "code": "PROBLEM_NOT_FOUND",
    "message": "指定された問題が見つかりません",
    "detail": "problem_id: 999"
  }
}
```

## 処理フロー
```
1. リクエスト検証
   ├─ problem_idの存在確認
   └─ user_sqlの検証
      - SELECT文であることを確認
      - 危険なキーワードのチェック

2. 問題情報の取得
   └─ app_system.problemsから正解SQLと結果を取得

3. ユーザーSQLの実行
   ├─ タイムアウト設定（5秒）
   ├─ 実行エラーのハンドリング
   └─ 結果の取得（最大100行）

4. 結果の比較
   ├─ 完全一致: 正解
   ├─ カラム順序のみ違い: 正解（警告付き）
   ├─ データが異なる: 不正解
   └─ エラー: 不正解（エラー情報付き）

5. フィードバック生成
   └─ AIに以下を渡してフィードバックを生成
      - 正誤判定
      - ユーザーSQL
      - 正解SQL（参考用）
      - 実行結果の差分
      - ユーザーのprompt（あれば）

6. 学習履歴の記録
   └─ 今後の難易度調整のため（将来実装）

7. レスポンス生成
```

## 実装例

### リクエスト例（curl）
```bash
# 基本的な回答チェック
curl -X POST http://localhost:8000/api/check-answer \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "problem_id": 42,
      "user_sql": "SELECT name, department, salary FROM employees WHERE department = '\''営業部'\''"
    }
  }'

# 詳しい説明を要求
curl -X POST http://localhost:8000/api/check-answer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "なぜ間違っているか初心者にもわかるように説明して",
    "context": {
      "problem_id": 42,
      "user_sql": "SELECT * FROM employees"
    }
  }'
```

### 実装コード例（FastAPI）
```python
@router.post("/api/check-answer", response_model=CheckAnswerResponse)
async def check_answer(
    request: UniversalRequest,
    db: DatabaseManager = Depends(get_db)
):
    # 1. リクエスト検証
    if not request.context or "problem_id" not in request.context:
        raise HTTPException(400, detail="problem_idが必要です")
    
    if "user_sql" not in request.context:
        raise HTTPException(400, detail="user_sqlが必要です")
    
    problem_id = request.context["problem_id"]
    user_sql = request.context["user_sql"].strip()
    
    # SQLの検証
    if not validate_select_only(user_sql):
        raise HTTPException(
            400,
            detail={
                "error": {
                    "code": "INVALID_SQL",
                    "message": "SELECT文のみ実行可能です"
                }
            }
        )
    
    # 2. 問題情報の取得
    problem = await db.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            404,
            detail={
                "error": {
                    "code": "PROBLEM_NOT_FOUND",
                    "message": "指定された問題が見つかりません"
                }
            }
        )
    
    # 3. ユーザーSQLの実行
    try:
        user_result = await db.execute_select(user_sql, timeout=5.0)
    except asyncpg.PostgresSyntaxError as e:
        # 構文エラー
        return CheckAnswerResponse(
            is_correct=False,
            message="SQL構文にエラーがあります。",
            error_type="syntax",
            error_message=str(e),
            hint=await generate_syntax_hint(str(e), user_sql)
        )
    except Exception as e:
        # その他のエラー
        return CheckAnswerResponse(
            is_correct=False,
            message="SQLの実行中にエラーが発生しました。",
            error_type="execution",
            error_message=str(e)
        )
    
    # 4. 結果の比較
    expected_result = problem.result_json
    is_correct = compare_results(user_result, expected_result)
    
    # 5. フィードバック生成
    feedback = await generate_feedback(
        is_correct=is_correct,
        user_sql=user_sql,
        correct_sql=problem.correct_sql,
        user_result=user_result,
        expected_result=expected_result,
        user_prompt=request.prompt
    )
    
    # 6. レスポンス生成
    response = CheckAnswerResponse(
        is_correct=is_correct,
        message=feedback.main_message
    )
    
    if not is_correct:
        response.hint = feedback.hint
        if should_show_results(user_result, expected_result):
            response.user_result = user_result[:10]  # 最大10行
            response.expected_result = expected_result[:10]
    
    return response

def validate_select_only(sql: str) -> bool:
    """SELECT文のみを許可する検証"""
    sql_upper = sql.upper().strip()
    
    # 禁止キーワードチェック
    forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER']
    for keyword in forbidden:
        if keyword in sql_upper:
            return False
    
    # SELECT文で始まることを確認
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
        return False
    
    return True

def compare_results(result1: List[Dict], result2: List[Dict]) -> bool:
    """結果の比較（カラム順序は無視）"""
    if len(result1) != len(result2):
        return False
    
    # 各行を比較（順序も重要）
    for r1, r2 in zip(result1, result2):
        if set(r1.keys()) != set(r2.keys()):
            return False
        for key in r1.keys():
            if r1[key] != r2[key]:
                return False
    
    return True
```

## 依存関係
- 内部API: なし
- 外部サービス: LocalAI（フィードバック生成）
- データベース: 問題情報の参照、SQL実行

## パフォーマンス要件
- 応答時間: 通常2-5秒
- SQL実行タイムアウト: 5秒
- 最大結果行数: 100行（比較用）

## セキュリティ考慮事項
- [x] SELECT文のみ実行許可（厳格な検証）
- [x] SQLインジェクション対策（パラメータ化クエリ）
- [x] 実行時間制限（DoS攻撃防止）
- [x] エラーメッセージから内部情報を隠蔽

## 監視項目
- 正答率
- エラー種別の分布
- 平均応答時間
- よくある間違いパターン

## AIプロンプト設計

### フィードバック生成プロンプト
```
ユーザーのSQL: {user_sql}
正解SQL: {correct_sql}
判定: {is_correct}

ユーザーの結果:
{user_result}

期待される結果:
{expected_result}

{user_prompt if user_prompt else ""}

上記の情報を元に、教育的なフィードバックを日本語で生成してください。

要件：
1. 励ましの言葉を含める
2. 具体的な改善点を指摘
3. 理解を深めるための説明
4. 初心者にも分かりやすく

以下の形式で返してください：
- main_message: メインのフィードバック（1-2文）
- hint: ヒント（不正解の場合のみ）
- explanation: 詳しい説明（オプション）
```

## 変更履歴
| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |