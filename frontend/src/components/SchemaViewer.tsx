import React from 'react';
import { clsx } from 'clsx';
import { TableSchema } from '../types/api';

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
        <p className="text-sm mt-1">まず「テーブル作成」ボタンを押してください</p>
      </div>
    );
  }

  return (
    <div className={clsx('card', className)}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">テーブル構造</h3>
      
      <div className="space-y-6">
        {schemas.map((table, tableIndex) => (
          <div key={tableIndex} className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <span className="bg-primary-100 text-primary-800 px-2 py-1 rounded text-sm mr-2">
                テーブル
              </span>
              {table.table_name}
            </h4>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      カラム名
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      データ型
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      NULL許可
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
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
                        <span className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
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
                          <span className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">
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
                <h5 className="text-sm font-medium text-gray-700 mb-2">サンプルデータ（上位3行）</h5>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50">
                        {table.columns.map((column) => (
                          <th key={column.column_name} className="px-2 py-1 text-left text-gray-500">
                            {column.column_name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {table.sample_data.slice(0, 3).map((row, rowIndex) => (
                        <tr key={rowIndex} className="border-t border-gray-200">
                          {table.columns.map((column) => (
                            <td key={column.column_name} className="px-2 py-1 text-gray-700">
                              {row[column.column_name] === null || row[column.column_name] === undefined
                                ? <span className="text-gray-400 italic">NULL</span>
                                : String(row[column.column_name])
                              }
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
      
      <div className="mt-4 text-sm text-gray-500 text-center">
        {schemas.length}個のテーブル
      </div>
    </div>
  );
};