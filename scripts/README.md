# 共通スクリプト

このディレクトリには、プロジェクト全体で使用する共通スクリプトを配置します。

## 使用方法

### 開発環境でのスクリプト実行
```bash
# バックエンドコンテナから実行
docker-compose -f docker-compose.dev.yml exec backend python /scripts/script_name.py

# 新しいコンテナで実行
docker-compose -f docker-compose.dev.yml run --rm backend python /scripts/script_name.py
```

## ディレクトリ構成
- `scripts/` - プロジェクト全体の共通スクリプト
- `backend/scripts/` - バックエンド専用スクリプト