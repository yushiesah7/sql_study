"""
プロンプト生成機能
LLMに送信するプロンプトを生成する
"""

from typing import Optional, List, Dict, Any
import json


class PromptGenerator:
    """LLM用プロンプト生成クラス"""

    @staticmethod
    def create_table_generation_prompt(
        user_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        テーブル作成用プロンプトを生成

        Args:
            user_prompt: ユーザーからの指示（オプション）

        Returns:
            LLMに送信するメッセージリスト
        """
        system_message = """あなたはSQL学習アプリのためのテーブル設計アシスタントです。
        
**目的**: 学習者がSQLの練習をするためのテーブルとサンプルデータを作成してください。

**要件**:
1. 2-4個のテーブルを作成
2. テーブル間に適切なリレーション（外部キー）を設定
3. 各テーブルに10-50行程度のリアルなサンプルデータを挿入
4. 学習に適した現実的なシナリオを選択

**出力形式**:
```json
{
  "theme": "テーマ名（例：社員管理、図書館、ECサイト）",
  "description": "テーマの簡単な説明",
  "sql_statements": [
    "CREATE TABLE ...",
    "INSERT INTO ...",
    ...
  ]
}
```

**注意事項**:
- CREATE TABLE文とINSERT文のみ出力
- PostgreSQL互換のSQL構文を使用
- データは多様性を持たせ、JOIN、GROUP BY、集計関数の練習に適したもの
- 日本語のデータを含める（名前、住所等）
"""

        if user_prompt:
            user_message = (
                f"以下の指示に従ってテーブルを作成してください：\n{user_prompt}"
            )
        else:
            user_message = "学習に適したテーブルとサンプルデータを作成してください。テーマはランダムに選んでください。"

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    @staticmethod
    def create_problem_generation_prompt(
        table_schemas: List[Dict[str, Any]], user_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        問題生成用プロンプトを生成

        Args:
            table_schemas: テーブルスキーマ情報
            user_prompt: ユーザーからの指示（オプション）

        Returns:
            LLMに送信するメッセージリスト
        """
        # テーブル情報を整理
        schema_info = PromptGenerator._format_table_schemas(table_schemas)

        system_message = f"""あなたはSQL学習アプリの問題作成アシスタントです。

**目的**: 与えられたテーブル構造に基づいて、SQL学習問題を作成してください。

**現在のテーブル構造**:
{schema_info}

**要件**:
1. 学習者が結果を見てSQLを推測する「逆引き学習」形式
2. 適切な難易度（初級〜中級）
3. 実行結果は3-10行程度
4. JOIN、GROUP BY、集計関数を適度に含む

**出力形式**:
```json
{{
  "difficulty": "easy|medium|hard",
  "correct_sql": "実際のSELECT文",
  "expected_result": [
    {{"column1": "value1", "column2": "value2"}},
    ...
  ],
  "hint": "ヒント文（オプション）"
}}
```

**注意事項**:
- SELECT文のみ使用
- 結果は実際にデータベースで実行可能
- 列名は実際のテーブル構造と一致させる
- expected_resultは実際の実行結果と同じ形式
"""

        if user_prompt:
            user_message = f"以下の条件で問題を作成してください：\n{user_prompt}"
        else:
            user_message = "適切な難易度のSQL学習問題を作成してください。"

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    @staticmethod
    def create_answer_check_prompt(
        user_sql: str,
        user_result: List[Dict[str, Any]],
        expected_result: List[Dict[str, Any]],
        table_schemas: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        回答チェック用プロンプトを生成

        Args:
            user_sql: ユーザーが入力したSQL
            user_result: ユーザーSQLの実行結果
            expected_result: 期待される実行結果
            table_schemas: テーブルスキーマ情報

        Returns:
            LLMに送信するメッセージリスト
        """
        schema_info = PromptGenerator._format_table_schemas(table_schemas)

        system_message = f"""あなたはSQL学習アプリの採点アシスタントです。

**テーブル構造**:
{schema_info}

**採点基準**:
1. 実行結果が期待結果と完全一致するか
2. SQLの記述が適切か（効率性、可読性）
3. 学習者にとって有益なフィードバック

**出力形式**:
```json
{{
  "is_correct": true/false,
  "score": 0-100,
  "feedback": "詳細なフィードバック",
  "improvement_suggestions": ["改善提案1", "改善提案2"],
  "hint": "ヒント（間違っている場合）"
}}
```

**フィードバック指針**:
- 正解の場合：よい点を褒める
- 不正解の場合：何が間違っているか具体的に指摘
- 常に建設的で学習促進的な内容
- 日本語で回答
"""

        user_message = f"""
**学習者のSQL**:
```sql
{user_sql}
```

**学習者の実行結果**:
```json
{json.dumps(user_result, ensure_ascii=False, indent=2)}
```

**期待される結果**:
```json
{json.dumps(expected_result, ensure_ascii=False, indent=2)}
```

この学習者の回答を採点し、フィードバックを提供してください。
"""

        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    @staticmethod
    def _format_table_schemas(table_schemas: List[Dict[str, Any]]) -> str:
        """
        テーブルスキーマ情報を読みやすい形式にフォーマット

        Args:
            table_schemas: テーブルスキーマ情報

        Returns:
            フォーマット済みのスキーマ情報
        """
        if not table_schemas:
            return "（テーブル情報なし）"

        formatted_schemas = []
        for table in table_schemas:
            table_name = table.get("table_name", "unknown")
            columns = table.get("columns", [])

            column_info = []
            for col in columns:
                col_name = col.get("column_name", "unknown")
                data_type = col.get("data_type", "unknown")
                is_nullable = col.get("is_nullable", "YES")
                nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                column_info.append(f"  - {col_name}: {data_type} {nullable_str}")

            table_info = f"テーブル: {table_name}\n" + "\n".join(column_info)
            formatted_schemas.append(table_info)

        return "\n\n".join(formatted_schemas)
