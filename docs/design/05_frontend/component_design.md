# コンポーネント設計書: SQL学習アプリケーション

## 概要
このドキュメントでは、SQL学習アプリケーションの各コンポーネントの詳細設計と実装例を定義します。
シンプルで再利用可能なコンポーネント設計を目指します。

## コンポーネント一覧

| コンポーネント | 用途 | Props |
|-------------|------|-------|
| Button | 汎用ボタン | onClick, children, variant, loading |
| ResultTable | 結果表示テーブル | data, columns |
| SqlEditor | SQL入力エリア | value, onChange, onExecute |
| SchemaViewer | テーブル構造表示 | schemas |
| LoadingSpinner | ローディング表示 | size |
| ErrorMessage | エラー表示 | error |

---

## 1. メインページ (app/page.tsx)

### 設計
シングルページアプリケーションのメインコンポーネント

### 実装例
```tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/Button';
import { ResultTable } from '@/components/ResultTable';
import { SqlEditor } from '@/components/SqlEditor';
import { SchemaViewer } from '@/components/SchemaViewer';
import { ErrorMessage } from '@/components/ErrorMessage';
import { sqlApi } from '@/lib/api';
import type { 
  TableSchema, 
  ProblemData, 
  FeedbackData 
} from '@/types';

export default function Home() {
  // 状態管理
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<TableSchema[] | null>(null);
  const [currentProblem, setCurrentProblem] = useState<ProblemData | null>(null);
  const [userSql, setUserSql] = useState('');
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);

  // テーブル作成
  const handleCreateTables = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await sqlApi.createTables();
      if (result.success) {
        const schemasData = await sqlApi.getSchemas();
        setSchemas(schemasData.schemas);
        // リセット
        setCurrentProblem(null);
        setUserSql('');
        setFeedback(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  // 問題生成
  const handleGenerateProblem = async () => {
    if (!schemas) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const problem = await sqlApi.generateProblem();
      setCurrentProblem({
        ...problem,
        displayColumns: problem.column_names || Object.keys(problem.result[0] || {}),
        displayRows: problem.result
      });
      setUserSql('');
      setFeedback(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  // 回答チェック
  const handleCheckAnswer = async () => {
    if (!currentProblem || !userSql.trim()) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const result = await sqlApi.checkAnswer(currentProblem.problem_id, userSql);
      setFeedback({
        ...result,
        timestamp: new Date()
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* ヘッダー */}
        <h1 className="text-3xl font-bold text-center mb-8">
          SQL学習アプリ
        </h1>

        {/* エラー表示 */}
        {error && (
          <div className="mb-4">
            <ErrorMessage error={error} />
          </div>
        )}

        {/* アクションボタン */}
        <div className="flex gap-4 mb-8 flex-wrap">
          <Button 
            onClick={handleCreateTables}
            loading={isLoading}
          >
            テーブルとデータ作成
          </Button>
          <Button 
            onClick={handleGenerateProblem}
            disabled={!schemas}
            loading={isLoading}
            variant="secondary"
          >
            問題作成
          </Button>
        </div>

        {/* テーブル構造表示 */}
        {schemas && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">テーブル構造</h2>
            <SchemaViewer schemas={schemas} />
          </div>
        )}

        {/* 問題の結果表示 */}
        {currentProblem && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">
              期待される結果（{currentProblem.row_count}行）
            </h2>
            <ResultTable 
              data={currentProblem.displayRows}
              columns={currentProblem.displayColumns}
            />
          </div>
        )}

        {/* SQL入力エリア */}
        {currentProblem && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">あなたの回答</h2>
            <SqlEditor
              value={userSql}
              onChange={setUserSql}
              onExecute={handleCheckAnswer}
            />
            <div className="mt-4 text-right">
              <Button 
                onClick={handleCheckAnswer}
                disabled={!userSql.trim()}
                loading={isLoading}
                variant="primary"
              >
                回答をチェック
              </Button>
            </div>
          </div>
        )}

        {/* フィードバック表示 */}
        {feedback && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">フィードバック</h2>
            <div className={`p-6 rounded-lg ${
              feedback.is_correct 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-yellow-50 border border-yellow-200'
            }`}>
              <p className="text-lg font-medium mb-2">
                {feedback.is_correct ? '🎉 正解！' : '🤔 もう少し！'}
              </p>
              <p className="mb-4">{feedback.message}</p>
              {feedback.hint && (
                <p className="text-sm text-gray-600">
                  ヒント: {feedback.hint}
                </p>
              )}
            </div>
            
            {/* ユーザーの結果（不正解時） */}
            {!feedback.is_correct && feedback.user_result && (
              <div className="mt-4">
                <h3 className="font-medium mb-2">あなたの結果:</h3>
                <ResultTable 
                  data={feedback.user_result}
                  columns={Object.keys(feedback.user_result[0] || {})}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 2. Button コンポーネント

### 設計
汎用的なボタンコンポーネント

### 実装例 (components/Button.tsx)
```tsx
import { ButtonHTMLAttributes, FC } from 'react';
import { LoadingSpinner } from './LoadingSpinner';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
}

export const Button: FC<ButtonProps> = ({
  children,
  variant = 'primary',
  loading = false,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500 disabled:bg-gray-100',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-300'
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <LoadingSpinner size="sm" />
          <span>処理中...</span>
        </span>
      ) : (
        children
      )}
    </button>
  );
};
```

---

## 3. ResultTable コンポーネント

### 設計
SQL実行結果を表示するテーブルコンポーネント

### 実装例 (components/ResultTable.tsx)
```tsx
import { FC } from 'react';

