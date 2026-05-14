import { clsx } from 'clsx';

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  colorClass?: string;
}

export function Progress({ value, max = 100, className, colorClass }: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const defaultColor =
    pct >= 80
      ? 'bg-green-500'
      : pct >= 60
      ? 'bg-blue-500'
      : pct >= 40
      ? 'bg-yellow-500'
      : 'bg-red-500';

  return (
    <div
      className={clsx('h-2 bg-slate-700 rounded-full overflow-hidden', className)}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <div
        className={clsx('h-full rounded-full transition-all duration-500', colorClass || defaultColor)}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
