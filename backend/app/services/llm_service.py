"""
LLM統合サービス
LLMクライアントとプロンプト生成を組み合わせた高レベルサービス
"""
import json
import logging
from typing import Dict, Any, Optional, List

from app.core.llm_client import LocalAIClient
from app.services.prompt_generator import PromptGenerator
from app.core.exceptions import LLMError
from app.core.error_codes import LLM_INVALID_RESPONSE, LLM_GENERATION_FAILED

logger = logging.getLogger(__name__)


class LLMService:
    """LLM統合サービスクラス"""
    
    def __init__(self, llm_client: LocalAIClient):
        """
        Initialize the LLMService with a given LLM client and create a prompt generator instance.
        """
        self.llm_client = llm_client
        self.prompt_generator = PromptGenerator()
    
    async def generate_tables(self, user_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates SQL table creation statements based on an optional user prompt.
        
        Parameters:
            user_prompt (Optional[str]): An optional instruction or theme provided by the user to guide table generation.
        
        Returns:
            Dict[str, Any]: A dictionary containing the generated theme, description, and a list of SQL statements for table creation.
        
        Raises:
            LLMError: If table generation fails or the response is invalid.
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
            
            logger.info(f"Generated tables for theme: {result.get('theme', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Table generation failed: {e}")
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                message="テーブル生成に失敗しました",
                error_code=LLM_GENERATION_FAILED,
                detail=str(e)
            )
    
    async def generate_problem(
        self, 
        table_schemas: List[Dict[str, Any]], 
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a SQL problem based on provided table schemas and an optional user prompt.
        
        Parameters:
            table_schemas (List[Dict[str, Any]]): List of table schema definitions to base the problem on.
            user_prompt (Optional[str]): Additional instructions or context from the user.
        
        Returns:
            Dict[str, Any]: A dictionary containing the generated problem, including difficulty, correct SQL, expected result, and an optional hint.
        
        Raises:
            LLMError: If problem generation fails or the response is invalid.
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
            
            logger.info(f"Generated problem with difficulty: {result.get('difficulty', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Problem generation failed: {e}")
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                message="問題生成に失敗しました",
                error_code=LLM_GENERATION_FAILED,
                detail=str(e)
            )
    
    async def check_answer(
        self,
        user_sql: str,
        user_result: List[Dict[str, Any]],
        expected_result: List[Dict[str, Any]],
        table_schemas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Checks the correctness of a user's SQL answer against the expected result and table schemas using an LLM.
        
        Parameters:
            user_sql (str): The SQL query submitted by the user.
            user_result (List[Dict[str, Any]]): The result produced by executing the user's SQL.
            expected_result (List[Dict[str, Any]]): The expected result for the SQL problem.
            table_schemas (List[Dict[str, Any]]): Schema definitions for the relevant tables.
        
        Returns:
            Dict[str, Any]: A dictionary containing the answer evaluation, including:
                - is_correct (bool): Whether the user's answer is correct.
                - score (int): The score assigned to the answer.
                - feedback (str): Feedback on the answer.
                - improvement_suggestions (List[str]): Suggestions for improvement.
                - hint (Optional[str]): An optional hint for the user.
        
        Raises:
            LLMError: If answer checking fails or the response is invalid.
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
                detail=str(e)
            )
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parses and returns a JSON object from the LLM response content.
        
        If the content includes a markdown-style JSON code block, extracts and parses the JSON within the block; otherwise, parses the entire content as JSON.
        
        Raises:
            LLMError: If the content cannot be parsed as valid JSON.
        """
        try:
            # JSONブロックを探して抽出
            content = content.strip()
            
            # ```json から ``` までを抽出
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_text = content[start:end].strip()
                else:
                    json_text = content[start:].strip()
            else:
                # JSONブロックがない場合は全体をJSONとして扱う
                json_text = content
            
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON parse error: {e}. Content: {content[:200]}...")
            raise LLMError(
                message="LLM応答の解析に失敗しました",
                error_code=LLM_INVALID_RESPONSE,
                detail=f"JSONフォーマットエラー: {str(e)}"
            )
    
    def _validate_table_generation_result(self, result: Dict[str, Any]) -> None:
        """
        Validate the result of table generation to ensure required fields and correct types are present.
        
        Raises:
            LLMError: If required fields are missing or if 'sql_statements' is not a list.
        """
        required_fields = ["theme", "sql_statements"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="テーブル生成結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません"
                )
        
        if not isinstance(result["sql_statements"], list):
            raise LLMError(
                message="テーブル生成結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="sql_statements は配列である必要があります"
            )
    
    def _validate_problem_generation_result(self, result: Dict[str, Any]) -> None:
        """
        Validate the structure of a problem generation result.
        
        Raises:
            LLMError: If required fields are missing or if 'expected_result' is not a list.
        """
        required_fields = ["difficulty", "correct_sql", "expected_result"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="問題生成結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません"
                )
        
        if not isinstance(result["expected_result"], list):
            raise LLMError(
                message="問題生成結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="expected_result は配列である必要があります"
            )
    
    def _validate_answer_check_result(self, result: Dict[str, Any]) -> None:
        """
        Validate the structure and types of the answer check result.
        
        Raises:
            LLMError: If required fields are missing or if 'is_correct' is not a boolean.
        """
        required_fields = ["is_correct", "feedback"]
        for field in required_fields:
            if field not in result:
                raise LLMError(
                    message="回答チェック結果が不正です",
                    error_code=LLM_INVALID_RESPONSE,
                    detail=f"必須フィールド '{field}' が見つかりません"
                )
        
        if not isinstance(result["is_correct"], bool):
            raise LLMError(
                message="回答チェック結果が不正です",
                error_code=LLM_INVALID_RESPONSE,
                detail="is_correct はboolean値である必要があります"
            )
    
    async def check_health(self) -> bool:
        """
        Asynchronously checks whether the LLM client service is operational.
        
        Returns:
            bool: True if the LLM client is healthy and responsive; otherwise, False.
        """
        return await self.llm_client.check_health()