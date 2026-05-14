'use client';

interface RadarPoint { label: string; value: number; color: string }

interface Props {
  points: RadarPoint[];
  size?: number;
}

export function RadarChart({ points, size = 220 }: Props) {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size * 0.38;
  const levels = 4;
  const n = points.length;

  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const coord = (r: number, i: number) => ({
    x: cx + r * Math.cos(angle(i)),
    y: cy + r * Math.sin(angle(i)),
  });

  // grid rings
  const gridRings = Array.from({ length: levels }, (_, l) =>
    Array.from({ length: n }, (_, i) => coord(maxR * ((l + 1) / levels), i))
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
      .join(' ') + ' Z'
  );

  // data polygon
  const dataPath = points
    .map((p, i) => {
      const r = (p.value / 100) * maxR;
      const { x, y } = coord(r, i);
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ') + ' Z';

  const scoreColor = (v: number) =>
    v >= 80 ? '#22c55e' : v >= 60 ? '#3b82f6' : v >= 40 ? '#eab308' : '#ef4444';

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* grid rings */}
      {gridRings.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="#334155" strokeWidth="0.8" />
      ))}

      {/* axes */}
      {points.map((_, i) => {
        const { x, y } = coord(maxR, i);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#334155" strokeWidth="0.8" />;
      })}

      {/* data fill */}
      <path d={dataPath} fill="rgba(59,130,246,0.15)" stroke="#3b82f6" strokeWidth="2" strokeLinejoin="round" />

      {/* data dots */}
      {points.map((p, i) => {
        const r = (p.value / 100) * maxR;
        const { x, y } = coord(r, i);
        return (
          <circle key={i} cx={x} cy={y} r={4} fill={scoreColor(p.value)} stroke="#0f172a" strokeWidth="1.5" />
        );
      })}

      {/* labels */}
      {points.map((p, i) => {
        const labelR = maxR + 18;
        const { x, y } = coord(labelR, i);
        const anchor = x < cx - 4 ? 'end' : x > cx + 4 ? 'start' : 'middle';
        return (
          <g key={i}>
            <text x={x} y={y - 4} textAnchor={anchor} fill="#94a3b8" fontSize="9" fontWeight="500">
              {p.label}
            </text>
            <text x={x} y={y + 8} textAnchor={anchor} fill={scoreColor(p.value)} fontSize="10" fontWeight="700">
              {p.value}
            </text>
          </g>
        );
      })}

      {/* center score */}
      <text x={cx} y={cy + 5} textAnchor="middle" fill="white" fontSize="14" fontWeight="800">
        {Math.round(points.reduce((s, p) => s + p.value, 0) / points.length)}
      </text>
    </svg>
  );
}
