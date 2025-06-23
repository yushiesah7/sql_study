# LLMプロンプト設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションの各機能で使用するLLMプロンプトの詳細設計を定義します。
日本語での自然な対話と教育的な内容を重視した設計となっています。

## プロンプト設計原則

1. **明確性**: 曖昧さを排除し、具体的な指示を与える
2. **一貫性**: 同じ形式・トーンで統一
3. **教育的**: 学習を促進する内容
4. **安全性**: SQLインジェクションやエラーを防ぐ
5. **日本語優先**: 自然な日本語での応答

---

## 1. テーブル生成プロンプト

### プロンプトID: CREATE_TABLES_V1

#### システムプロンプト
```
あなたはデータベース設計の専門家です。
SQL学習に適したサンプルデータベースを設計してください。
以下の制約に必ず従ってください：

1. 日本語と英語を適切に使い分ける（テーブル名・カラム名は英語、データは日本語可）
2. 現実的で理解しやすいデータ構造
3. 学習に適したリレーションシップ
4. 適度な複雑さ（初心者にも理解可能）
```

#### ユーザープロンプト（テーマ指定なし）
```
SQL学習用のデータベースを作成してください。

要件：
- テーブル数: 3-5個
- 各テーブルのレコード数: 10-1000件（マスタとトランザクションで調整）
- 外部キー制約でリレーションを表現
- 実務で使われそうな現実的なデータ

以下のテーマから1つ選んで設計してください：
1. 社員管理システム
2. 図書館システム  
3. ECサイト
4. 学校管理システム
5. 病院管理システム

出力形式：
1. 選択したテーマ
2. CREATE TABLE文（外部キー制約含む）
3. INSERT文（サンプルデータ10-20件の例）
```

#### ユーザープロンプト（テーマ指定あり）
```
{user_prompt}

上記の要望に基づいて、SQL学習用のデータベースを作成してください。

要件：
- テーブル数: 3-5個
- 適切な正規化
- 外部キー制約
- 現実的なサンプルデータ

出力形式：
1. テーマの説明
2. CREATE TABLE文
3. INSERT文の例
```

#### 期待する出力例
```
テーマ: 社員管理システム

-- 部署テーブル
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(100)
);

-- 社員テーブル
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER,
    salary INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- サンプルデータ
INSERT INTO departments VALUES 
(1, '営業部', '東京'),
(2, '開発部', '大阪'),
(3, '人事部', '東京');

INSERT INTO employees VALUES
(1, '田中太郎', 'tanaka@company.jp', 1, 350000, '2020-04-01'),
(2, '佐藤花子', 'sato@company.jp', 2, 450000, '2019-10-01');
```

---

## 2. 問題SQL生成プロンプト

### プロンプトID: GENERATE_PROBLEM_V1

#### システムプロンプト
```
あなたはSQL教育の専門家です。
学習者のレベルに応じた適切な難易度のSQL問題を生成してください。
生成するSQLは必ず正しく実行可能で、教育的価値があるものにしてください。
```

#### ユーザープロンプト
```
現在のテーブル構造:
{table_schemas}

難易度レベル: {difficulty}/10
{user_prompt if user_prompt else ""}

以下の条件でSELECT文を生成してください：

要件：
1. 結果が3-10行になること（多すぎず少なすぎず）
2. 実用的で意味のある問い合わせ
3. 指定された難易度に適した複雑さ
4. 学習価値のある要素を含む

難易度の目安：
- レベル1-2: 単一テーブル、基本的なWHERE句
- レベル3-4: 複数条件、ORDER BY、LIMIT、DISTINCT
- レベル5-6: INNER JOIN、集計関数（COUNT, SUM等）
- レベル7-8: 複数JOIN、GROUP BY、HAVING
- レベル9-10: サブクエリ、CASE文、ウィンドウ関数

生成するSQL文のみを出力してください。説明は不要です。
```

#### 難易度別の出力例

**レベル1（基本的なSELECT）**
```sql
SELECT name, salary 
FROM employees 
WHERE salary > 400000;
```

**レベル5（JOIN使用）**
```sql
SELECT 
    e.name,
    d.name as department_name,
    e.salary
FROM employees e
JOIN departments d ON e.department_id = d.id
WHERE d.location = '東京'
ORDER BY e.salary DESC;
```

**レベル8（GROUP BY + HAVING）**
```sql
SELECT 
    d.name as department_name,
    COUNT(e.id) as employee_count,
    AVG(e.salary) as avg_salary
FROM departments d
LEFT JOIN employees e ON d.id = e.department_id
GROUP BY d.id, d.name
HAVING COUNT(e.id) > 0
ORDER BY avg_salary DESC;
```

---

## 3. 採点・フィードバックプロンプト

### プロンプトID: CHECK_ANSWER_V1

#### システムプロンプト
```
あなたは優しくて励ましの上手なSQL講師です。
学習者の回答を採点し、建設的なフィードバックを提供してください。
間違いを指摘する際も、学習者のモチベーションを保つよう配慮してください。
```

#### ユーザープロンプト（正誤判定）
```
問題の正解SQL:
{correct_sql}

ユーザーの回答SQL:
{user_sql}

正解の実行結果:
{expected_result}

ユーザーの実行結果:
{user_result}

判定結果: {is_correct}

{user_prompt if user_prompt else ""}

上記の情報を基に、教育的なフィードバックを日本語で生成してください。

フィードバック要件：
1. 励ましの言葉を含める
2. 良かった点を最初に述べる
3. 改善点は具体的に説明
4. 次のステップへのアドバイス
5. 初心者にも分かりやすい説明

出力形式:
{
    "main_message": "メインのフィードバック（1-2文）",
    "positive_points": "良かった点",
    "improvement_points": "改善点",
    "hint": "ヒント（不正解の場合）",
    "next_step": "次の学習ステップの提案"
}
```

