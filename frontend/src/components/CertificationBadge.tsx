import { clsx } from 'clsx';
import type { CertificationLevel } from '@/lib/types';

interface CertificationBadgeProps {
  level: CertificationLevel | null;
  size?: 'sm' | 'md' | 'lg';
  showDescription?: boolean;
}

const levelConfig: Record<CertificationLevel, { label: string; color: string; bg: string; border: string; description: string; emoji: string }> = {
  PLATINUM: {
    label: 'Platinum',
    color: 'text-purple-300',
    bg: 'bg-purple-900/30',
    border: 'border-purple-500/50',
    description: 'Exceptional quality — 90+ score',
    emoji: '💎',
  },
  GOLD: {
    label: 'Gold',
    color: 'text-yellow-300',
    bg: 'bg-yellow-900/30',
    border: 'border-yellow-500/50',
    description: 'High quality — 80+ score',
    emoji: '🥇',
  },
  SILVER: {
    label: 'Silver',
    color: 'text-slate-300',
    bg: 'bg-slate-700/30',
    border: 'border-slate-400/50',
    description: 'Good quality — 70+ score',
    emoji: '🥈',
  },
  BRONZE: {
    label: 'Bronze',
    color: 'text-orange-300',
    bg: 'bg-orange-900/30',
    border: 'border-orange-500/50',
    description: 'Acceptable quality — 60+ score',
    emoji: '🥉',
  },
  NOT_CERTIFIED: {
    label: 'Not Certified',
    color: 'text-red-300',
    bg: 'bg-red-900/30',
    border: 'border-red-500/50',
    description: 'Below threshold — <60 score',
    emoji: '✗',
  },
};

const sizeClasses = {
  sm: { wrapper: 'px-2 py-1', text: 'text-xs', emoji: 'text-sm' },
  md: { wrapper: 'px-3 py-1.5', text: 'text-sm', emoji: 'text-base' },
  lg: { wrapper: 'px-4 py-2', text: 'text-base', emoji: 'text-xl' },
};

export function CertificationBadge({ level, size = 'md', showDescription = false }: CertificationBadgeProps) {
  if (!level) {
    return (
      <span className="px-2 py-1 rounded-full text-xs bg-slate-800 text-slate-500 border border-slate-700">
        Pending
      </span>
    );
  }

  const config = levelConfig[level];
  const sizes = sizeClasses[size];

  return (
    <div className="flex flex-col items-start gap-0.5">
      <span
        className={clsx(
          'inline-flex items-center gap-1.5 rounded-full font-semibold border',
          config.bg,
          config.color,
          config.border,
          sizes.wrapper,
          sizes.text
        )}
      >
        <span className={sizes.emoji}>{config.emoji}</span>
        {config.label}
      </span>
      {showDescription && (
        <span className="text-xs text-slate-500 ml-1">{config.description}</span>
      )}
    </div>
  );
}