interface ResultTableProps {
  data: Array<Record<string, any>>;
  columns?: string[];
}

export const ResultTable: FC<ResultTableProps> = ({ data, columns }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        データがありません
      </div>
    );
  }

  // カラム名の決定
  const displayColumns = columns || Object.keys(data[0]);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200">
        <thead>
          <tr className="bg-gray-50">
            {displayColumns.map((col) => (
              <th
                key={col}
                className="px-4 py-2 border-b border-gray-200 text-left text-sm font-medium text-gray-700"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {displayColumns.map((col) => (
                <td
                  key={col}
                  className="px-4 py-2 border-b border-gray-200 text-sm text-gray-900"
                >
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// 値のフォーマット
function formatValue(value: any): string {
  if (value === null) return 'NULL';
  if (value === undefined) return '';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
```

---

## 4. SqlEditor コンポーネント

### 設計
SQL入力用のテキストエディタコンポーネント

### 実装例 (components/SqlEditor.tsx)
```tsx
import { FC, KeyboardEvent } from 'react';

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
  placeholder?: string;
}

export const SqlEditor: FC<SqlEditorProps> = ({
  value,
  onChange,
  onExecute,
  placeholder = 'SELECT文を入力してください...'
}) => {
  // Ctrl+Enter で実行
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === 'Enter' && onExecute) {
      e.preventDefault();
      onExecute();
    }
  };

  return (
    <div className="relative">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full h-48 p-4 font-mono text-sm bg-gray-900 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        spellCheck={false}
      />
      <div className="absolute bottom-2 right-2 text-xs text-gray-500">
        Ctrl+Enter で実行
      </div>
    </div>
  );
};
```

---

## 5. SchemaViewer コンポーネント

### 設計
テーブル構造を見やすく表示するコンポーネント

### 実装例 (components/SchemaViewer.tsx)
```tsx
import { FC } from 'react';
import type { TableSchema } from '@/types';

interface SchemaViewerProps {
  schemas: TableSchema[];
}

export const SchemaViewer: FC<SchemaViewerProps> = ({ schemas }) => {
  return (
    <div className="bg-gray-100 rounded-lg p-4 space-y-4">
      {schemas.map((table) => (
        <div key={table.table_name} className="bg-white rounded p-4">
          <h3 className="font-bold text-lg mb-2">
            📋 {table.table_name}
          </h3>
          <div className="space-y-1 text-sm">
            {table.columns.map((col) => (
              <div key={col.name} className="flex items-center gap-2">
                <span className="font-mono">
                  {col.is_primary_key && '🔑'}
                </span>
                <span className="font-mono text-gray-700">
                  {col.name}
                </span>
                <span className="text-gray-500">
                  ({col.type})
                </span>
                {!col.nullable && (
                  <span className="text-xs bg-yellow-100 px-1 rounded">
                    NOT NULL
                  </span>
                )}
                {col.foreign_key && (
                  <span className="text-xs bg-blue-100 px-1 rounded">
                    → {col.foreign_key.table}.{col.foreign_key.column}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 6. LoadingSpinner コンポーネント

### 設計
ローディング状態を表示するスピナー

### 実装例 (components/LoadingSpinner.tsx)
```tsx
import { FC } from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: FC<LoadingSpinnerProps> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="inline-block">
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`}
      />
    </div>
  );
};
```

---

## 7. ErrorMessage コンポーネント

### 設計
エラーメッセージを表示するコンポーネント

### 実装例 (components/ErrorMessage.tsx)
```tsx
import { FC } from 'react';

interface ErrorMessageProps {
  error: string;
  onClose?: () => void;
}

export const ErrorMessage: FC<ErrorMessageProps> = ({ error, onClose }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start justify-between">
      <div className="flex items-start gap-3">
        <span className="text-red-500 text-xl">⚠️</span>
        <p className="text-red-700 text-sm">{error}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="text-red-500 hover:text-red-700"
        >
          ✕
        </button>
      )}
    </div>
  );
};
```

---

## スタイリング設計

### Tailwind CSS設定 (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['Consolas', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

### グローバルスタイル (app/globals.css)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply text-gray-900 antialiased;
  }
}

@layer components {
  /* カスタムスクロールバー */
  .custom-scrollbar::-webkit-scrollbar {
    @apply w-2 h-2;
  }
  
  .custom-scrollbar::-webkit-scrollbar-track {
    @apply bg-gray-100 rounded;
  }
  
  .custom-scrollbar::-webkit-scrollbar-thumb {
    @apply bg-gray-400 rounded hover:bg-gray-500;
  }
}
```

## レスポンシブ対応

### モバイル最適化のポイント
1. **ボタンの配置**: フレックスボックスでwrap
2. **テーブル**: 横スクロール可能
3. **SQL入力**: 高さを調整
4. **フォントサイズ**: 読みやすさを維持

```tsx
// レスポンシブ対応の例
<div className="flex gap-4 mb-8 flex-wrap">
  {/* モバイルでは縦並びに */}
</div>

<div className="overflow-x-auto">
  {/* テーブルは横スクロール */}
</div>
```

## アニメーション

### 基本的なトランジション
```css
/* ボタンホバー */
.transition-colors

/* フェードイン */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
```

## 変更履歴

| 日付 | バージョン | 変更内容 | 変更者 |
|-----|-----------|---------|--------|
| 2024-12-22 | 1.0.0 | 初版作成 | - |