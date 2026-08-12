import { clsx } from 'clsx';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary';
  className?: string;
}

const variantClasses = {
  default: 'bg-slate-700 text-slate-200',
  success: 'bg-green-900/50 text-green-300 border border-green-700/50',
  warning: 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50',
  danger: 'bg-red-900/50 text-red-300 border border-red-700/50',
  info: 'bg-blue-900/50 text-blue-300 border border-blue-700/50',
  secondary: 'bg-slate-800 text-slate-300',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
