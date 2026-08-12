'use client';

interface ScoreGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

function getColor(score: number): string {
  if (score >= 90) return '#a78bfa'; // Platinum - purple
  if (score >= 80) return '#fbbf24'; // Gold
  if (score >= 70) return '#94a3b8'; // Silver
  if (score >= 60) return '#cd7c2e'; // Bronze
  return '#ef4444'; // Fail - red
}

function getTextColor(score: number): string {
  if (score >= 90) return 'text-purple-400';
  if (score >= 80) return 'text-yellow-400';
  if (score >= 70) return 'text-slate-300';
  if (score >= 60) return 'text-orange-400';
  return 'text-red-400';
}

export function ScoreGauge({ score, size = 'md', showLabel = true }: ScoreGaugeProps) {
  const sizeMap = { sm: 80, md: 120, lg: 160 };
  const dim = sizeMap[size];
  const radius = (dim / 2) - 8;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const dashOffset = circumference - (progress / 100) * circumference;
  const color = getColor(score);
  const textColor = getTextColor(score);
  const fontSize = size === 'sm' ? 16 : size === 'md' ? 22 : 32;
  const subFontSize = size === 'sm' ? 8 : 10;

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={dim} height={dim} viewBox={`0 0 ${dim} ${dim}`} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke="#1e293b"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        {/* Score text - rotated back to normal */}
        <text
          x={dim / 2}
          y={dim / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={color}
          fontSize={fontSize}
          fontWeight="bold"
          style={{ transform: `rotate(90deg)`, transformOrigin: `${dim / 2}px ${dim / 2}px` }}
        >
          {Math.round(score)}
        </text>
        {size !== 'sm' && (
          <text
            x={dim / 2}
            y={dim / 2 + fontSize / 2 + 4}
            textAnchor="middle"
            fill="#94a3b8"
            fontSize={subFontSize}
            style={{ transform: `rotate(90deg)`, transformOrigin: `${dim / 2}px ${dim / 2}px` }}
          >
            /100
          </text>
        )}
      </svg>
      {showLabel && (
        <span className={`text-xs font-medium ${textColor}`}>
          Score
        </span>
      )}
    </div>
  );
}
