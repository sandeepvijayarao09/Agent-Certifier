import { clsx } from 'clsx';
import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-slate-900 border border-slate-700/50 rounded-xl p-6',
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: CardProps) {
  return (
    <div className={clsx('mb-4', className)}>{children}</div>
  );
}

export function CardTitle({ children, className }: CardProps) {
  return (
    <h3 className={clsx('text-lg font-semibold text-slate-100', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className }: CardProps) {
  return <div className={clsx('', className)}>{children}</div>;
}