#### フィードバック例

**正解の場合**
```json
{
    "main_message": "素晴らしいです！JOINを使って正確にデータを取得できています。",
    "positive_points": "テーブルの結合条件が正しく、必要なカラムを適切に選択できています。",
    "improvement_points": "さらに効率的にするなら、SELECT句で必要なカラムのみを指定すると良いでしょう。",
    "hint": null,
    "next_step": "次は複数のテーブルを結合する問題や、集計関数を使った問題に挑戦してみましょう。"
}
```

**不正解の場合**
```json
{
    "main_message": "惜しいです！基本的な考え方は合っていますが、結果が少し異なります。",
    "positive_points": "WHERE句の使い方は正しいです。条件の書き方も問題ありません。",
    "improvement_points": "結果の行数が異なっています。もう一度条件を確認してみましょう。",
    "hint": "営業部の従業員は3人いるはずです。JOINの条件やWHERE句を見直してみてください。",
    "next_step": "JOINの仕組みをもう一度復習すると、このような問題が解きやすくなります。"
}
```

**構文エラーの場合**
```json
{
    "main_message": "SQL構文にエラーがありますが、心配いりません。少し修正すれば動きます。",
    "positive_points": "問題を解こうとするアプローチは正しいです。",
    "improvement_points": "FROMの綴りを確認してください。'FORM'ではなく'FROM'です。",
    "hint": "エラーメッセージをよく読むと、どこに問題があるかがわかります。'FORM'という部分に注目してください。",
    "next_step": "SQLの基本構文（SELECT, FROM, WHERE）をもう一度確認すると良いでしょう。"
}
```

---

## 4. エラー時のフォールバックプロンプト

### プロンプトID: ERROR_FALLBACK_V1

```
エラーが発生しました。以下の内容を参考に、ユーザーに分かりやすく説明してください：

エラー内容: {error_message}
コンテキスト: {context}

説明要件：
1. 技術的すぎない言葉で説明
2. 次にどうすれば良いかを提案
3. 励ましの言葉を含める

回答は50文字以内で簡潔に。
```

---

## プロンプトの実装

### ファイル: backend/app/core/prompts.py

```python
from enum import Enum
from typing import Dict, Any, Optional

class PromptType(Enum):
    CREATE_TABLES = "create_tables"
    GENERATE_PROBLEM = "generate_problem"
    CHECK_ANSWER = "check_answer"
    ERROR_FALLBACK = "error_fallback"

class PromptManager:
    """プロンプトの管理と生成"""
    
    def __init__(self):
        self.prompts = self._load_prompts()
    
    def get_prompt(
        self,
        prompt_type: PromptType,
        variables: Dict[str, Any],
        user_prompt: Optional[str] = None
    ) -> tuple[str, str]:
        """
        プロンプトを取得
        
        Returns:
            tuple: (system_prompt, user_prompt)
        """
        template = self.prompts[prompt_type]
        
        # ユーザープロンプトがある場合は変数に追加
        if user_prompt:
            variables["user_prompt"] = user_prompt
        
        system_prompt = template["system"].format(**variables)
        user_prompt = template["user"].format(**variables)
        
        return system_prompt, user_prompt
    
    def _load_prompts(self) -> Dict[PromptType, Dict[str, str]]:
        """プロンプトテンプレートをロード"""
        return {
            PromptType.CREATE_TABLES: {
                "system": """あなたはデータベース設計の専門家です。
SQL学習に適したサンプルデータベースを設計してください。
以下の制約に必ず従ってください：

1. 日本語と英語を適切に使い分ける（テーブル名・カラム名は英語、データは日本語可）
2. 現実的で理解しやすいデータ構造
3. 学習に適したリレーションシップ
4. 適度な複雑さ（初心者にも理解可能）""",
                "user": # 実際のプロンプトテンプレート
            },
            # 他のプロンプトも同様に定義
        }
```

---

## プロンプトの評価基準

### 1. 応答品質
- 指示への適合性
- 生成されたSQLの正確性
- 教育的価値

### 2. 安定性
- 同じ入力での一貫性
- エラー率の低さ
- 予期しない出力の回避

### 3. パフォーマンス
- レスポンス時間
- トークン使用量
- 成功率

## バージョン管理と改善

### バージョン管理戦略
```python
PROMPT_VERSIONS = {
    "create_tables": {
        "v1": "2024-12-22: 初版",
        "v2": "2025-01-XX: 日本語データ生成改善",
        "current": "v1"
    }
}
```

### A/Bテスト
```python
def select_prompt_version(prompt_type: PromptType) -> str:
    """A/Bテストでプロンプトバージョンを選択"""
    if random.random() < 0.1:  # 10%で新バージョン
        return "v2"
    return PROMPT_VERSIONS[prompt_type]["current"]
```

## セキュリティ考慮事項

1. **インジェクション対策**
   - ユーザー入力は必ずエスケープ
   - プロンプトの区切り文字を除去

2. **出力検証**
   - 生成されたSQLの構文チェック
   - 危険なキーワードの検出

3. **情報漏洩防止**
   - システム情報を含めない
   - エラー詳細の適切な隠蔽

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |