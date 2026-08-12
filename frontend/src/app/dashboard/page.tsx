'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Shield, RefreshCw, Trash2, Eye, ArrowLeft, Upload,
  LayoutDashboard, BarChart3, Users, Activity,
  TrendingUp, Award, AlertTriangle, Loader2, CheckCircle,
  XCircle, Clock, Zap, Scale, Heart, Code2, Play,
  ChevronRight, FileText,
} from 'lucide-react';
import { CertificationBadge } from '@/components/CertificationBadge';
import { ScoreGauge } from '@/components/ScoreGauge';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { HorizontalBars, ColumnChart, DonutChart } from '@/components/charts/BarChart';
import { RadarChart } from '@/components/charts/RadarChart';
import { api } from '@/lib/api';
import type { Agent, AgentStatus, PlatformStats } from '@/lib/types';

/* ─── constants ──────────────────────────────────────────── */

type View = 'overview' | 'agents' | 'analytics' | 'activity';

const STATUS_BADGE: Record<AgentStatus, { variant: 'success' | 'warning' | 'danger' | 'info' | 'secondary'; label: string }> = {
  pending: { variant: 'secondary', label: 'Pending' },
  running: { variant: 'info', label: 'Running' },
  completed: { variant: 'success', label: 'Completed' },
  failed: { variant: 'danger', label: 'Failed' },
};

const LANG_ICONS: Record<string, string> = {
  Python: '🐍', JavaScript: '🟨', TypeScript: '🔷', Go: '🔵',
  Java: '☕', Ruby: '💎', Rust: '🦀', 'C++': '⚙️', 'C#': '💜', PHP: '🐘',
};

const CAT_ICONS: Record<string, React.ElementType> = {
  security: Shield, stability: Zap, performance: TrendingUp,
  informatics: Code2, compliance: Scale, ethics: Heart,
};
const CAT_COLORS: Record<string, string> = {
  security: '#ef4444', stability: '#3b82f6', performance: '#22c55e',
  informatics: '#a855f7', compliance: '#eab308', ethics: '#ec4899',
};
const CERT_COLORS: Record<string, string> = {
  PLATINUM: '#a78bfa', GOLD: '#fbbf24', SILVER: '#94a3b8',
  BRONZE: '#f97316', NOT_CERTIFIED: '#ef4444',
};

const CATEGORIES = ['security', 'stability', 'performance', 'informatics', 'compliance', 'ethics'];

/* ─── sub-components ─────────────────────────────────────── */

