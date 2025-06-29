"""
LLM統合サービス
LLMクライアントとプロンプト生成を組み合わせた高レベルサービス
"""

import json
import logging
from typing import Any

from app.core.error_codes import LLM_GENERATION_FAILED, LLM_INVALID_RESPONSE
from app.core.exceptions import LLMError
from app.core.llm_client import LLMClient
from app.services.prompt_generator import PromptGenerator

logger = logging.getLogger(__name__)


class LLMService:
    """LLM統合サービスクラス"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.prompt_generator = PromptGenerator()

    async def generate_tables(self, user_prompt: str | None = None) -> dict[str, Any]:
        """
        テーブル作成SQL生成

        Args:
            user_prompt: ユーザーからの指示

        Returns:
            テーブル作成情報
            {
                "theme": str,
                "description": str,
                "sql_statements": List[str]
            }
        """
        try:
            # プロンプト生成
            messages = self.prompt_generator.create_table_generation_prompt(user_prompt)

            # LLM呼び出し
            response = await self.llm_client.chat_completion(messages)
            content = self.llm_client.extract_content(response)

            # JSON解析
            result = self._parse_json_response(content)

            # 結果検証
            self._validate_table_generation_result(result)

            # SQL文の後処理（末尾のカンマを削除）
            sql_statements = result.get("sql_statements", [])
            cleaned_statements = []
            for sql in sql_statements:
                # 末尾の余分なカンマを削除
                sql = sql.strip()
                if sql.endswith(","):
                    sql = sql[:-1]
                cleaned_statements.append(sql)
            
            result["sql_statements"] = cleaned_statements

            # デバッグ: 生成されたSQL文をログ出力
            logger.info(f"Generated SQL statements: {cleaned_statements}")

            logger.info(f"Generated tables for theme: {result.get('theme', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"Table generation failed: {e}")
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                message="テーブル生成に失敗しました",
                error_code=LLM_GENERATION_FAILED,
                detail=str(e),
            ) from None

    async def generate_problem(
        self, table_schemas: list[dict[str, Any]], user_prompt: str | None = None
    ) -> dict[str, Any]:
        """
        問題生成

        Args:
            table_schemas: テーブルスキーマ情報
            user_prompt: ユーザーからの指示

        Returns:
            問題情報
            {
                "difficulty": str,
                "correct_sql": str,
                "expected_result": List[Dict],
                "hint": Optional[str]
            }
        """
        try:
            # プロンプト生成
            messages = self.prompt_generator.create_problem_generation_prompt(
                table_schemas, user_prompt
            )

            # LLM呼び出し
            response = await self.llm_client.chat_completion(messages)
            content = self.llm_client.extract_content(response)

            # JSON解析
            result = self._parse_json_response(content)

            # 結果検証
            self._validate_problem_generation_result(result)

            logger.info(
                f"Generated problem with difficulty: "
                f"{result.get('difficulty', 'Unknown')}"
            )
            return result

        except Exception as e:
            logger.error(f"Problem generation failed: {e}")
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                message="問題生成に失敗しました",
                error_code=LLM_GENERATION_FAILED,
                detail=str(e),
            ) from None

    async def check_answer(
        self,
        user_sql: str,
        user_result: list[dict[str, Any]],
        expected_result: list[dict[str, Any]],
        table_schemas: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        回答チェック

        Args:
            user_sql: ユーザーSQL
            user_result: ユーザーSQLの実行結果
            expected_result: 期待される結果
            table_schemas: テーブルスキーマ情報

        Returns:
            採点結果
            {
                "is_correct": bool,
                "score": int,
                "feedback": str,
                "improvement_suggestions": List[str],
                "hint": Optional[str]
            }
        """
        try:
            # プロンプト生成
            messages = self.prompt_generator.create_answer_check_prompt(
                user_sql, user_result, expected_result, table_schemas
            )

            # LLM呼び出し
            response = await self.llm_client.chat_completion(messages)
            content = self.llm_client.extract_content(response)

            # JSON解析
            result = self._parse_json_response(content)

            # 結果検証
            self._validate_answer_check_result(result)

            logger.info(f"Answer checked. Correct: {result.get('is_correct', False)}")
            return result

        except Exception as e:
            logger.error(f"Answer check failed: {e}")
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                message="回答チェックに失敗しました",
                error_code=LLM_GENERATION_FAILED,
                detail=str(e),
            ) from None

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """
        LLMレスポンスからJSONを解析

        Args:
            content: LLMからのレスポンステキスト

        Returns:
            解析されたJSON

        Raises:
            LLMError: JSON解析失敗時
        """
        try:
            # JSONブロックを探して抽出
            content = content.strip()

            # ```json から ``` までを抽出
            if "```json" in content:
                json_tag = "```json"
                start = content.find(json_tag) + len(json_tag)
                end = content.find("```", start)
                if end != -1:
                    json_text = content[start:end].strip()
                else:
                    json_text = content[start:].strip()
            else:
                # JSONブロックがない場合は全体をJSONとして扱う
                json_text = content

            parsed_json: dict[str, Any] = json.loads(json_text)
            return parsed_json

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parse error: {e}. Content: {content[:200]}...")
            raise LLMError(
                message="LLM応答の解析に失敗しました",
                error_code=LLM_INVALID_RESPONSE,
                detail=f"JSONフォーマットエラー: {e!s}",
            ) from None

    def _validate_table_generation_result(self, result: dict[str, Any]) -> None:
        """テーブル生成結果の検証"""
        required_fields = ["theme", "sql_statements"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="テーブル生成結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません",
                )

        if not isinstance(result["sql_statements"], list):
            raise LLMError(
                message="テーブル生成結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="sql_statements は配列である必要があります",
            )

    def _validate_problem_generation_result(self, result: dict[str, Any]) -> None:
        """問題生成結果の検証"""
        required_fields = ["difficulty", "correct_sql", "expected_result"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="問題生成結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません",
                )

        if not isinstance(result["expected_result"], list):
            raise LLMError(
                message="問題生成結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="expected_result は配列である必要があります",
            )

    def _validate_answer_check_result(self, result: dict[str, Any]) -> None:
        """回答チェック結果の検証"""
        required_fields = ["is_correct", "feedback"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="回答チェック結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません",
                )

        if not isinstance(result["is_correct"], bool):
            raise LLMError(
                message="回答チェック結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="is_correct はboolean値である必要があります",
            )

    async def check_health(self) -> bool:
        """
        LLMサービスの健全性チェック

        Returns:
            正常に動作するかどうか
        """
        return await self.llm_client.check_health()
