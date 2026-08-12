'use client';

import { useState, useEffect, useCallback } from 'react';
import { Play, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import { api } from '@/lib/api';
import type { AgentStatus } from '@/lib/types';

interface TestRunnerProps {
  agentId: string;
  currentStatus: AgentStatus;
  onComplete?: () => void;
}

export function TestRunner({ agentId, currentStatus, onComplete }: TestRunnerProps) {
  const [status, setStatus] = useState<AgentStatus>(currentStatus);
  const [completedTests, setCompletedTests] = useState(0);
  const [totalTests] = useState(60);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    try {
      const s = await api.getStatus(agentId);
      setStatus(s.status);
      setCompletedTests(s.completed_tests);

      if (s.status === 'completed' || s.status === 'failed') {
        setRunning(false);
        onComplete?.();
      }
    } catch {
      // silently ignore poll errors
    }
  }, [agentId, onComplete]);

  useEffect(() => {
    if (status === 'running') {
      setRunning(true);
      const interval = setInterval(pollStatus, 1500);
      return () => clearInterval(interval);
    }
  }, [status, pollStatus]);

  const handleRun = async () => {
    setError(null);
    setRunning(true);
    setCompletedTests(0);
    try {
      await api.runTests(agentId);
      setStatus('running');
      const interval = setInterval(async () => {
        const s = await api.getStatus(agentId);
        setStatus(s.status);
        setCompletedTests(s.completed_tests);
        if (s.status === 'completed' || s.status === 'failed') {
          clearInterval(interval);
          setRunning(false);
          onComplete?.();
        }
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start tests');
      setRunning(false);
    }
  };

  const progress = totalTests > 0 ? (completedTests / totalTests) * 100 : 0;

  return (
    <div className="space-y-3">
      {status === 'running' ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-blue-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Running tests...
            </div>
            <span className="text-slate-400">
              {completedTests} / {totalTests}
            </span>
          </div>
          <Progress value={progress} colorClass="bg-blue-500" />
        </div>
      ) : status === 'completed' ? (
        <div className="flex items-center gap-2 text-green-400 text-sm">
          <CheckCircle className="w-4 h-4" />
          Tests completed
        </div>
      ) : status === 'failed' ? (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <XCircle className="w-4 h-4" />
          Test run failed
        </div>
      ) : null}

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      <Button
        onClick={handleRun}
        disabled={running}
        loading={running}
        variant={status === 'completed' ? 'secondary' : 'primary'}
      >
        <Play className="w-4 h-4" />
        {status === 'completed' ? 'Re-run Tests' : status === 'running' ? 'Running...' : 'Run Tests'}
      </Button>
    </div>
  );
}
