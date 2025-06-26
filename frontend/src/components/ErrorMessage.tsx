import React from 'react';
import { clsx } from 'clsx';
import { AlertCircle, X } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  title?: string;
  onDismiss?: () => void;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  title,
  onDismiss,
  variant = 'error',
  className,
}) => {
  const variantClasses = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const iconClasses = {
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  };

  return (
    <div
      className={clsx(
        'rounded-md border p-4',
        variantClasses[variant],
        className,
      )}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className={clsx('h-5 w-5', iconClasses[variant])} />
        </div>
        <div className="ml-3 flex-1">
          {title && <h3 className="mb-1 text-sm font-medium">{title}</h3>}
          <div className="text-sm">
            <p>{message}</p>
          </div>
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                onClick={onDismiss}
                className={clsx(
                  'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                  variant === 'error' &&
                    'text-red-500 hover:bg-red-100 focus:ring-red-600',
                  variant === 'warning' &&
                    'text-yellow-500 hover:bg-yellow-100 focus:ring-yellow-600',
                  variant === 'info' &&
                    'text-blue-500 hover:bg-blue-100 focus:ring-blue-600',
                )}
              >
                <span className="sr-only">閉じる</span>
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
