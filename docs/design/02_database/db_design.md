# データベース設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションのデータベース設計を定義します。
PostgreSQLを使用し、学習用のサンプルデータと問題管理に必要な最小限の構成から始めます。

## 設計方針

1. **動的なテーブル生成**: AIが学習用テーブルを動的に作成・削除
2. **セッション単位の管理**: 問題の履歴と進捗をメモリ/軽量DBで管理
3. **セキュリティ重視**: ユーザーは読み取り専用アクセスのみ

## データベース構成

### 1. システム管理用スキーマ（app_system）

システムが内部的に使用するテーブル群です。

#### problems（問題管理テーブル）

```sql
CREATE TABLE app_system.problems (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,  -- 現在のテーマ（社員管理、図書館等）
    correct_sql TEXT NOT NULL,    -- AIが生成した正解SQL
    result_json JSONB NOT NULL,   -- 正解SQLの実行結果
    difficulty INTEGER DEFAULT 1, -- 難易度（1-10）
    category VARCHAR(50),         -- カテゴリ（select, join, aggregate等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE  -- 現在の問題かどうか
);

-- インデックス
CREATE INDEX idx_problems_active ON app_system.problems(is_active);
CREATE INDEX idx_problems_created ON app_system.problems(created_at DESC);
```

#### session_state（セッション状態管理）

```sql
CREATE TABLE app_system.session_state (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 保存する情報の例
INSERT INTO app_system.session_state (key, value) VALUES
('current_theme', '"社員管理"'),
('difficulty_level', '3'),
('problem_count', '5'),
('correct_count', '3');
```

### 2. 学習用スキーマ（public）

AIが動的に作成・削除する学習用テーブルです。

#### テーマ例1: 社員管理システム

```sql
-- AIが自動生成するテーブル例
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER,
    position VARCHAR(50),
    salary INTEGER,
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    location VARCHAR(100),
    manager_id INTEGER
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department_id INTEGER,
    start_date DATE,
    end_date DATE,
    budget INTEGER
);

-- 外部キー制約
ALTER TABLE employees ADD FOREIGN KEY (department_id) REFERENCES departments(id);
ALTER TABLE departments ADD FOREIGN KEY (manager_id) REFERENCES employees(id);
ALTER TABLE projects ADD FOREIGN KEY (department_id) REFERENCES departments(id);
```

#### テーマ例2: 図書館システム

```sql
-- 別のテーマの例
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100),
    isbn VARCHAR(20) UNIQUE,
    publication_year INTEGER,
    category VARCHAR(50),
    available_copies INTEGER DEFAULT 1
);

CREATE TABLE members (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    join_date DATE DEFAULT CURRENT_DATE,
    membership_type VARCHAR(20)
);

CREATE TABLE loans (
    id INTEGER PRIMARY KEY,
    book_id INTEGER REFERENCES books(id),
    member_id INTEGER REFERENCES members(id),
    loan_date DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    return_date DATE
);
```

## データベース接続設計

### 接続プール設定

```python
# db.py での実装イメージ
class DatabaseConfig:
    # 接続プール設定
    MIN_CONNECTIONS = 2
    MAX_CONNECTIONS = 10
    CONNECTION_TIMEOUT = 5.0  # 秒
    QUERY_TIMEOUT = 5.0  # 秒（SELECT文の最大実行時間）
    
    # ユーザー権限
    ADMIN_USER = "postgres"  # テーブル作成・削除用
    READONLY_USER = "student"  # SELECT実行用（将来実装）
```

### 接続管理クラス

```python
class DatabaseManager:
    """データベース接続とクエリ実行を管理"""
    
    async def initialize(self):
        """接続プールの初期化"""
        
    async def execute_admin_query(self, sql: str):
        """管理者権限でのクエリ実行（DDL用）"""
        
    async def execute_select(self, sql: str, timeout: float = 5.0):
        """SELECT文の実行（タイムアウト付き）"""
        
    async def get_table_schemas(self):
        """現在のテーブル構造を取得"""
```

