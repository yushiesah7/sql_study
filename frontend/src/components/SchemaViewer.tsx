import React from 'react';
import { clsx } from 'clsx';
import { type TableSchema } from '../types/api';

interface SchemaViewerProps {
  schemas: TableSchema[];
  className?: string;
}

export const SchemaViewer: React.FC<SchemaViewerProps> = ({
  schemas,
  className,
}) => {
  if (!schemas || schemas.length === 0) {
    return (
      <div className={clsx('card text-center text-gray-500', className)}>
        <p>テーブルスキーマがありません</p>
        <p className="mt-1 text-sm">
          まず「テーブル作成」ボタンを押してください
        </p>
      </div>
    );
  }

  return (
    <div className={clsx('card', className)}>
      <h3 className="mb-4 text-lg font-medium text-gray-900">テーブル構造</h3>

      <div className="space-y-6">
        {schemas.map((table, tableIndex) => (
          <div
            key={tableIndex}
            className="rounded-lg border border-gray-200 p-4"
          >
            <h4 className="mb-3 flex items-center font-medium text-gray-900">
              <span className="bg-primary-100 text-primary-800 mr-2 rounded px-2 py-1 text-sm">
                テーブル
              </span>
              {table.table_name}
            </h4>

            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      カラム名
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      データ型
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      NULL許可
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      デフォルト値
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {table.columns.map((column, colIndex) => (
                    <tr key={colIndex} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-sm font-medium text-gray-900">
                        {column.column_name}
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700">
                        <span className="rounded bg-gray-100 px-2 py-1 font-mono text-xs">
                          {column.data_type}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700">
                        {column.is_nullable ? (
                          <span className="text-green-600">Yes</span>
                        ) : (
                          <span className="text-red-600">No</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700">
                        {column.column_default ? (
                          <span className="rounded bg-gray-100 px-1 py-0.5 font-mono text-xs">
                            {column.column_default}
                          </span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {table.sample_data && table.sample_data.length > 0 && (
              <div className="mt-4">
                <h5 className="mb-2 text-sm font-medium text-gray-700">
                  サンプルデータ（上位3行）
                </h5>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50">
                        {table.columns.map((column) => (
                          <th
                            key={column.column_name}
                            className="px-2 py-1 text-left text-gray-500"
                          >
                            {column.column_name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {table.sample_data.slice(0, 3).map((row, rowIndex) => (
                        <tr key={rowIndex} className="border-t border-gray-200">
                          {table.columns.map((column) => (
                            <td
                              key={column.column_name}
                              className="px-2 py-1 text-gray-700"
                            >
                              {row[column.column_name] === null ||
                              row[column.column_name] === undefined ? (
                                <span className="italic text-gray-400">
                                  NULL
                                </span>
                              ) : (
                                String(row[column.column_name])
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 text-center text-sm text-gray-500">
        {schemas.length}個のテーブル
      </div>
    </div>
  );
};
