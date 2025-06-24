import React, { useState, useCallback } from 'react';
import { 
  Button, 
  SqlEditor, 
  TableDisplay, 
  SchemaViewer, 
  LoadingSpinner, 
  ErrorMessage 
} from '../components';
import { api, ApiError } from '../utils/api';
import { 
  AppState, 
  GenerateProblemResponse, 
  CheckAnswerResponse,
  TableSchema 
} from '../types/api';

export default function Home() {
  const [state, setState] = useState<AppState>({
    tables: [],
    currentProblem: null,
    lastCheckResult: null,
    isLoading: false,
    error: null,
  });

  const [sqlInput, setSqlInput] = useState('');

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const handleCreateTables = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.createTables();
      
      if (response.success) {
        const schemas = await api.getTableSchemas();
        setState(prev => ({
          ...prev,
          tables: schemas.tables,
          currentProblem: null,
          lastCheckResult: null,
          isLoading: false,
        }));
      } else {
        throw new Error(response.message || 'テーブル作成に失敗しました');
      }
    } catch (error) {
      console.error('テーブル作成エラー:', error);
      setError(error instanceof ApiError ? error.message : 'テーブル作成中にエラーが発生しました');
      setLoading(false);
    }
  }, [setLoading, setError]);

  const handleGenerateProblem = useCallback(async () => {
    if (state.tables.length === 0) {
      setError('まずテーブルを作成してください');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await api.generateProblem();
      setState(prev => ({
        ...prev,
        currentProblem: response,
        lastCheckResult: null,
        isLoading: false,
      }));
    } catch (error) {
      console.error('問題生成エラー:', error);
      setError(error instanceof ApiError ? error.message : '問題生成中にエラーが発生しました');
      setLoading(false);
    }
  }, [state.tables.length, setLoading, setError]);

  const handleCheckAnswer = useCallback(async () => {
    if (!state.currentProblem) {
      setError('問題が生成されていません');
      return;
    }

    if (!sqlInput.trim()) {
      setError('SQLを入力してください');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await api.checkAnswer({
        sql: sqlInput,
        problem_id: state.currentProblem.problem_id,
      });
      
      setState(prev => ({
        ...prev,
        lastCheckResult: response,
        isLoading: false,
      }));
    } catch (error) {
      console.error('回答チェックエラー:', error);
      setError(error instanceof ApiError ? error.message : '回答チェック中にエラーが発生しました');
      setLoading(false);
    }
  }, [state.currentProblem, sqlInput, setLoading, setError]);

  const handleNewProblem = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentProblem: null,
      lastCheckResult: null,
    }));
    setSqlInput('');
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            SQL学習アプリケーション
          </h1>
          <p className="text-lg text-gray-600">
            結果から逆算してSQLを考える逆引き型学習
          </p>
        </div>

        {/* エラー表示 */}
        {state.error && (
          <div className="mb-6">
            <ErrorMessage
              message={state.error}
              onDismiss={() => setError(null)}
            />
          </div>
        )}

        {/* 操作パネル */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">操作パネル</h2>
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={handleCreateTables}
              loading={state.isLoading}
              disabled={state.isLoading}
            >
              テーブル作成
            </Button>
            
            <Button
              onClick={handleGenerateProblem}
              variant="secondary"
              loading={state.isLoading}
              disabled={state.isLoading || state.tables.length === 0}
            >
              問題生成
            </Button>
            
            {state.currentProblem && (
              <Button
                onClick={handleNewProblem}
                variant="secondary"
                disabled={state.isLoading}
              >
                新しい問題
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左側: テーブル構造とSQL入力 */}
          <div className="space-y-6">
            {/* テーブル構造 */}
            <SchemaViewer schemas={state.tables} />
            
            {/* SQL入力エリア */}
            {state.currentProblem && (
              <div className="card">
                <SqlEditor
                  value={sqlInput}
                  onChange={setSqlInput}
                  disabled={state.isLoading}
                />
                <div className="mt-4">
                  <Button
                    onClick={handleCheckAnswer}
                    loading={state.isLoading}
                    disabled={state.isLoading || !sqlInput.trim()}
                    className="w-full sm:w-auto"
                  >
                    回答をチェック
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* 右側: 問題と結果 */}
          <div className="space-y-6">
            {/* 問題表示 */}
            {state.currentProblem && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  問題 #{state.currentProblem.problem_id}
                </h3>
                <div className="mb-4">
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                    state.currentProblem.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                    state.currentProblem.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {state.currentProblem.difficulty === 'easy' ? '簡単' :
                     state.currentProblem.difficulty === 'medium' ? '普通' : '難しい'}
                  </span>
                </div>
                <p className="text-gray-700 mb-4">
                  以下の結果を出力するSQLを作成してください：
                </p>
                <TableDisplay 
                  data={state.currentProblem.expected_result}
                  title="期待される結果"
                />
                {state.currentProblem.hint && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>ヒント:</strong> {state.currentProblem.hint}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ローディング表示 */}
            {state.isLoading && (
              <div className="card">
                <LoadingSpinner 
                  size="lg" 
                  text="処理中..." 
                  className="py-8"
                />
              </div>
            )}

            {/* 回答結果表示 */}
            {state.lastCheckResult && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  判定結果
                </h3>
                
                <div className={`p-4 rounded-md mb-4 ${
                  state.lastCheckResult.is_correct 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className={`flex items-center mb-2 ${
                    state.lastCheckResult.is_correct ? 'text-green-800' : 'text-red-800'
                  }`}>
                    <div className={`w-4 h-4 rounded-full mr-2 ${
                      state.lastCheckResult.is_correct ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="font-medium">
                      {state.lastCheckResult.is_correct ? '正解！' : '不正解'}
                    </span>
                  </div>
                  <p className={state.lastCheckResult.is_correct ? 'text-green-700' : 'text-red-700'}>
                    {state.lastCheckResult.message}
                  </p>
                </div>

                {state.lastCheckResult.user_result && (
                  <div className="mb-4">
                    <TableDisplay 
                      data={state.lastCheckResult.user_result}
                      title="あなたのSQL実行結果"
                    />
                  </div>
                )}

                {state.lastCheckResult.error_message && (
                  <div className="mb-4 p-3 bg-red-50 rounded-md">
                    <p className="text-sm text-red-800">
                      <strong>エラー:</strong> {state.lastCheckResult.error_message}
                    </p>
                  </div>
                )}

                {state.lastCheckResult.hint && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-800">
                      <strong>アドバイス:</strong> {state.lastCheckResult.hint}
                    </p>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  実行時間: {state.lastCheckResult.execution_time.toFixed(3)}秒
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 使い方説明 */}
        {state.tables.length === 0 && !state.isLoading && (
          <div className="card mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              使い方
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>「テーブル作成」ボタンを押してランダムなテーマでテーブルを作成</li>
              <li>「問題生成」ボタンを押して、AIが作成した問題を取得</li>
              <li>期待される結果を見て、同じ結果を出力するSQLを考える</li>
              <li>SQL入力エリアにSELECT文を入力</li>
              <li>「回答をチェック」ボタンで正誤判定を受ける</li>
              <li>間違いの場合はヒントを参考に再挑戦</li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}