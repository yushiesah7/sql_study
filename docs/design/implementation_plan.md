# 実装計画書: SQL学習アプリケーション

## 概要
このドキュメントは、SQL学習アプリケーションの実装を迷いなく進めるための作業計画書です。
各タスクの実施順序、作成するファイル、参照すべき設計書を明確に定義します。

## 実装の基本方針

1. **ボトムアップ開発**: 基盤部分から順に構築
2. **段階的動作確認**: 各段階で動作確認を実施
3. **設計書準拠**: 必ず対応する設計書を参照
4. **コメント最小**: コードで意図を表現

---

## フェーズ0: 開発環境準備（30分）

### タスク一覧
| # | タスク | 成果物 | 参照ドキュメント |
|---|--------|--------|----------------|
| 0.1 | プロジェクト初期化 | .gitignore, README.md | - |
| 0.2 | Docker環境確認 | docker-compose.yml更新 | 仕様.md |
| 0.3 | 環境変数ファイル作成 | .env, .env.example | 後述の環境変数一覧 |

### 0.3 環境変数設定
```env
# .env.example
# Database (Dockerコンテナ名を使用)
DATABASE_URL=postgresql://postgres:changethis@db:5432/mydb

# LocalAI (Dockerコンテナ名を使用)
LLM_API_URL=http://llm:8080/v1
LLM_MODEL_NAME=gpt-3.5-turbo
LLM_TIMEOUT=30.0

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001

# CORS設定
ALLOWED_ORIGINS=["http://localhost:3000","http://frontend:3000"]
```

---

## フェーズ1: バックエンド基盤構築（2時間）

### タスク一覧
| # | タスク | 作成ファイル | 参照ドキュメント | 確認方法 |
|---|--------|------------|----------------|---------|
| 1.1 | Pythonパッケージ設定 | backend/requirements.txt | 06_implementation_details/fastapi_structure.md | pip install -r requirements.txt |
| 1.2 | FastAPIアプリ初期化 | backend/app/main.py | 06_implementation_details/fastapi_structure.md | uvicorn app.main:app --reload |
| 1.3 | 設定管理 | backend/app/core/config.py | 06_implementation_details/fastapi_structure.md | - |
| 1.4 | Pydanticモデル | backend/app/schemas.py | 01_data_model/schemas_design.md | - |
| 1.5 | エラーハンドラー | backend/app/core/exceptions.py | 06_implementation_details/error_handling.md | - |

### 1.1 requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
asyncpg==0.29.0
httpx==0.25.2
python-multipart==0.0.6
python-dotenv==1.0.0
```

### 1.2 動作確認
```bash
cd backend
uvicorn app.main:app --reload
# http://localhost:8000/docs でSwagger UI確認
```

---

## フェーズ2: データベース接続（2時間）

### タスク一覧
| # | タスク | 作成ファイル | 参照ドキュメント | 確認方法 |
|---|--------|------------|----------------|---------|
| 2.1 | DB接続マネージャー | backend/app/core/db.py | 02_database/db_design.md | 接続テスト |
| 2.2 | 依存性注入設定 | backend/app/core/dependencies.py | 02_database/db_design.md | - |
| 2.3 | ヘルスチェックAPI | backend/app/api/health.py | - | GET /health |

### 2.3 動作確認
```bash
# PostgreSQLコンテナ起動
docker-compose up -d db

# ヘルスチェック
curl http://localhost:8000/health
```

---

## フェーズ3: LLM統合（3時間）

### タスク一覧
| # | タスク | 作成ファイル | 参照ドキュメント | 確認方法 |
|---|--------|------------|----------------|---------|
| 3.1 | LLMクライアント | backend/app/core/llm_client.py | 04_llm/llm_integration_design.md | ユニットテスト |
| 3.2 | プロンプト管理 | backend/app/core/prompts.py | 04_llm/prompt_designs.md | - |
| 3.3 | LLMヘルスチェック | （health.pyに追加） | 04_llm/llm_integration_design.md | GET /health |

### 3.3 動作確認
```bash
# LocalAIコンテナ起動
docker-compose up -d llm

# 動作テスト（別ファイルで）
python -m pytest tests/test_llm_client.py
```

---

## フェーズ4: API実装（4時間）

### タスク一覧
| # | タスク | 作成ファイル | 参照ドキュメント | 確認方法 |
|---|--------|------------|----------------|---------|
| 4.1 | ルーター統合 | backend/app/api/routes.py | - | - |
| 4.2 | テーブル作成API | backend/app/api/create_tables.py | 03_api/create_tables_api.md | POST /api/create-tables |
| 4.3 | スキーマ取得API | backend/app/api/table_schemas.py | 03_api/table_schemas_api.md | GET /api/table-schemas |
| 4.4 | 問題生成API | backend/app/api/generate_problem.py | 03_api/generate_problem_api.md | POST /api/generate-problem |
| 4.5 | 回答チェックAPI | backend/app/api/check_answer.py | 03_api/check_answer_api.md | POST /api/check-answer |

### 4.2-4.5 実装の順序
1. create_tables（他が依存）
2. table_schemas（確認用）
3. generate_problem（コア機能）
4. check_answer（最終機能）

### 動作確認スクリプト
```bash
# tests/manual_test.sh
#!/bin/bash

