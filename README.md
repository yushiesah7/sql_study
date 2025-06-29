# SQL学習アプリケーション

AIを活用した新しいタイプのSQL学習アプリケーションです。  
表示された結果から逆算してSQLを考える「逆引き学習方式」を採用しています。

## 特徴

- 🤖 AIが自動でテーブルとサンプルデータを生成
- 📊 実行結果を見てSQLを推測する学習方式
- 💡 AIによる的確なフィードバックとヒント
- 🔒 安全な実行環境（SELECT文のみ許可）
- 🆓 完全無料（LocalAI使用）

## 技術スタック

- **バックエンド**: FastAPI + Python 3.11
- **フロントエンド**: Next.js 14 + TypeScript + Tailwind CSS
- **データベース**: PostgreSQL 15
- **AI/LLM**: LocalAI（OpenAI API互換）
- **インフラ**: Docker Compose

## 必要な環境

- Docker Desktop
- 8GB以上のメモリ
- 10GB以上の空きストレージ（AIモデル用）

## セットアップ

### 1. リポジトリのクローン
```bash
git clone <your-repository-url>
cd sql_study
```

### 2. 環境変数の設定
```bash
cp .env.example .env
# 必要に応じて.envを編集
```

### 3. modelsディレクトリの作成
```bash
mkdir -p models
```

### 4. アプリケーション起動
```bash
docker-compose up -d
```

初回起動時はLocalAIのモデルダウンロードに5-10分かかります。

### 5. アクセス
- フロントエンド: [http://localhost:3000](http://localhost:3000)
- バックエンドAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
- LocalAI: [http://localhost:8080](http://localhost:8080)

## 使い方

1. **テーブル作成**: 「テーブルとデータ作成」ボタンをクリック
2. **問題生成**: 「問題作成」ボタンで新しい問題を生成
3. **SQL作成**: 表示された結果と同じになるSQLを入力
4. **回答チェック**: 「回答をチェック」ボタンで正誤判定

## 開発

### 開発環境の起動（推奨）
```bash
# 開発用Docker環境（ボリュームマウント・ホットリロード付き）
docker-compose -f docker-compose.dev.yml up -d

# または Makefile を使用
make dev
```

開発環境の特徴：
- ファイルの自動同期（ホストの変更が即座にコンテナに反映）
- ホットリロード対応（コード変更時に自動再起動）
- データベースのポート公開（5432）

### 開発用コマンド（Makefile）
```bash
# 開発環境起動
make dev

# ログ確認
make logs

# Linting/Formatting
make lint    # Ruffでコードチェック
make format  # Ruffでコードフォーマット

# テスト実行
make test

# データベース接続
make db-shell

# コンテナに入る
make backend-shell
make frontend-shell
```

### ローカル開発（Docker を使わない場合）
```bash
# バックエンド
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# フロントエンド
cd frontend
npm install
npm run dev
```

### テスト実行
```bash
# Docker環境
docker-compose exec backend pytest
docker-compose exec frontend npm test

# または Makefile
make test
make frontend-test
```

## プロジェクト構成
```
sql_study/
├── backend/          # FastAPIバックエンド
├── frontend/         # Next.jsフロントエンド
├── models/           # LocalAIモデル格納
├── docs/             # 設計ドキュメント
└── docker-compose.yml
```

## トラブルシューティング

### LocalAIが起動しない
```bash
# ログ確認
docker-compose logs -f llm

# 再起動
docker-compose restart llm
```

### データベース接続エラー
```bash
# PostgreSQLの状態確認
docker-compose ps db

# データベースに接続
docker-compose exec db psql -U postgres -d mydb
```

## 設計ドキュメント

詳細な設計は `docs/` ディレクトリを参照してください：
- [実装計画書](docs/design/implementation_plan.md)
- [API設計書](docs/design/03_api/)
- [データモデル設計書](docs/design/01_data_model/)

## ライセンス

MIT License

## 貢献

Issue や Pull Request は歓迎します！

## 作者

- GitHub: [@yushiesah7](https://github.com/yushiesah7)