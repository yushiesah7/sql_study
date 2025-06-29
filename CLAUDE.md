# SQL学習アプリケーション - プロジェクト固有指示

## プロジェクト概要
このプロジェクトは「結果から逆算してSQLを考える」逆引き型のSQL学習アプリケーションです。
AIが生成したSQL実行結果を見て、ユーザーが同じ結果を得られるSQLを作成する学習方式を採用しています。

## アプリケーションフロー
1. **テーブルとデータ作成**: AIがランダムなテーマ（社員管理、図書館、ECサイトなど）でテーブルを自動生成
2. **問題作成**: AIがSQLを内部で実行し、その結果のみを表示
3. **ユーザー回答**: 表示された結果と同じになるSQLを推測して入力
4. **採点とフィードバック**: AIが正誤判定と改善アドバイスを提供
5. **次の問題へ**: 同じテーブルで新しい問題、または新しいテーマで最初から

## ディレクトリ構成
```text
sql_study/
├── backend/
│   ├── app/               # FastAPIアプリケーション
│   ├── tests/             # テストコード
│   ├── scripts/           # バックエンド専用スクリプト
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/               # Next.jsソースコード
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
├── docs/
│   ├── task_list.md       # 実装タスクリスト（実行順序付き）
│   └── design/            # 設計書
├── models/
│   └── llm/               # LLMモデルファイル（*.gguf）
├── scripts/               # 共通スクリプト
├── logs/                  # ログファイル
├── .env                   # 環境変数設定
├── .gitignore
├── docker-compose.yml     # 本番用Docker Compose設定
├── docker-compose.dev.yml # 開発用Docker Compose設定
├── CLAUDE.md             # プロジェクト固有指示
└── README.md
```

## 実装時の重要事項

### セキュリティ
- ユーザーが実行できるのはSELECT文のみ
- DROP, DELETE, UPDATE, INSERTは禁止
- SQLインジェクション対策必須
- 実行タイムアウト: 5秒

### UI/UX最小要件
1. テーブルとデータ作成ボタン
2. 問題作成ボタン
3. テーブル構造表示エリア
4. 期待される結果表示
5. SQL入力フォーム
6. 回答チェックボタン
7. エラー/ローディング表示

### 技術スタック
- バックエンド: FastAPI + PostgreSQL + LocalAI
- フロントエンド: Next.js + TypeScript + Tailwind CSS
- インフラ: Docker Compose

## 現在の進捗状況
- [x] 基本ディレクトリ構造作成
- [x] 仕様書（仕様.md）作成
- [ ] フェーズ1: データモデル設計
- [ ] フェーズ2: API設計
- [ ] フェーズ3: フロントエンド設計
- [ ] フェーズ4: 実装詳細設計
- [ ] フェーズ5: 統合設計

## 設計フェーズの注意点
1. **設計書は必ずテンプレートを使用**（docs/design/templates/）
2. **実装前に設計書のレビューを実施**
3. **依存関係を考慮した実装順序を守る**（docs/task_list.md参照）

## コマンド実行時の注意事項
- コマンドを実行する際は、必ずそのコマンドの意味と動作を説明すること
- 特に初めて使うコマンドや、システムに影響を与えるコマンドは詳細に解説する
- 代替手段がある場合は併せて提示する

## バックエンド開発ルール

### アーキテクチャ概要
- **本番環境**: Dockerfileで`COPY`を使用し、ビルド時にファイルを固定
- **開発環境**: docker-compose.dev.ymlでボリュームマウントを使用し、ホットリロード対応
- **フレームワーク**: FastAPI + uvicorn
- **データベース**: PostgreSQL 15
- **LLM**: LocalAI

### 開発フロー

#### 1. 開発環境の起動
```bash
# 開発用docker-compose（ボリュームマウント・ホットリロード付き）
docker-compose -f docker-compose.dev.yml up -d

# 本番用docker-compose（イメージビルド方式）
docker-compose up -d
```

#### 2. コード修正時の対応
**開発環境の場合**:
- ホストでファイルを編集すると、自動的にコンテナに反映される
- uvicornの`--reload`オプションによりサーバーが自動再起動

**本番環境の場合**:
- イメージの再ビルドが必要
```bash
docker-compose build backend
docker-compose up -d backend
```

#### 3. Linting/Formatting

**統一コマンド（推奨）**:
```bash
# Makefileコマンド（開発環境で統一されたlint/format）
make lint     # Ruffでコードをチェック
make format   # Ruffでコードをフォーマット 
make mypy     # 型チェックを実行
```

**直接実行の場合**:
```bash
# コンテナ内で実行（開発環境・本番環境共通）
docker-compose -f docker-compose.dev.yml exec backend ruff check /app
docker-compose -f docker-compose.dev.yml exec backend ruff format /app
docker-compose -f docker-compose.dev.yml exec backend mypy /app
```

#### 4. テスト実行
```bash
# 開発環境・本番環境共通
docker-compose exec backend pytest
```

### よく使うコマンド

```bash
# ログ確認
docker-compose logs -f backend

# データベース接続
docker-compose exec db psql -U postgres -d mydb

# コンテナに入る
docker-compose exec backend bash

# 依存関係の更新
docker-compose exec backend pip install -r requirements.txt

# Linter/Formatter実行（バックエンド）
docker-compose -f docker-compose.dev.yml run --rm backend ruff check /app
docker-compose -f docker-compose.dev.yml run --rm backend ruff format /app
docker-compose -f docker-compose.dev.yml run --rm backend mypy /app

# テスト実行
docker-compose -f docker-compose.dev.yml run --rm backend pytest

# スクリプト実行

# バックエンド専用スクリプト（backend/scripts/内のファイル）
# コンテナ内パス: /app/scripts/
docker-compose -f docker-compose.dev.yml exec backend python /app/scripts/test_llm_manual.py
docker-compose -f docker-compose.dev.yml exec backend python /app/scripts/test_create_tables_api.py

# 共通スクリプト（scripts/内のファイル）  
# コンテナ内パス: /scripts/
docker-compose -f docker-compose.dev.yml exec backend python /scripts/common_utility.py
docker-compose -f docker-compose.dev.yml exec frontend node /scripts/frontend_utility.js

# フロントエンドLinter/Formatter
cd frontend
npm run lint
npm run prettier:check
npm run format  # ESLint + Prettier自動修正
```

### トラブルシューティング

#### ファイルが同期されない場合
1. docker-compose.dev.ymlを使用しているか確認
2. ボリュームマウントのパスが正しいか確認
3. コンテナを再起動: `docker-compose -f docker-compose.dev.yml restart backend`

#### ポート競合エラー
1. 既存のプロセスを確認: `lsof -i :8001`
2. docker-compose.ymlのポート設定を変更

#### ImportError
1. 依存関係を再インストール: `docker-compose exec backend pip install -r requirements.txt`
2. PYTHONPATH確認: コンテナ内で`echo $PYTHONPATH`