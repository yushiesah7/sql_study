#!/usr/bin/env python3
"""
テーブル作成APIのデバッグテスト
LLMレスポンスの詳細を確認
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.services.prompt_generator import PromptGenerator

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_table_creation():
    """テーブル作成の詳細テスト"""
    try:
        # LLMクライアント初期化
        llm_client = LLMClient()

        # プロンプト生成
        prompt_generator = PromptGenerator()
        messages = prompt_generator.create_table_generation_prompt()

        logger.info("=== Sending request to LLM ===")
        logger.info(f"Messages: {messages}")

        # LLM呼び出し
        response = await llm_client.chat_completion(messages)
        content = llm_client.extract_content(response)

        logger.info("=== Raw LLM Response ===")
        logger.info(content)
        logger.info("=== End of Response ===")

        # JSON解析を試みる
        try:
            # JSONブロックを探して抽出
            content_stripped = content.strip()
            
            if "```json" in content_stripped:
                json_tag = "```json"
                start = content_stripped.find(json_tag) + len(json_tag)
                end = content_stripped.find("```", start)
                if end != -1:
                    json_text = content_stripped[start:end].strip()
                else:
                    json_text = content_stripped[start:].strip()
            else:
                json_text = content_stripped

            logger.info("=== Extracted JSON ===")
            logger.info(json_text)
            logger.info("=== End of JSON ===")

            import json
            parsed = json.loads(json_text)
            logger.info("✅ JSON parsing successful!")
            logger.info(f"Theme: {parsed.get('theme')}")
            logger.info(f"Number of SQL statements: {len(parsed.get('sql_statements', []))}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.error(f"Error position: line {e.lineno}, column {e.colno}")
            # エラー位置の前後を表示
            lines = json_text.split('\n')
            if e.lineno <= len(lines):
                logger.error(f"Error line: {lines[e.lineno-1]}")
                if e.lineno > 1:
                    logger.error(f"Previous line: {lines[e.lineno-2]}")
                if e.lineno < len(lines):
                    logger.error(f"Next line: {lines[e.lineno]}")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_table_creation())