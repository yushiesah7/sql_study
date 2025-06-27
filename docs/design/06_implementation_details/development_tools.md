# 開発ツール設定詳細

## 概要
このドキュメントでは、SQL学習アプリケーションで使用するLinter、Formatter、その他開発ツールの設定を記載します。

## バックエンド（Python）

### Ruff
バージョン: 0.12.0

#### 設定ファイル
- `backend/pyproject.toml`: メイン設定
- `backend/.ruff.toml`: 追加設定（レガシー）

#### 主な設定内容（pyproject.toml）
```toml
[tool.ruff]
line-length = 88  # Blackデフォルトに合わせる
fix = true  # 自動修正を有効化
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ASYNC",  # flake8-async
    "RUF",    # Ruff固有ルール
]

ignore = [
    "B008",   # function calls in argument defaults
    "SIM108", # Use ternary operator
    "RUF012", # Mutable class attributes should be annotated
]

exclude = [
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "migrations",
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ARG001", "ARG002"]  # テストでは未使用引数を許可

[tool.ruff.lint.isort]
known-first-party = ["app"]
combine-as-imports = true

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

#### 実行コマンド
```bash
# Lintチェック
cd backend
ruff check .

# 自動フォーマット
ruff format .

# Docker環境での実行（開発環境）
docker-compose -f docker-compose.dev.yml run --rm backend ruff check /app
docker-compose -f docker-compose.dev.yml run --rm backend ruff format /app
```

### Black（補助的に使用）
バージョン: 定義されているが主にRuffを使用

```toml
[tool.black]
line-length = 79
target-version = ['py311']
include = '\.pyi?$'
```

### mypy
型チェックツール

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = false
ignore_missing_imports = true
no_implicit_optional = true
check_untyped_defs = true
strict_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### 実行コマンド
```bash
# ローカル実行
cd backend
mypy app

# Docker環境での実行
docker-compose -f docker-compose.dev.yml run --rm backend mypy /app
```

### pytest
テストフレームワーク

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## フロントエンド（TypeScript/React）

### ESLint
バージョン: 8.57.0

#### 設定ファイル: `.eslintrc.json`
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": [
      "error",
      { "argsIgnorePattern": "^_" }
    ]
  }
}
```

#### 実行コマンド
```bash
# Lintチェック
cd frontend
npm run lint

# 自動修正
npm run lint -- --fix
```

### Prettier
バージョン: 3.6.0

#### 設定ファイル: `.prettierrc.json`
```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "plugins": ["prettier-plugin-tailwindcss"],
  "tailwindConfig": "./tailwind.config.js"
}
```

#### 実行コマンド
```bash
# フォーマットチェック
cd frontend
npm run prettier:check

# 自動フォーマット
npm run prettier:fix
```

### 統合設定（package.json）
```json
{
  "scripts": {
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
    "prettier:check": "prettier --check \"src/**/*.{js,jsx,ts,tsx,css,md}\"",
    "prettier:fix": "prettier --write \"src/**/*.{js,jsx,ts,tsx,css,md}\"",
    "format": "npm run prettier:fix && npm run lint:fix"
  }
}
```

## CI/CD統合

### GitHub Actions（.github/workflows/ci.yml）
```yaml
- name: Run Ruff
  run: |
    cd backend
    ruff check .
    ruff format --check .

- name: Run mypy
  run: |
    cd backend
    mypy app

- name: Lint
  run: |
    cd frontend
    npm run lint

- name: Format check
  run: |
    cd frontend
    npm run prettier:check
```

## VS Code推奨設定

`.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

## 開発フロー

1. **コード記述時**
   - VS Codeの自動フォーマット機能を活用
   - 保存時に自動的にフォーマット

2. **コミット前**
   - バックエンド: `ruff check . && ruff format .`
   - フロントエンド: `npm run format`

3. **CI/CDパイプライン**
   - プルリクエスト時に自動的にチェック
   - フォーマットエラーがある場合はマージ不可

## トラブルシューティング

### Ruffエラーが出る場合
1. Python 3.11以上がインストールされているか確認
2. `pip install -r requirements.txt`で依存関係を更新
3. `.ruff_cache`を削除して再実行

### ESLintエラーが出る場合
1. `node_modules`を削除して`npm install`を実行
2. `.eslintcache`を削除
3. TypeScriptのバージョンを確認

### Prettierとの競合
1. ESLintとPrettierの設定が競合しないよう注意
2. `eslint-config-prettier`が正しく設定されているか確認

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-27 | 1.0.0 | 初版作成 | - |