'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft, Shield, FileText, RefreshCw, Loader2,
  CheckCircle, XCircle, AlertTriangle, SkipForward
} from 'lucide-react';
import { ScoreGauge } from '@/components/ScoreGauge';
import { CertificationBadge } from '@/components/CertificationBadge';
import { TestRunner } from '@/components/TestRunner';
import { TestResultCard } from '@/components/TestResultCard';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Progress } from '@/components/ui/Progress';
import { api } from '@/lib/api';
import type { AgentDetail, CategoryResult, TestResultsResponse } from '@/lib/types';

const CATEGORY_TABS = [
  { key: 'security', label: 'Security', icon: '🔒' },
  { key: 'stability', label: 'Stability', icon: '⚡' },
  { key: 'performance', label: 'Performance', icon: '🚀' },
  { key: 'informatics', label: 'Informatics', icon: '📊' },
  { key: 'compliance', label: 'Compliance', icon: '⚖️' },
  { key: 'ethics', label: 'Ethics', icon: '💚' },
];

const LANG_ICONS: Record<string, string> = {
  Python: '🐍', JavaScript: '🟨', TypeScript: '🔷', Go: '🔵',
  Java: '☕', Ruby: '💎', Rust: '🦀', 'C++': '⚙️', 'C#': '🔵', PHP: '🐘',
};

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [results, setResults] = useState<TestResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgent = useCallback(async () => {
    try {
      const [agentData, resultsData] = await Promise.all([
        api.getAgent(id),
        api.getResults(id).catch(() => null),
      ]);
      setAgent(agentData);
      if (resultsData) setResults(resultsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAgent();
  }, [fetchAgent]);

  const handleTestComplete = useCallback(() => {
    fetchAgent();
  }, [fetchAgent]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center gap-4">
        <p className="text-red-400">{error || 'Agent not found'}</p>
        <Button onClick={() => router.push('/dashboard')}>Back to Dashboard</Button>
      </div>
    );
  }

  const categoryMap: Record<string, CategoryResult> = {};
  if (results) {
    results.categories.forEach((cat) => {
      categoryMap[cat.category] = cat;
    });
  }

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Nav */}
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-slate-400 hover:text-slate-200 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span className="font-bold text-slate-100">{agent.name}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={fetchAgent}>
              <RefreshCw className="w-4 h-4" />
            </Button>
            {agent.status === 'completed' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => router.push(`/agent/${id}/report`)}
              >
                <FileText className="w-4 h-4" />
                Full Report
              </Button>
            )}
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {/* Header Card */}
        <Card className="flex flex-col md:flex-row md:items-start gap-6">
          <div className="flex items-start gap-4 flex-1">
            <span className="text-4xl">{LANG_ICONS[agent.language] || '📄'}</span>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">{agent.name}</h1>
              <p className="text-slate-400 text-sm mt-0.5">
                {agent.filename} &bull; {agent.language} &bull;{' '}
                {(agent.file_size / 1024).toFixed(1)} KB
              </p>
              <div className="flex items-center gap-3 mt-3">
                <CertificationBadge level={agent.certification_level} size="md" />
                <span className="text-xs text-slate-500">
                  Uploaded {new Date(agent.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {agent.overall_score !== null && (
              <ScoreGauge score={agent.overall_score} size="md" />
            )}
            <div className="space-y-2">
              <TestRunner
                agentId={id}
                currentStatus={agent.status}
                onComplete={handleTestComplete}
              />
            </div>
          </div>
        </Card>

        {/* Category Overview */}
        {results && results.categories.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {CATEGORY_TABS.map((tab) => {
              const cat = categoryMap[tab.key];
              if (!cat) return null;
              return (
                <Card key={tab.key} className="p-4 text-center">
                  <div className="text-2xl mb-1">{tab.icon}</div>
                  <div className="text-xs text-slate-400 mb-2">{tab.label}</div>
                  <div className="text-xl font-bold text-slate-100 mb-2">
                    {Math.round(cat.average_score)}
                  </div>
                  <Progress value={cat.average_score} />
                  <div className="flex justify-center gap-2 mt-2 text-xs">
                    <span className="text-green-400">{cat.passed}✓</span>
                    <span className="text-red-400">{cat.failed}✗</span>
                    <span className="text-yellow-400">{cat.warnings}!</span>
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {/* Test Results Tabs */}
        {results && results.categories.length > 0 ? (
          <Tabs defaultValue="security">
            <TabsList>
              {CATEGORY_TABS.map((tab) => {
                const cat = categoryMap[tab.key];
                return (
                  <TabsTrigger key={tab.key} value={tab.key}>
                    {tab.icon} {tab.label}
                    {cat && (
                      <span className="ml-1.5 text-xs opacity-70">
                        {Math.round(cat.average_score)}
                      </span>
                    )}
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {CATEGORY_TABS.map((tab) => {
              const cat = categoryMap[tab.key];
              return (
                <TabsContent key={tab.key} value={tab.key}>
                  {cat ? (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4 text-sm">
                          <span className="flex items-center gap-1 text-green-400">
                            <CheckCircle className="w-4 h-4" /> {cat.passed} passed
                          </span>
                          <span className="flex items-center gap-1 text-red-400">
                            <XCircle className="w-4 h-4" /> {cat.failed} failed
                          </span>
                          <span className="flex items-center gap-1 text-yellow-400">
                            <AlertTriangle className="w-4 h-4" /> {cat.warnings} warnings
                          </span>
                        </div>
                        <div className="text-2xl font-bold text-slate-100">
                          {Math.round(cat.average_score)}/100
                        </div>
                      </div>
                      <div className="space-y-2">
                        {cat.tests.map((test) => (
                          <TestResultCard key={test.id || test.test_name} result={test} />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      No results for this category yet
                    </div>
                  )}
                </TabsContent>
              );
            })}
          </Tabs>
        ) : (
          <Card className="text-center py-12">
            <Shield className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 mb-2">No test results yet</p>
            <p className="text-slate-500 text-sm">Click "Run Tests" to start the analysis</p>
          </Card>
        )}
      </div>
    </main>
  );
}
