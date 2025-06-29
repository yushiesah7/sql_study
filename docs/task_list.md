な# SQL学習アプリケーション - 実行順序付き設計タスクリスト

## 概要
このドキュメントは、SQL学習アプリケーションの設計・実装タスクを実行順序に従って管理するためのリストです。
各フェーズは前のフェーズに依存するため、順序を守って実施してください。

---

## フェーズ1: 基盤設計（データ構造の定義）

### 1.1 データモデル設計 ⭐最優先
**実施順序: 1番目**  
**理由**: 全てのAPIとUIがこれに依存するため最初に決定する必要がある

- [ ] schemas.py の全Pydanticモデル定義
  - [ ] CreateTablesResponse（テーブル作成レスポンス）
  - [ ] GenerateProblemResponse（問題生成レスポンス）  
  - [ ] CheckAnswerRequest（解答チェックリクエスト）
  - [ ] CheckAnswerResponse（解答チェックレスポンス）
  - [ ] TableSchemaResponse（テーブル構造レスポンス）
- [ ] エラーレスポンス形式の統一
  - [ ] エラーコード体系の設計
  - [ ] エラーメッセージフォーマット
- [ ] データ型と制約の決定
  - [ ] 最大行数、カラム数の制限
  - [ ] SQL文字列の最大長

### 1.2 データベース設計
**実施順序: 2番目**  
**理由**: データモデルが決まったら、それを永続化する方法を決める

- [ ] テーブル作成戦略
  - [ ] テーマ別のテーブル定義（社員管理、図書館、ECサイト）
  - [ ] 各テーマのテーブル構造とリレーション
  - [ ] サンプルデータの規模と内容
- [ ] 接続方式の選定
  - [ ] asyncpg vs SQLModel vs psycopg3 の比較検討
  - [ ] 接続プール設定（最大接続数、タイムアウト）
- [ ] models.py（問題管理テーブル）
  - [ ] problems テーブル定義
  - [ ] attempts テーブル定義（将来拡張用）
- [ ] db.py インターフェース設計
  - [ ] DatabaseManager クラスの設計
  - [ ] 各メソッドのシグネチャ定義

---

## フェーズ2: API詳細設計（バックエンド機能）

### 2.1 エンドポイント設計
**実施順序: 3番目**  
**理由**: データモデルとDB設計に基づいてAPI仕様を決定

- [ ] POST /api/create-tables
  - [ ] 処理フロー設計
  - [ ] 既存テーブル削除ロジック
  - [ ] トランザクション管理
- [ ] GET /api/table-schemas
  - [ ] スキーマ情報の取得方法
  - [ ] レスポンスフォーマット
- [ ] POST /api/generate-problem
  - [ ] 難易度調整ロジック
  - [ ] 問題の多様性確保方法
- [ ] POST /api/check-answer
  - [ ] SQL実行と結果比較ロジック
  - [ ] セキュリティ（SELECT文のみ許可）

### 2.2 LLM連携設計  
**実施順序: 4番目**  
**理由**: APIの要件が決まったらLLMプロンプトを設計

- [ ] LocalAI接続設定
  - [ ] APIエンドポイントURL
  - [ ] モデル選定（日本語対応）
  - [ ] タイムアウト設定
- [ ] プロンプト設計
  - [ ] テーブル生成プロンプト
  - [ ] 問題SQL生成プロンプト
  - [ ] 採点・アドバイスプロンプト
- [ ] generative.py の関数設計
  - [ ] call_llm 関数
  - [ ] generate_table_schema 関数
  - [ ] generate_problem_sql 関数
  - [ ] generate_feedback 関数

---

## フェーズ3: フロントエンド設計（UI/UX）

### 3.1 TypeScript型定義
**実施順序: 5番目**  
**理由**: バックエンドのスキーマに合わせて型を定義

- [ ] APIレスポンス型の定義
  - [ ] バックエンドのPydanticモデルと同期
- [ ] コンポーネントProps型
  - [ ] 各コンポーネントの入出力定義
- [ ] 状態管理の型
  - [ ] グローバル状態の型定義

### 3.2 コンポーネント設計
**実施順序: 6番目**  
**理由**: 型定義に基づいてコンポーネントを設計

- [ ] ページ構成
  - [ ] index.tsx の画面レイアウト
  - [ ] 画面遷移フロー
- [ ] 共通コンポーネント
  - [ ] TableDisplay（結果表示）
  - [ ] SqlEditor（SQL入力）
  - [ ] SchemaViewer（テーブル構造表示）
  - [ ] LoadingSpinner
  - [ ] ErrorMessage
- [ ] 状態管理フロー
  - [ ] どの状態をどこで管理するか
  - [ ] API呼び出しのタイミング

---

## フェーズ4: 実装詳細設計

### 4.1 エラーハンドリング・セキュリティ
**実施順序: 7番目**  
**理由**: 全体の処理フローが決まったら例外処理を設計

- [ ] セキュリティ対策
  - [ ] SQLインジェクション対策の実装方法
  - [ ] 実行可能SQL文の正規表現パターン
  - [ ] タイムアウト実装（5秒）
- [ ] エラーハンドリング
  - [ ] 各種エラーケースの洗い出し
  - [ ] ユーザーフレンドリーなメッセージ変換

### 4.2 環境設定
**実施順序: 8番目**  
**理由**: 全ての技術選定が終わったら環境変数を確定

- [ ] .env ファイル設計
  - [ ] 必要な環境変数の洗い出し
  - [ ] デフォルト値の設定
- [ ] requirements.txt 確定
  - [ ] 全ての必要なPythonパッケージ
  - [ ] バージョン固定
- [ ] package.json 確定
  - [ ] 全ての必要なnpmパッケージ
  - [ ] スクリプト定義
- [ ] Dockerfile 最適化
  - [ ] マルチステージビルド
  - [ ] キャッシュ最適化

---

## フェーズ5: 統合設計

### 5.1 起動・初期化フロー
**実施順序: 9番目**  
**理由**: 個別の設計が完了したら統合を設計

- [ ] docker-compose 起動順序
  - [ ] depends_on の設定
  - [ ] ヘルスチェック実装
- [ ] DB初期化処理
  - [ ] 初回起動時の処理
  - [ ] マイグレーション戦略

### 5.2 ログ・モニタリング（オプション）
**実施順序: 10番目**  
**理由**: 基本機能が決まったら運用面を考慮

- [ ] ログフォーマット設計
- [ ] エラー通知の仕組み
- [ ] パフォーマンス計測ポイント

---

## 進捗管理

### 完了フェーズ
- なし（これから開始）

### 現在作業中
- フェーズ1.1: データモデル設計

### 次の作業
- フェーズ1.2: データベース設計

---

## 注意事項
1. 各フェーズの設計書は `docs/design/` 配下の対応するディレクトリに保存
2. 設計書作成時は必ずテンプレート（`docs/design/templates/`）を使用
3. 前のフェーズが完了してから次のフェーズに進む
4. 設計変更が発生した場合は、影響を受ける後続フェーズも更新する