# 1. テーブル作成
curl -X POST http://localhost:8000/api/create-tables \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. スキーマ確認
curl http://localhost:8000/api/table-schemas

# 3. 問題生成
curl -X POST http://localhost:8000/api/generate-problem \
  -H "Content-Type: application/json" \
  -d '{}'

# 4. 回答チェック（problem_idは上記の結果から）
curl -X POST http://localhost:8000/api/check-answer \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "problem_id": 1,
      "user_sql": "SELECT * FROM employees"
    }
  }'
```

---

## フェーズ5: フロントエンド実装（4時間）

### タスク一覧
| # | タスク | 作成ファイル | 参照ドキュメント | 確認方法 |
|---|--------|------------|----------------|---------|
| 5.1 | Next.jsプロジェクト作成 | frontend/全体 | 05_frontend/frontend_design.md | npm run dev |
| 5.2 | 型定義 | frontend/src/types/index.ts | 05_frontend/frontend_design.md | tsc --noEmit |
| 5.3 | API通信層 | frontend/src/lib/api.ts | 05_frontend/frontend_design.md | - |
| 5.4 | 基本コンポーネント | frontend/src/components/*.tsx | 05_frontend/component_design.md | Storybook（optional） |
| 5.5 | メインページ実装 | frontend/src/app/page.tsx | 05_frontend/component_design.md | ブラウザ確認 |

### 5.1 プロジェクト作成
```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
# 後でsrcディレクトリに移動
```

### 5.5 段階的実装
1. 静的UIの実装（ボタンと枠のみ）
2. API通信の追加
3. 状態管理の追加
4. エラーハンドリング追加

---

## フェーズ6: 統合・最終調整（2時間）

### タスク一覧
| # | タスク | 更新ファイル | 確認方法 |
|---|--------|------------|---------|
| 6.1 | Docker Compose統合 | docker-compose.yml | docker-compose up |
| 6.2 | 環境変数調整 | .env | 各サービス接続確認 |
| 6.3 | CORS設定確認 | backend/app/main.py | ブラウザからAPI呼び出し |
| 6.4 | エラーケーステスト | - | 手動テスト |
| 6.5 | README更新 | README.md | - |

### 6.4 必須テストケース
- [ ] DBが起動していない状態でのアクセス
- [ ] LLMが起動していない状態でのアクセス
- [ ] 不正なSQL入力
- [ ] 長時間実行されるSQL
- [ ] ネットワークエラー

---

## デバッグ用コマンド集

### Docker関連
```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f backend
docker-compose logs -f llm

# コンテナに入る
docker-compose exec backend bash
docker-compose exec db psql -U postgres -d mydb

# 再起動
docker-compose restart backend
```

### バックエンド開発
```bash
cd backend

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 型チェック
mypy app/

# テスト実行
pytest
```

### フロントエンド開発
```bash
cd frontend

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 型チェック
npm run type-check

# リント
npm run lint
```

---

## トラブルシューティング

### よくある問題と解決策

| 問題 | 原因 | 解決策 |
|-----|------|--------|
| "Connection refused" | サービス未起動 | docker-compose up -d |
| "Module not found" | パッケージ未インストール | pip install -r requirements.txt |
| CORS エラー | CORS設定ミス | main.pyのallow_origins確認 |
| "Table not found" | テーブル未作成 | POST /api/create-tables |
| LLMタイムアウト | モデル未ロード | LocalAIログ確認、モデル設定 |

---

## 実装チェックリスト

### バックエンド
- [ ] FastAPIが起動する
- [ ] Swagger UIが表示される（/docs）
- [ ] DBに接続できる
- [ ] LLMに接続できる
- [ ] 全APIが動作する

### フロントエンド  
- [ ] Next.jsが起動する
- [ ] APIと通信できる
- [ ] 全機能が動作する
- [ ] エラー時の表示が適切
- [ ] レスポンシブ対応

### 統合
- [ ] docker-compose upで全て起動
- [ ] エンドツーエンドで動作
- [ ] エラー時の挙動が適切

---

## 作業時間見積もり

| フェーズ | 見積時間 | 実績 |
|---------|---------|------|
| 環境準備 | 30分 | - |
| バックエンド基盤 | 2時間 | - |
| DB接続 | 2時間 | - |
| LLM統合 | 3時間 | - |
| API実装 | 4時間 | - |
| フロントエンド | 4時間 | - |
| 統合・調整 | 2時間 | - |
| **合計** | **17.5時間** | - |

※ 経験により変動。デバッグ時間は別途。

---

## 次のアクション

1. この計画書を確認
2. 不明点があれば設計書を参照
3. フェーズ0から順番に実装開始

実装で迷ったら、必ず対応する設計書を参照すること。