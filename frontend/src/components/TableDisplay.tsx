import React from 'react';
import { clsx } from 'clsx';

interface TableDisplayProps {
  data: Record<string, unknown>[];
  title?: string;
  className?: string;
  maxRows?: number;
}

export const TableDisplay: React.FC<TableDisplayProps> = ({
  data,
  title,
  className,
  maxRows = 100,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className={clsx('card text-center text-gray-500', className)}>
        <p>データがありません</p>
      </div>
    );
  }

  const columns = Array.from(new Set(data.flatMap((row) => Object.keys(row))));
  const displayData = data.slice(0, maxRows);
  const hasMoreRows = data.length > maxRows;

  return (
    <div className={clsx('card', className)}>
      {title && (
        <h3 className="mb-4 text-lg font-medium text-gray-900">{title}</h3>
      )}

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column} className="px-4 py-2">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, index) => (
              <tr
                // indexをキーとして使用: SQL結果の表示専用で行の並び替えやアニメーションがないため
                key={index}
                className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
              >
                {columns.map((column) => (
                  <td key={column} className="px-4 py-2">
                    <span className="text-sm">
                      {row[column] === null || row[column] === undefined ? (
                        <span className="italic text-gray-400">NULL</span>
                      ) : (
                        String(row[column])
                      )}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {hasMoreRows && (
        <div className="mt-4 text-center text-sm text-gray-500">
          {data.length}行中{maxRows}行を表示
        </div>
      )}

      <div className="mt-2 text-right text-xs text-gray-400">
        {data.length}行 × {columns.length}列
      </div>
    </div>
  );
};
