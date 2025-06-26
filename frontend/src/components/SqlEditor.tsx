import React, { useState } from 'react';
import { clsx } from 'clsx';

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  className?: string;
}

export const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  placeholder = 'SELECT文を入力してください...',
  disabled = false,
  error,
  className,
}) => {
  const [focused, setFocused] = useState(false);

  return (
    <div className={clsx('relative', className)}>
      <label className="mb-2 block text-sm font-medium text-gray-700">
        SQL入力
      </label>
      <div
        className={clsx(
          'relative overflow-hidden rounded-md border transition-colors',
          focused
            ? 'border-primary-500 ring-1 ring-primary-500'
            : 'border-gray-300',
          error ? 'border-red-500 ring-1 ring-red-500' : '',
          disabled ? 'bg-gray-50' : 'bg-white',
        )}
      >
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className={clsx(
            'w-full resize-none p-3 font-mono text-sm focus:outline-none',
            'max-h-[300px] min-h-[120px]',
            disabled ? 'bg-gray-50 text-gray-500' : 'bg-white text-gray-900',
          )}
          rows={6}
        />
        <div className="absolute bottom-2 right-2 text-xs text-gray-400">
          {value.length} 文字
        </div>
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      <div className="mt-2 text-xs text-gray-500">
        SELECT文のみ実行可能です。INSERT、UPDATE、DELETEは使用できません。
      </div>
    </div>
  );
};