## セキュリティ設計

### 1. SQL実行の制限

```python
# 許可するSQL文のパターン
ALLOWED_SQL_PATTERNS = [
    r'^SELECT\s+',  # SELECT文のみ許可
    r'^WITH\s+.*SELECT\s+',  # CTE付きSELECT
]

# 禁止キーワード
FORBIDDEN_KEYWORDS = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE', 'EXEC'
]
```

### 2. ユーザー権限（将来実装）

```sql
-- 読み取り専用ユーザーの作成
CREATE USER student WITH PASSWORD 'readonly_password';

-- publicスキーマの読み取り権限のみ付与
GRANT USAGE ON SCHEMA public TO student;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO student;

-- デフォルト権限の設定
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO student;
```

## データ生成戦略

### サンプルデータの規模

| テーブル種別 | 最小行数 | 最大行数 | 備考 |
|-----------|---------|---------|------|
| マスタ系 | 10 | 100 | departments, categories等 |
| トランザクション系 | 100 | 1000 | employees, orders等 |
| 関連テーブル | 50 | 500 | 多対多の中間テーブル等 |

### データ生成の原則

1. **現実的なデータ**: 実際のビジネスで使われそうなデータ
2. **適度な複雑さ**: JOIN練習に適したリレーション
3. **日本語対応**: 名前や部署名は日本語を含む
4. **NULL値を含む**: 実践的なSQL練習のため

## テーブル管理フロー

### 1. テーブル作成時

```python
async def create_tables(theme: str):
    # 1. 既存の学習用テーブルを全削除
    await drop_all_learning_tables()
    
    # 2. セッション状態を更新
    await update_session_state("current_theme", theme)
    
    # 3. AIにテーブル構造を生成させる
    schema = await ai_generate_schema(theme)
    
    # 4. テーブルとデータを作成
    await create_tables_from_schema(schema)
    
    # 5. 問題履歴をリセット
    await deactivate_all_problems()
```

### 2. 問題生成時

```python
async def generate_problem():
    # 1. 現在のテーブル構造を取得
    schemas = await get_table_schemas()
    
    # 2. 難易度を自動調整
    difficulty = await calculate_next_difficulty()
    
    # 3. AIに問題SQL生成を依頼
    sql = await ai_generate_problem_sql(schemas, difficulty)
    
    # 4. SQLを実行して結果を保存
    result = await execute_select(sql)
    
    # 5. 問題を登録
    problem_id = await save_problem(sql, result, difficulty)
    
    return problem_id, result
```

## インデックス設計

学習用テーブルは動的生成のため、基本的なインデックスのみ：

```sql
-- プライマリキーは自動的にインデックス作成
-- 外部キーも自動的にインデックス作成（PostgreSQL）

-- 必要に応じてAIが追加するインデックスの例
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_active ON employees(is_active) WHERE is_active = TRUE;
```

## バックアップ・リカバリ戦略

学習用アプリケーションのため、最小限の構成：

1. **システムテーブル**: 定期的なバックアップ（1日1回）
2. **学習用テーブル**: バックアップ不要（都度生成）
3. **問題履歴**: 必要に応じてエクスポート機能

## パフォーマンス考慮事項

1. **クエリタイムアウト**: 5秒で強制終了
2. **結果セット制限**: 最大1000行
3. **同時実行制限**: 1ユーザー1クエリ
4. **定期的なVACUUM**: 自動VACUUM設定

## 拡張ポイント

### 将来追加可能な機能

1. **マルチユーザー対応**
   - ユーザーごとのスキーマ分離
   - 進捗の個別管理

2. **学習履歴の永続化**
   - 長期的な進捗追跡
   - 苦手分野の分析

3. **カスタムデータセット**
   - ユーザーがCSVアップロード
   - 独自のテーブル定義

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |