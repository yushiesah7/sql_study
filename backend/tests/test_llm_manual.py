#!/usr/bin/env python3
import asyncio
import httpx
import json


async def test_llm():
    """最小限のLLMテスト"""
    url = "http://llm:8080/chat/completions"
    payload = {
        "model": "hermes-3-llama-3.2-3b",
        "messages": [{"role": "user", "content": "1+1=?"}],
        "max_tokens": 10,
        "temperature": 0.1,
    }

    print(f"テスト開始: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            print(f"ステータス: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"回答: {content}")
            else:
                print(f"エラー: {response.text}")
    except Exception as e:
        print(f"例外: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_llm())
