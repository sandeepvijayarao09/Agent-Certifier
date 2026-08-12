'use client';

interface Bar { label: string; value: number; color?: string; maxValue?: number }

interface Props {
  bars: Bar[];
  height?: number;
  showValues?: boolean;
  horizontal?: boolean;
}

function scoreColor(v: number, max = 100) {
  const pct = (v / max) * 100;
  if (pct >= 80) return '#22c55e';
  if (pct >= 60) return '#3b82f6';
  if (pct >= 40) return '#eab308';
  return '#ef4444';
}

export function HorizontalBars({ bars, showValues = true }: { bars: Bar[]; showValues?: boolean }) {
  const max = Math.max(...bars.map(b => b.maxValue ?? b.value), 1);
  return (
    <div className="space-y-2.5">
      {bars.map((bar, i) => {
        const pct = Math.min((bar.value / max) * 100, 100);
        const color = bar.color ?? scoreColor(bar.value, max);
        return (
          <div key={i} className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-24 truncate shrink-0 text-right">{bar.label}</span>
            <div className="flex-1 h-5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 flex items-center justify-end pr-2"
                style={{ width: `${pct}%`, backgroundColor: color, minWidth: pct > 5 ? undefined : '0' }}
              />
            </div>
            {showValues && (
              <span className="text-xs font-bold tabular-nums w-8 text-right" style={{ color }}>
                {typeof bar.value === 'number' && bar.value % 1 === 0 ? bar.value : bar.value.toFixed(1)}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ColumnChart({ bars, height = 120 }: { bars: Bar[]; height?: number }) {
  const max = Math.max(...bars.map(b => b.value), 1);
  return (
    <div className="flex items-end gap-1.5" style={{ height }}>
      {bars.map((bar, i) => {
        const pct = (bar.value / max) * 100;
        const color = bar.color ?? '#3b82f6';
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
            <div className="relative w-full flex flex-col justify-end" style={{ height: height - 24 }}>
              <div
                className="w-full rounded-t-sm transition-all duration-700"
                style={{ height: `${pct}%`, backgroundColor: color, minHeight: bar.value > 0 ? 2 : 0 }}
                title={`${bar.label}: ${bar.value}`}
              />
            </div>
            <span className="text-[9px] text-slate-500 truncate w-full text-center">{bar.label}</span>
          </div>
        );
      })}
    </div>
  );
}

export function DonutChart({ segments, size = 100 }: {
  segments: Array<{ label: string; value: number; color: string }>;
  size?: number;
}) {
  const total = segments.reduce((s, seg) => s + seg.value, 0);
  if (total === 0) return (
    <svg width={size} height={size}>
      <circle cx={size/2} cy={size/2} r={size*0.38} fill="none" stroke="#1e293b" strokeWidth={size*0.18} />
    </svg>
  );

  const r = size * 0.38;
  const circumference = 2 * Math.PI * r;
  let offset = 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
      {segments.map((seg, i) => {
        const dash = (seg.value / total) * circumference;
        const gap = circumference - dash;
        const el = (
          <circle
            key={i}
            cx={size / 2} cy={size / 2} r={r}
            fill="none"
            stroke={seg.color}
            strokeWidth={size * 0.18}
            strokeDasharray={`${dash} ${gap}`}
            strokeDashoffset={-offset}
          />
        );
        offset += dash;
        return el;
      })}
    </svg>
  );
}
