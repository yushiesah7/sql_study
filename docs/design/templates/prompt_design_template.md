# LLMプロンプト設計書: [プロンプト名]

## 概要
[このプロンプトの目的と期待する出力を2-3文で説明]

## 基本情報
| 項目 | 内容 |
|-----|------|
| プロンプトID | PROMPT_XXX |
| 使用場所 | ファイル名:関数名 |
| LLMモデル | gpt-3.5-turbo / gpt-4 等 |
| 最大トークン数 | 入力: xxx / 出力: xxx |
| 温度パラメータ | 0.0 - 1.0 |

## プロンプトテンプレート

### システムプロンプト
```
あなたはSQL学習アプリケーションのアシスタントです。
以下の制約に従って回答してください：
- 日本語で回答する
- 教育的な内容にする
- 具体例を含める
```

### ユーザープロンプト
```
{context}

以下の要件に従って{task}を実行してください：

要件：
1. {requirement1}
2. {requirement2}
3. {requirement3}

{additional_info}

出力形式：
{output_format}
```

## 入力変数

| 変数名 | 型 | 必須 | 説明 | 例 |
|-------|---|------|------|---|
| context | string | ○ | 現在の状況説明 | "テーブル構造: ..." |
| task | string | ○ | 実行するタスク | "SQL問題を生成" |
| requirement1 | string | ○ | 要件1 | "SELECT文を使用" |
| requirement2 | string | × | 要件2 | "JOINを含む" |
| requirement3 | string | × | 要件3 | "3-5行の結果" |
| additional_info | string | × | 追加情報 | "難易度: 中級" |
| output_format | string | ○ | 出力形式指定 | "JSON形式で..." |

## 期待する出力

### 出力形式
```json
{
  "result": "生成された内容",
  "metadata": {
    "difficulty": "medium",
    "category": "join"
  }
}
```

### 出力例
```json
{
  "result": "SELECT e.name, d.department_name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.location = '東京'",
  "metadata": {
    "difficulty": "medium",
    "category": "join"
  }
}
```

## プロンプトエンジニアリング技法

### 使用する技法
- [ ] Few-shot learning（例示による学習）
- [ ] Chain of thought（思考の連鎖）
- [ ] Role playing（役割設定）
- [ ] Output formatting（出力形式指定）
- [ ] Constraints（制約条件）

### 具体的な実装
```python
# Few-shot example
examples = [
    {"input": "...", "output": "..."},
    {"input": "...", "output": "..."}
]

# Chain of thought
prompt += "\n\nステップごとに考えてください：\n1. まず...\n2. 次に...\n3. 最後に..."
```

## エラーハンドリング

### 想定されるエラー
| エラータイプ | 原因 | 対処法 |
|------------|------|--------|
| 形式エラー | JSON形式でない | 再実行 or デフォルト値 |
| 内容エラー | 要件を満たさない | プロンプト修正して再実行 |
| タイムアウト | 処理時間超過 | より簡潔なプロンプトに変更 |

### リトライ戦略
```python
max_retries = 3
for i in range(max_retries):
    try:
        result = call_llm(prompt)
        if validate_result(result):
            return result
    except Exception as e:
        if i == max_retries - 1:
            raise
        prompt = modify_prompt(prompt, e)
```

## パフォーマンス最適化

### トークン数削減
- [ ] 不要な説明を削除
- [ ] 簡潔な指示に変更
- [ ] 出力形式を最小化

### レスポンス時間改善
- [ ] ストリーミング対応
- [ ] キャッシュ活用
- [ ] 並列処理

## 品質保証

### 検証項目
- [ ] 出力の一貫性
- [ ] 要件への適合性
- [ ] エッジケースの処理
- [ ] 多様性の確保

### テストケース
| ケース | 入力 | 期待出力 | 備考 |
|-------|------|---------|------|
| 正常系1 | ... | ... | 基本的なケース |
| 正常系2 | ... | ... | 複雑なケース |
| 異常系1 | ... | エラー | 不正な入力 |

## 改善履歴

### バージョン管理
| バージョン | 変更日 | 変更内容 | 効果 |
|-----------|-------|---------|------|
| v1.0 | YYYY-MM-DD | 初版 | - |
| v1.1 | YYYY-MM-DD | 出力形式を明確化 | エラー率20%減 |

### A/Bテスト結果
| テスト項目 | バージョンA | バージョンB | 採用 |
|-----------|------------|------------|------|
| 正答率 | 85% | 92% | B |
| 応答時間 | 2.3秒 | 2.1秒 | B |

## 注意事項
- [ ] 個人情報を含めない
- [ ] 著作権に配慮
- [ ] 倫理的な内容
- [ ] 教育的価値の確保

## 関連ドキュメント
- [LLM API仕様書](../03_api/llm_api.md)
- [プロンプト実装ガイド](./prompt_guide.md)