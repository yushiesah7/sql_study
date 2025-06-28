# バックエンド専用スクリプト

このディレクトリには、バックエンド固有のスクリプトを配置します。

## 使用方法

### 開発環境でのスクリプト実行
```bash
# バックエンドコンテナから実行
docker-compose -f docker-compose.dev.yml exec backend python /app/scripts/script_name.py

# 新しいコンテナで実行
docker-compose -f docker-compose.dev.yml run --rm backend python /app/scripts/script_name.py
```

## スクリプトの種類
- データベースマイグレーション
- データインポート/エクスポート
- バックエンド固有のユーティリティ