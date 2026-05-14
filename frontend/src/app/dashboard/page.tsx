'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Shield, RefreshCw, Trash2, Eye, ArrowLeft,
  TrendingUp, Users, Award, AlertTriangle, Loader2
} from 'lucide-react';
import { CertificationBadge } from '@/components/CertificationBadge';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { api } from '@/lib/api';
import type { Agent, AgentStatus } from '@/lib/types';

const STATUS_BADGE: Record<AgentStatus, { variant: 'success' | 'warning' | 'danger' | 'info' | 'secondary'; label: string }> = {
  pending: { variant: 'secondary', label: 'Pending' },
  running: { variant: 'info', label: 'Running' },
  completed: { variant: 'success', label: 'Completed' },
  failed: { variant: 'danger', label: 'Failed' },
};

const LANG_ICONS: Record<string, string> = {
  Python: '🐍', JavaScript: '🟨', TypeScript: '🔷', Go: '🔵',
  Java: '☕', Ruby: '💎', Rust: '🦀', 'C++': '⚙️', 'C#': '🔵', PHP: '🐘',
};

export default function DashboardPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchAgents = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const data = await api.listAgents();
      setAgents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // Auto-refresh if any agents are running
  useEffect(() => {
    const hasRunning = agents.some((a) => a.status === 'running');
    if (!hasRunning) return;
    const interval = setInterval(() => fetchAgents(true), 2000);
    return () => clearInterval(interval);
  }, [agents, fetchAgents]);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this agent and all test results?')) return;
    setDeleting(id);
    try {
      await api.deleteAgent(id);
      setAgents((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(null);
    }
  };

  // Stats
  const totalAgents = agents.length;
  const certified = agents.filter((a) => a.certification_level && a.certification_level !== 'NOT_CERTIFIED').length;
  const avgScore = agents.filter((a) => a.overall_score !== null).length
    ? Math.round(
        agents
          .filter((a) => a.overall_score !== null)
          .reduce((sum, a) => sum + (a.overall_score ?? 0), 0) /
          agents.filter((a) => a.overall_score !== null).length
      )
    : 0;
  const criticalIssues = agents.filter((a) => a.overall_score !== null && (a.overall_score ?? 100) < 60).length;

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Nav */}
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-slate-400 hover:text-slate-200 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span className="font-bold text-slate-100">Agent Dashboard</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchAgents(true)}
              loading={refreshing}
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => router.push('/')}>
              Upload Agent
            </Button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <Users className="w-4 h-4" /> Total Agents
            </div>
            <div className="text-3xl font-bold text-slate-100">{totalAgents}</div>
          </div>
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <Award className="w-4 h-4 text-yellow-400" /> Certified
            </div>
            <div className="text-3xl font-bold text-yellow-400">{certified}</div>
          </div>
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <TrendingUp className="w-4 h-4 text-blue-400" /> Avg Score
            </div>
            <div className="text-3xl font-bold text-blue-400">{avgScore || '—'}</div>
          </div>
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
              <AlertTriangle className="w-4 h-4 text-red-400" /> Critical
            </div>
            <div className="text-3xl font-bold text-red-400">{criticalIssues}</div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-slate-900 border border-slate-700/50 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/50">
            <h2 className="font-semibold text-slate-100">All Agents</h2>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
            </div>
          ) : agents.length === 0 ? (
            <div className="text-center py-16">
              <Shield className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-400 mb-4">No agents uploaded yet</p>
              <Button onClick={() => router.push('/')}>Upload First Agent</Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50 bg-slate-800/30">
                    <th className="text-left px-6 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Agent</th>
                    <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Status</th>
                    <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Score</th>
                    <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Certification</th>
                    <th className="text-left px-4 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Date</th>
                    <th className="text-right px-6 py-3 text-xs text-slate-500 font-medium uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {agents.map((agent, i) => {
                    const sb = STATUS_BADGE[agent.status];
                    return (
                      <tr
                        key={agent.id}
                        className="border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <span className="text-xl">{LANG_ICONS[agent.language] || '📄'}</span>
                            <div>
                              <Link
                                href={`/agent/${agent.id}`}
                                className="text-slate-200 font-medium hover:text-blue-400 transition-colors"
                              >
                                {agent.name}
                              </Link>
                              <p className="text-xs text-slate-500">{agent.filename} &bull; {agent.language}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-1.5">
                            {agent.status === 'running' && (
                              <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                            )}
                            <Badge variant={sb.variant}>{sb.label}</Badge>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          {agent.overall_score !== null ? (
                            <div className="w-28">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-bold text-slate-200">{agent.overall_score}</span>
                              </div>
                              <Progress value={agent.overall_score} />
                            </div>
                          ) : (
                            <span className="text-slate-600 text-sm">—</span>
                          )}
                        </td>
                        <td className="px-4 py-4">
                          <CertificationBadge level={agent.certification_level} size="sm" />
                        </td>
                        <td className="px-4 py-4 text-xs text-slate-500">
                          {new Date(agent.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => router.push(`/agent/${agent.id}`)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(agent.id)}
                              loading={deleting === agent.id}
                              className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                            >
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
    </main>
  );
}
