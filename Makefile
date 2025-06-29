# SQL学習アプリケーション - Makefile
# 開発タスクを簡略化するためのコマンド集

.PHONY: help dev prod down build logs test lint format clean

# デフォルトターゲット
help: ## ヘルプを表示
	@echo "使用可能なコマンド:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 開発環境
dev: ## 開発環境を起動（ホットリロード付き）
	docker-compose -f docker-compose.dev.yml up -d
	@echo "開発環境が起動しました"
	@echo "Backend: http://localhost:8001"
	@echo "Frontend: http://localhost:3000"

dev-build: ## 開発環境を再ビルドして起動
	docker-compose -f docker-compose.dev.yml build
	docker-compose -f docker-compose.dev.yml up -d

# 本番環境
prod: ## 本番環境を起動
	docker-compose up -d
	@echo "本番環境が起動しました"
	@echo "Backend: http://localhost:8001"
	@echo "Frontend: http://localhost:3000"

build: ## 本番環境を再ビルド
	docker-compose build

# 共通コマンド
down: ## 環境を停止
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

logs: ## ログを表示（backend）
	docker-compose logs -f backend

logs-all: ## 全サービスのログを表示
	docker-compose logs -f

# バックエンド開発
backend-shell: ## バックエンドコンテナに入る
	docker-compose exec backend bash

test: ## テストを実行
	docker-compose exec backend pytest

test-v: ## テストを詳細実行
	docker-compose exec backend pytest -v

lint: ## Ruffでコードをチェック
	docker-compose -f docker-compose.dev.yml exec backend ruff check /app

format: ## Ruffでコードをフォーマット
	docker-compose -f docker-compose.dev.yml exec backend ruff format /app

mypy: ## 型チェックを実行
	docker-compose -f docker-compose.dev.yml exec backend mypy /app

# フロントエンド開発
frontend-shell: ## フロントエンドコンテナに入る
	docker-compose exec frontend sh

frontend-lint: ## ESLintでコードをチェック
	docker-compose exec frontend npm run lint

frontend-format: ## Prettierでコードをフォーマット
	docker-compose exec frontend npm run format

frontend-build: ## フロントエンドをビルド
	docker-compose exec frontend npm run build

# データベース
db-shell: ## データベースに接続
	docker-compose exec db psql -U postgres -d mydb

db-backup: ## データベースをバックアップ
	docker-compose exec db pg_dump -U postgres mydb > backup_$$(date +%Y%m%d_%H%M%S).sql

# クリーンアップ
clean: ## 未使用のDockerリソースをクリーンアップ
	docker system prune -f
	docker volume prune -f

clean-all: ## 全てのDockerリソースをクリーンアップ（注意）
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -af
	docker volume prune -f

# 状態確認
status: ## サービスの状態を確認
	@echo "=== 本番環境 ==="
	@docker-compose ps
	@echo "\n=== 開発環境 ==="
	@docker-compose -f docker-compose.dev.yml ps

# 初期セットアップ
setup: ## 初期セットアップ
	@echo "環境変数ファイルをコピーしています..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "開発環境を起動しています..."
	@make dev
	@echo "セットアップが完了しました！"