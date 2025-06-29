#!/usr/bin/env python3
import asyncio
import json

import httpx


async def test_create_tables() -> None:
    """テーブル作成APIのテスト(軽量版)"""
    url = "http://llm:8080/chat/completions"

    # まず直接LLMをテストして応答速度を確認
    simple_payload = {
        "model": "hermes-3-llama-3.2-3b",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer very briefly.",
            },
            {
                "role": "user",
                "content": "List 3 programming languages in a comma-separated list.",
            },
        ],
        "max_tokens": 50,
        "temperature": 0.1,
    }

    print("=== 直接LLMテスト ===")
    print(f"リクエスト: {json.dumps(simple_payload, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.post(url, json=simple_payload)
            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"ステータス: {response.status_code}")
            print(f"応答時間: {elapsed:.2f}秒")

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"回答: {content}")
            else:
                print(f"エラー: {response.text}")

    except Exception as e:
        print(f"例外: {type(e).__name__}: {e}")

    print("\n=== APIテスト(軽量版) ===")
    # APIテスト - max_tokensを小さくして軽量なレスポンスを要求
    api_url = "http://backend:8000/api/create-tables"
    api_payload = {
        "prompt": "小さな本のテーブルだけ作成してください。データは3件だけ。"
    }

    print(f"APIリクエスト: {json.dumps(api_payload, ensure_ascii=False)}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = asyncio.get_event_loop().time()
            response = await client.post(api_url, json=api_payload)
            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"ステータス: {response.status_code}")
            print(f"応答時間: {elapsed:.2f}秒")

            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                print(f"成功: {result.get('success', False)}")
                print(f"メッセージ: {result.get('message', '')}")
                print(f"テーマ: {data.get('theme', 'Unknown')}")
                print(f"テーブル数: {data.get('table_count', 0)}")
            else:
                print(f"エラー: {response.text}")

    except Exception as e:
        print(f"例外: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_create_tables())