function StatCard({
  label, value, sub, icon: Icon, color, trend,
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color: string; trend?: number;
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-lg" style={{ background: `${color}20` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-medium ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="text-3xl font-black text-white mb-0.5">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
      {sub && <div className="text-xs text-slate-600 mt-1">{sub}</div>}
    </div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-base font-bold text-slate-100">{title}</h2>
      {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
    </div>
  );
}

/* ─── views ──────────────────────────────────────────────── */

function OverviewView({ stats, agents, onRefresh }: {
  stats: PlatformStats | null; agents: Agent[]; onRefresh: () => void;
}) {
  if (!stats) return (
    <div className="flex items-center justify-center py-24">
      <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
    </div>
  );
  const router = useRouter();

  const certEntries = Object.entries(stats.certification_distribution) as [string, number][];
  const certTotal = certEntries.reduce((s, [, v]) => s + v, 0);

  const radarPoints = CATEGORIES.map(cat => ({
    label: cat.charAt(0).toUpperCase() + cat.slice(1),
    value: Math.round(stats.category_averages[cat] ?? 0),
    color: CAT_COLORS[cat],
  }));

  const langBars = Object.entries(stats.language_distribution).map(([lang, count]) => ({
    label: `${LANG_ICONS[lang] ?? '📄'} ${lang}`,
    value: count,
    maxValue: Math.max(...Object.values(stats.language_distribution)),
    color: '#3b82f6',
  }));

  const catBars = CATEGORIES.map(cat => ({
    label: cat.charAt(0).toUpperCase() + cat.slice(1),
    value: Math.round(stats.category_averages[cat] ?? 0),
    color: CAT_COLORS[cat],
  }));

  const distBars = Object.entries(stats.score_distribution).map(([range, count]) => ({
    label: range.split('-')[0],
    value: count,
    color: (() => {
      const v = parseInt(range.split('-')[0]);
      return v >= 80 ? '#22c55e' : v >= 60 ? '#3b82f6' : v >= 40 ? '#eab308' : '#ef4444';
    })(),
  }));

  return (
    <div className="space-y-8">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Agents" value={stats.totals.agents} icon={Users} color="#3b82f6"
          sub={`${stats.totals.tested} tested`} />
        <StatCard label="Certified" value={stats.totals.certified} icon={Award} color="#eab308"
          sub={`${stats.totals.agents > 0 ? Math.round(stats.totals.certified / stats.totals.agents * 100) : 0}% rate`} />
        <StatCard label="Avg Score" value={stats.avg_score || '—'} icon={TrendingUp} color="#22c55e"
          sub="across all tested" />
        <StatCard label="Pass Rate" value={`${stats.totals.pass_rate}%`} icon={CheckCircle} color="#a855f7"
          sub={`${stats.test_summary.passed.toLocaleString()} / ${stats.test_summary.total.toLocaleString()} tests`} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tests Executed" value={stats.test_summary.total.toLocaleString()} icon={Activity} color="#06b6d4"
          sub={`${stats.test_summary.failed} failed`} />
        <StatCard label="Running Now" value={stats.totals.running} icon={Clock} color="#f97316"
          sub="live test runs" />
        <StatCard label="Not Certified" value={stats.totals.not_certified} icon={XCircle} color="#ef4444"
          sub="score < 60" />
        <StatCard label="Failed Runs" value={stats.totals.failed_runs} icon={AlertTriangle} color="#6b7280"
          sub="pipeline errors" />
      </div>

      {/* Middle row: Radar + Cert Distribution + Category Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Radar */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Platform Category Averages" subtitle="Average score per category across all agents" />
          <div className="flex justify-center">
            {radarPoints.some(p => p.value > 0)
              ? <RadarChart points={radarPoints} size={210} />
              : <div className="text-slate-600 text-sm py-16 text-center">Run tests to see data</div>
            }
          </div>
        </div>

        {/* Cert distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Certification Distribution" subtitle={`${certTotal} agents tested`} />
          {certTotal === 0 ? (
            <div className="text-slate-600 text-sm text-center py-8">No completed tests yet</div>
          ) : (
            <div className="space-y-3">
              {certEntries.map(([level, count]) => (
                <div key={level} className="flex items-center gap-3">
                  <div className="w-16 text-right">
                    <span className="text-xs font-bold" style={{ color: CERT_COLORS[level] }}>
                      {level.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex-1 h-6 bg-slate-800 rounded overflow-hidden">
                    <div
                      className="h-full rounded transition-all duration-700 flex items-center px-2"
                      style={{
                        width: `${certTotal > 0 ? (count / certTotal) * 100 : 0}%`,
                        backgroundColor: CERT_COLORS[level],
                        minWidth: count > 0 ? 32 : 0,
                      }}
                    >
                      {count > 0 && <span className="text-xs font-bold text-black">{count}</span>}
                    </div>
                  </div>
                  <span className="text-xs text-slate-500 w-10 text-right">
                    {certTotal > 0 ? Math.round((count / certTotal) * 100) : 0}%
                  </span>
                </div>
              ))}
              {/* Donut summary */}
              <div className="flex items-center justify-center gap-4 mt-4 pt-3 border-t border-slate-800">
                <DonutChart
                  size={80}
                  segments={certEntries.map(([level, value]) => ({
                    label: level, value, color: CERT_COLORS[level],
                  }))}
                />
                <div className="space-y-1">
                  {certEntries.filter(([, v]) => v > 0).map(([level, count]) => (
                    <div key={level} className="flex items-center gap-2 text-xs">
                      <div className="w-2 h-2 rounded-full" style={{ background: CERT_COLORS[level] }} />
                      <span className="text-slate-400">{level.replace('_', ' ')}</span>
                      <span className="font-bold text-white ml-auto">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Category bars */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Category Scores" subtitle="Average score per category (0–100)" />
          {catBars.some(b => b.value > 0) ? (
            <HorizontalBars bars={catBars} />
          ) : (
            <div className="text-slate-600 text-sm text-center py-8">Run tests to see data</div>
          )}
        </div>
      </div>

      {/* Score distribution + Language + Top Failures */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Score histogram */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Score Distribution" subtitle="Number of agents per score range" />
          {distBars.some(b => b.value > 0) ? (
            <ColumnChart bars={distBars} height={130} />
          ) : (
            <div className="text-slate-600 text-sm text-center py-10">No scored agents yet</div>
          )}
        </div>

        {/* Language breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Language Breakdown" subtitle="Agents by programming language" />
          {langBars.length > 0 ? (
            <HorizontalBars bars={langBars} />
          ) : (
            <div className="text-slate-600 text-sm text-center py-10">No agents yet</div>
          )}
        </div>

        {/* Top failures */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Most Common Failures" subtitle="Top failing test cases platform-wide" />
          {stats.top_failures.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-10">No failures — great!</div>
          ) : (
            <div className="space-y-2">
              {stats.top_failures.map((f, i) => {
                const [cat, test] = f.test.split('/');
                return (
                  <div key={i} className="flex items-center gap-2 p-2 bg-red-950/20 border border-red-900/30 rounded-lg">
                    <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-200 truncate">
                        {test?.replace(/_/g, ' ')}
                      </p>
                      <p className="text-xs text-slate-500">{cat}</p>
                    </div>
                    <span className="text-xs font-bold text-red-400">{f.count}×</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom row: Top agents + Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Top agents */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <SectionHeader title="Top Performing Agents" subtitle="Highest overall scores" />
          {stats.top_agents.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-8">No scored agents yet</div>
          ) : (
            <div className="space-y-2">
              {stats.top_agents.map((a, i) => (
                <Link key={a.id} href={`/agent/${a.id}`}
                  className="flex items-center gap-3 p-3 bg-slate-800/40 hover:bg-slate-800 border border-slate-700/40 rounded-lg transition-colors">
                  <span className="text-xl font-black text-slate-600 w-6">#{i + 1}</span>
                  <span className="text-xl">{LANG_ICONS[a.language] ?? '📄'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">{a.name}</p>
                    <p className="text-xs text-slate-500">{a.language}</p>
                  </div>
                  <CertificationBadge level={a.certification_level} size="sm" />
                  <span className="text-sm font-bold text-white w-8 text-right">{a.overall_score?.toFixed(0)}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent agents */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <SectionHeader title="Recent Agents" subtitle="Latest uploads and test runs" />
            <Link href="#agents" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
              View all <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          {stats.recent_agents.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-8">No agents yet</div>
          ) : (
            <div className="space-y-2">
              {stats.recent_agents.map(a => {
                const sb = STATUS_BADGE[a.status as AgentStatus];
                return (
                  <Link key={a.id} href={`/agent/${a.id}`}
                    className="flex items-center gap-3 p-3 bg-slate-800/40 hover:bg-slate-800 border border-slate-700/40 rounded-lg transition-colors">
                    <span className="text-xl">{LANG_ICONS[a.language] ?? '📄'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{a.name}</p>
                      <p className="text-xs text-slate-500">
                        {new Date(a.created_at).toLocaleDateString()} · {a.language}
                      </p>
                    </div>
                    {a.overall_score !== null
                      ? <span className="text-sm font-bold text-white">{a.overall_score.toFixed(0)}</span>
                      : <Badge variant={sb.variant}>{sb.label}</Badge>
                    }
                    <CertificationBadge level={a.certification_level} size="sm" />
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AgentsView({ agents, onDelete, onRun, onRefresh, deleting, running }: {
  agents: Agent[];
  onDelete: (id: string) => void;
  onRun: (id: string) => void;
  onRefresh: () => void;
  deleting: string | null;
  running: string | null;
}) {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterLang, setFilterLang] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'name'>('date');

  const langs = Array.from(new Set(agents.map(a => a.language)));
  const filtered = agents
    .filter(a => a.name.toLowerCase().includes(search.toLowerCase()) || a.filename.toLowerCase().includes(search.toLowerCase()))
    .filter(a => filterStatus === 'all' || a.status === filterStatus)
    .filter(a => filterLang === 'all' || a.language === filterLang)
    .sort((a, b) => {
      if (sortBy === 'score') return (b.overall_score ?? -1) - (a.overall_score ?? -1);
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  return (
    <div className="space-y-5">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center bg-slate-900 border border-slate-800 rounded-xl p-4">
        <input
          type="text"
          placeholder="Search agents…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[160px] bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
        />
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none">
          <option value="all">All Status</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <select value={filterLang} onChange={e => setFilterLang(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none">
          <option value="all">All Languages</option>
          {langs.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none">
          <option value="date">Sort: Date</option>
          <option value="score">Sort: Score</option>
          <option value="name">Sort: Name</option>
        </select>
        <span className="text-xs text-slate-500 ml-auto">{filtered.length} agents</span>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        {filtered.length === 0 ? (
          <div className="text-center py-16">
            <Shield className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400">No agents match your filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-800/30">
                  {['Agent', 'Language', 'Status', 'Score', 'Certification', 'Tests', 'Date', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider first:pl-6 last:text-right last:pr-6">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(agent => {
                  const sb = STATUS_BADGE[agent.status];
                  return (
                    <tr key={agent.id} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{LANG_ICONS[agent.language] ?? '📄'}</span>
                          <div>
                            <Link href={`/agent/${agent.id}`}
                              className="text-sm font-medium text-slate-200 hover:text-blue-400 transition-colors">
                              {agent.name}
                            </Link>
                            <p className="text-xs text-slate-600 truncate max-w-[160px]">{agent.filename}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-400">{agent.language}</span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-1.5">
                          {agent.status === 'running' && <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />}
                          <Badge variant={sb.variant}>{sb.label}</Badge>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {agent.overall_score !== null ? (
                          <div className="w-28">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-bold text-slate-200">{agent.overall_score.toFixed(1)}</span>
                            </div>
                            <Progress value={agent.overall_score} />
                          </div>
                        ) : <span className="text-slate-700">—</span>}
                      </td>
                      <td className="px-4 py-4">
                        <CertificationBadge level={agent.certification_level} size="sm" />
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-500">{agent.test_count}</span>
                      </td>
                      <td className="px-4 py-4 text-xs text-slate-600">
                        {new Date(agent.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => router.push(`/agent/${agent.id}`)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm"
                            loading={running === agent.id}
                            disabled={agent.status === 'running'}
                            onClick={() => onRun(agent.id)}
                            className="text-blue-400 hover:bg-blue-900/20">
                            <Play className="w-4 h-4" />
                          </Button>
                          {agent.status === 'completed' && (
                            <Button variant="ghost" size="sm" onClick={() => router.push(`/agent/${agent.id}/report`)}
                              className="text-slate-400">
                              <FileText className="w-4 h-4" />
                            </Button>
                          )}
                          <Button variant="ghost" size="sm"
                            loading={deleting === agent.id}
                            onClick={() => onDelete(agent.id)}
                            className="text-red-400 hover:bg-red-900/20">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsView({ stats }: { stats: PlatformStats | null }) {
  if (!stats) return <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 text-blue-400 animate-spin" /></div>;

  const passRateBars = CATEGORIES.map(cat => {
    const d = stats.category_pass_rates[cat];
    return { label: cat.charAt(0).toUpperCase() + cat.slice(1), value: d?.pass_rate ?? 0, color: CAT_COLORS[cat] };
  });

  const avgScoreBars = CATEGORIES.map(cat => ({
    label: cat.charAt(0).toUpperCase() + cat.slice(1),
    value: Math.round(stats.category_averages[cat] ?? 0),
    color: CAT_COLORS[cat],
  }));

  return (
    <div className="space-y-6">
      {/* test summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Tests Run', value: stats.test_summary.total.toLocaleString(), color: '#3b82f6', icon: Activity },
          { label: 'Passed', value: stats.test_summary.passed.toLocaleString(), color: '#22c55e', icon: CheckCircle },
          { label: 'Failed', value: stats.test_summary.failed.toLocaleString(), color: '#ef4444', icon: XCircle },
          { label: 'Warnings', value: stats.test_summary.warnings.toLocaleString(), color: '#eab308', icon: AlertTriangle },
        ].map(s => (
          <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <s.icon className="w-4 h-4" style={{ color: s.color }} />
              <span className="text-xs text-slate-500">{s.label}</span>
            </div>
            <div className="text-2xl font-black text-white">{s.value}</div>
            {stats.test_summary.total > 0 && (
              <div className="mt-2">
                <Progress value={parseInt(s.value.replace(/,/g, '')) / stats.test_summary.total * 100} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Pass rate per category */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Pass Rate by Category" subtitle="% of tests passing per category" />
          <HorizontalBars bars={passRateBars} />
        </div>

        {/* Avg score per category */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Average Score by Category" subtitle="Mean score (0–100) per category" />
          <HorizontalBars bars={avgScoreBars} />
        </div>
      </div>

      {/* Category detail table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h2 className="font-bold text-slate-100">Category Breakdown Detail</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/30">
                {['Category', 'Weight', 'Avg Score', 'Pass Rate', 'Passed', 'Failed', 'Warnings', 'Total'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider first:pl-6">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CATEGORIES.map(cat => {
                const avg = stats.category_averages[cat] ?? 0;
                const pr = stats.category_pass_rates[cat];
                const Icon = CAT_ICONS[cat] ?? Shield;
                const weights: Record<string, string> = {
                  security: '30%', stability: '20%', performance: '15%',
                  informatics: '15%', compliance: '10%', ethics: '10%',
                };
                return (
                  <tr key={cat} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4" style={{ color: CAT_COLORS[cat] }} />
                        <span className="text-sm font-medium text-slate-200 capitalize">{cat}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-400">{weights[cat]}</td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold" style={{ color: CAT_COLORS[cat] }}>{avg.toFixed(1)}</span>
                        <div className="w-16"><Progress value={avg} /></div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-slate-300">{pr?.pass_rate ?? 0}%</span>
                    </td>
                    <td className="px-4 py-4 text-sm text-green-400">{pr?.passed ?? 0}</td>
                    <td className="px-4 py-4 text-sm text-red-400">{pr?.failed ?? 0}</td>
                    <td className="px-4 py-4 text-sm text-yellow-400">{pr?.warnings ?? 0}</td>
                    <td className="px-4 py-4 text-sm text-slate-500">{pr?.total ?? 0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top failures + Score histogram */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Score Distribution" subtitle="Count of agents per score range (0–100)" />
          <ColumnChart bars={Object.entries(stats.score_distribution).map(([k, v]) => ({
            label: k.split('-')[0],
            value: v,
            color: (() => { const n = parseInt(k); return n >= 80 ? '#22c55e' : n >= 60 ? '#3b82f6' : n >= 40 ? '#eab308' : '#ef4444'; })(),
          }))} height={140} />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Most Common Failures" subtitle="Frequently failing tests across all agents" />
          {stats.top_failures.length === 0 ? (
            <div className="text-center py-10 text-slate-600 text-sm">No failures recorded — excellent!</div>
          ) : (
            <div className="space-y-2 mt-2">
              {stats.top_failures.map((f, i) => {
                const [cat, test] = f.test.split('/');
                const Icon = CAT_ICONS[cat] ?? Shield;
                return (
                  <div key={i} className="flex items-center gap-3 p-3 bg-red-950/20 border border-red-900/30 rounded-lg">
                    <span className="text-xs font-black text-red-400 w-5 text-right">#{i + 1}</span>
                    <Icon className="w-4 h-4 shrink-0" style={{ color: CAT_COLORS[cat] }} />
                    <div className="flex-1">
                      <p className="text-xs font-medium text-slate-200">{test?.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-slate-500 capitalize">{cat}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-bold text-red-400">{f.count}</span>
                      <p className="text-xs text-slate-600">failures</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ActivityView({ stats }: { stats: PlatformStats | null }) {
  if (!stats) return <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 text-blue-400 animate-spin" /></div>;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Recent Agents" subtitle="Latest uploads" />
          {stats.recent_agents.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-10">No agents yet</div>
          ) : (
            <div className="space-y-3">
              {stats.recent_agents.map(a => {
                const sb = STATUS_BADGE[a.status as AgentStatus];
                return (
                  <Link key={a.id} href={`/agent/${a.id}`}
                    className="flex items-center gap-3 p-3 bg-slate-800/40 hover:bg-slate-800 border border-slate-700/40 rounded-lg transition-colors">
                    <span className="text-2xl">{LANG_ICONS[a.language] ?? '📄'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-200 truncate">{a.name}</p>
                      <p className="text-xs text-slate-500">{a.language} · {new Date(a.created_at).toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      {a.overall_score !== null
                        ? <span className="text-sm font-bold text-white">{a.overall_score.toFixed(1)}</span>
                        : <Badge variant={sb.variant}>{sb.label}</Badge>
                      }
                      <div className="mt-1"><CertificationBadge level={a.certification_level} size="sm" /></div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <SectionHeader title="Top Performers" subtitle="Highest certified agents" />
          {stats.top_agents.length === 0 ? (
            <div className="text-slate-600 text-sm text-center py-10">No scored agents yet</div>
          ) : (
            <div className="space-y-3">
              {stats.top_agents.map((a, i) => (
                <Link key={a.id} href={`/agent/${a.id}`}
                  className="flex items-center gap-3 p-3 bg-slate-800/40 hover:bg-slate-800 border border-slate-700/40 rounded-lg transition-colors">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-black"
                    style={{ background: i === 0 ? '#a78bfa22' : i === 1 ? '#fbbf2422' : '#94a3b822',
                      color: i === 0 ? '#a78bfa' : i === 1 ? '#fbbf24' : '#94a3b8' }}>
                    #{i + 1}
                  </div>
                  <span className="text-xl">{LANG_ICONS[a.language] ?? '📄'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{a.name}</p>
                    <p className="text-xs text-slate-500">{a.language}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-black text-white">{a.overall_score?.toFixed(1)}</p>
                    <CertificationBadge level={a.certification_level} size="sm" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── main page ──────────────────────────────────────────── */

export default function DashboardPage() {
  const router = useRouter();
  const [view, setView] = useState<View>('overview');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [loadingStats, setLoadingStats] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [running, setRunning] = useState<string | null>(null);

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) { setLoadingAgents(true); setLoadingStats(true); }
    else setRefreshing(true);
    try {
      const [agentsData, statsData] = await Promise.all([
        api.listAgents(),
        api.getStats().catch(() => null),
      ]);
      setAgents(agentsData);
      if (statsData) setStats(statsData);
    } finally {
      setLoadingAgents(false);
      setLoadingStats(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    const hasRunning = agents.some(a => a.status === 'running');
    if (!hasRunning) return;
    const t = setInterval(() => fetchAll(true), 2500);
    return () => clearInterval(t);
  }, [agents, fetchAll]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this agent and all test results?')) return;
    setDeleting(id);
    try {
      await api.deleteAgent(id);
      setAgents(prev => prev.filter(a => a.id !== id));
      fetchAll(true);
    } finally { setDeleting(null); }
  };

  const handleRun = async (id: string) => {
    setRunning(id);
    try {
      await api.runTests(id);
      fetchAll(true);
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed to start');
    } finally { setRunning(null); }
  };

  const navItems: Array<{ key: View; label: string; icon: React.ElementType }> = [
    { key: 'overview', label: 'Overview', icon: LayoutDashboard },
    { key: 'agents', label: 'Agents', icon: Users },
    { key: 'analytics', label: 'Analytics', icon: BarChart3 },
    { key: 'activity', label: 'Activity', icon: Activity },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-slate-800 bg-slate-900/60 flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-slate-800">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-400" />
            <span className="font-bold text-slate-100">Agent Certifier</span>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setView(key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                view === key
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}>
              <Icon className="w-4 h-4 shrink-0" />
              {label}
              {key === 'agents' && agents.length > 0 && (
                <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${
                  view === key ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-400'
                }`}>{agents.length}</span>
              )}
              {key === 'agents' && agents.some(a => a.status === 'running') && (
                <Loader2 className="w-3 h-3 animate-spin ml-auto text-blue-400" />
              )}
            </button>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="p-3 border-t border-slate-800 space-y-2">
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => fetchAll(true)} loading={refreshing}>
            <RefreshCw className="w-4 h-4" /> Refresh
          </Button>
          <Button size="sm" className="w-full justify-start" onClick={() => router.push('/')}>
            <Upload className="w-4 h-4" /> Upload Agent
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col">
        {/* Top bar */}
        <header className="border-b border-slate-800 bg-slate-900/40 px-6 py-4 flex items-center justify-between shrink-0">
          <div>
            <h1 className="font-bold text-slate-100 capitalize">{view}</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              {view === 'overview' && 'Platform-wide metrics and insights'}
              {view === 'agents' && `${agents.length} agents · ${agents.filter(a => a.status === 'completed').length} tested`}
              {view === 'analytics' && 'Deep-dive test analysis'}
              {view === 'activity' && 'Recent uploads and results'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {agents.some(a => a.status === 'running') && (
              <div className="flex items-center gap-1.5 text-xs text-blue-400 bg-blue-950/40 border border-blue-800/40 rounded-lg px-3 py-1.5">
                <Loader2 className="w-3 h-3 animate-spin" /> Tests running…
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={() => fetchAll(true)} loading={refreshing}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </header>

        {/* View content */}
        <div className="flex-1 overflow-auto p-6">
          {loadingAgents && loadingStats ? (
            <div className="flex items-center justify-center py-32">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
          ) : (
            <>
              {view === 'overview' && <OverviewView stats={stats} agents={agents} onRefresh={() => fetchAll(true)} />}
              {view === 'agents' && (
                <AgentsView agents={agents} onDelete={handleDelete} onRun={handleRun}
                  onRefresh={() => fetchAll(true)} deleting={deleting} running={running} />
              )}
              {view === 'analytics' && <AnalyticsView stats={stats} />}
              {view === 'activity' && <ActivityView stats={stats} />}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
