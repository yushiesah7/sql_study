# フロントエンド設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションのフロントエンド設計を定義します。
シンプルで直感的なUIを提供し、ユーザーがSQLの学習に集中できる環境を実現します。

## 設計方針

1. **最小限の機能**: 必要な機能のみに絞る
2. **シンプルなUI**: ボタンと表示エリアのみ
3. **状態管理なし**: APIが全て管理
4. **レスポンシブ対応**: モバイルでも使える
5. **日本語UI**: 全て日本語表記

## 技術スタック

| 技術 | 選定理由 |
|-----|---------|
| Next.js 14 | App Router、TypeScript標準対応 |
| TypeScript | 型安全性 |
| Tailwind CSS | 高速なスタイリング |
| axios | シンプルなAPI通信 |

### 不採用の技術とその理由
- Redux/Zustand: 状態管理が最小限のため不要
- Material-UI: オーバースペック
- React Query: キャッシュ不要（AIが管理）

## ディレクトリ構造

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx         # メインページ（唯一のページ）
│   │   ├── layout.tsx       # レイアウト
│   │   └── globals.css      # グローバルスタイル
│   ├── components/
│   │   ├── Button.tsx       # 共通ボタン
│   │   ├── ResultTable.tsx  # 結果表示テーブル
│   │   ├── SqlEditor.tsx    # SQL入力エリア
│   │   └── SchemaViewer.tsx # テーブル構造表示
│   ├── lib/
│   │   └── api.ts          # API通信関数
│   └── types/
│       └── index.ts        # TypeScript型定義
├── public/              # 静的ファイル
├── package.json
├── tsconfig.json
├── next.config.js
└── tailwind.config.js
```

## 画面構成

### シングルページ構成
```
┌─────────────────────────────────────┐
│          SQL学習アプリ               │ <- ヘッダー
├─────────────────────────────────────┤
│ [テーブル作成] [問題生成]            │ <- アクションボタン
├─────────────────────────────────────┤
│ テーブル構造:                        │
│ ┌─────────────────────────────────┐ │
│ │ employees: id, name, salary...  │ │ <- スキーマ表示
│ │ departments: id, name...        │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 問題の結果:                          │
│ ┌─────────────────────────────────┐ │
│ │ name    | department | salary   │ │ <- 結果テーブル
│ │ 田中    | 営業部     | 350000   │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ あなたの回答:                        │
│ ┌─────────────────────────────────┐ │
│ │ SELECT ...                      │ │ <- SQL入力
│ └─────────────────────────────────┘ │
│             [回答をチェック]          │
├─────────────────────────────────────┤
│ フィードバック:                      │
│ ┌─────────────────────────────────┐ │
│ │ 正解です！よくできました。        │ │ <- 結果表示
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 状態管理

### 最小限の状態（useState のみ）
```typescript
interface PageState {
  // 表示制御
  isLoading: boolean;
  
  // 現在のデータ
  schemas: TableSchema[] | null;
  currentProblem: ProblemData | null;
  userSql: string;
  feedback: FeedbackData | null;
  
  // エラー
  error: string | null;
}
```

### 状態の流れ
1. **初期状態**: 全てnull、ボタンのみ表示
2. **テーブル作成後**: schemasに値、問題生成可能に
3. **問題生成後**: currentProblemに値、SQL入力可能に
4. **回答チェック後**: feedbackに値、次の問題へ

## API通信設計

### lib/api.ts
```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒
});

// エラーハンドリング
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error.message);
    }
    throw new Error('通信エラーが発生しました');
  }
);

export const sqlApi = {
  // テーブル作成
  createTables: async (prompt?: string) => {
    const { data } = await api.post('/api/create-tables', { prompt });
    return data;
  },
  
  // スキーマ取得
  getSchemas: async () => {
    const { data } = await api.get('/api/table-schemas');
    return data;
  },
  
  // 問題生成
  generateProblem: async (prompt?: string) => {
    const { data } = await api.post('/api/generate-problem', { prompt });
    return data;
  },
  
  // 回答チェック
  checkAnswer: async (problemId: number, userSql: string) => {
    const { data } = await api.post('/api/check-answer', {
      context: { problem_id: problemId, user_sql: userSql }
    });
    return data;
  },
};
```

## TypeScript型定義

### types/index.ts
```typescript
// APIレスポンス型（バックエンドと同期）
export interface CreateTablesResponse {
  success: boolean;
  theme: string;
  message?: string;
}

export interface TableSchema {
  table_name: string;
  columns: Array<{
    name: string;
    type: string;
    nullable: boolean;
    is_primary_key: boolean;
    foreign_key?: {
      table: string;
      column: string;
    };
  }>;
}

export interface GenerateProblemResponse {
  problem_id: number;
  result: Array<Record<string, any>>;
  row_count?: number;
  column_names?: string[];
}

export interface CheckAnswerResponse {
  is_correct: boolean;
  message: string;
  user_result?: Array<Record<string, any>>;
  expected_result?: Array<Record<string, any>>;
  hint?: string;
  error_type?: string;
  error_message?: string;
}

// UI用の型
export interface ProblemData extends GenerateProblemResponse {
  displayColumns: string[];
  displayRows: Array<Record<string, any>>;
}

export interface FeedbackData extends CheckAnswerResponse {
  timestamp: Date;
}
```

## エラーハンドリング

### エラーの種類と表示
```typescript
enum ErrorType {
  NETWORK = 'ネットワークエラー',
  NO_TABLES = 'テーブルが作成されていません',
  INVALID_SQL = 'SQLの形式が正しくありません',
  TIMEOUT = 'タイムアウトしました',
  UNKNOWN = '予期しないエラーが発生しました'
}

// エラー表示コンポーネント
const ErrorMessage: React.FC<{ error: string }> = ({ error }) => (
  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
    <p className="text-sm">{error}</p>
  </div>
);
```

## レスポンシブ設計

### ブレークポイント
- モバイル: 〜640px
- タブレット: 641px〜1024px  
- デスクトップ: 1025px〜

### モバイル対応
- ボタンを縦並びに
- テーブルを横スクロール可能に
- SQL入力エリアの高さを調整

## アクセシビリティ

- キーボード操作対応
- 適切なaria-label
- フォーカス管理
- エラーメッセージの適切な通知

## パフォーマンス最適化

### 1. 遅延読み込み不要
- シングルページのため全て初期読み込み

### 2. 最小限の再レンダリング
```typescript
// メモ化は最小限に
const ResultTable = React.memo(({ data }) => {
  // テーブル表示
});
```

### 3. バンドルサイズ削減
- 不要なライブラリを含めない
- Tree shakingを活用

## 開発環境設定

### package.json（主要部分）
```json
{
  "name": "sql-learning-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

## セキュリティ考慮事項

1. **XSS対策**: Reactのデフォルトエスケープに依存
2. **CSRF対策**: 認証なしのため不要
3. **環境変数**: APIエンドポイントのみ
4. **入力検証**: フロントでは最小限、バックエンドで実施

## テスト戦略

MVP段階では手動テストのみ：
1. 各ボタンの動作確認
2. エラー時の表示確認
3. モバイル表示確認

## 実装優先順位

1. **基本レイアウト**（1日）
   - ページ構造
   - ボタン配置

2. **API通信**（1日）
   - 各エンドポイントの実装
   - エラーハンドリング

3. **コンポーネント実装**（2日）
   - ResultTable
   - SqlEditor
   - SchemaViewer

4. **統合・調整**（1日）
   - 全体の動作確認
   - スタイリング調整

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |