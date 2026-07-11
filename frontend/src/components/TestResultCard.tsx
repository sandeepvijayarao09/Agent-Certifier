'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, XCircle, AlertTriangle, SkipForward } from 'lucide-react';
import { clsx } from 'clsx';
import { Progress } from '@/components/ui/Progress';
import type { TestResult, TestStatus } from '@/lib/types';

interface TestResultCardProps {
  result: TestResult;
}

const statusConfig: Record<TestStatus, { icon: typeof CheckCircle; color: string; bg: string; label: string }> = {
  pass: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-900/20', label: 'Pass' },
  fail: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-900/20', label: 'Fail' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-900/20', label: 'Warning' },
  skip: { icon: SkipForward, color: 'text-slate-400', bg: 'bg-slate-800/50', label: 'Skip' },
};

function formatTestName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .split(' ')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export function TestResultCard({ result }: TestResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const config = statusConfig[result.status] || statusConfig.skip;
  const Icon = config.icon;
  const details = result.details as Record<string, unknown>;

  return (
    <div
      className={clsx(
        'rounded-lg border border-slate-700/50 overflow-hidden',
        config.bg
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-800/30 transition-colors"
      >
        <Icon className={clsx('w-5 h-5 flex-shrink-0', config.color)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-4">
            <span className="text-sm font-medium text-slate-200 truncate">
              {formatTestName(result.test_name)}
            </span>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className={clsx('text-xs font-medium', config.color)}>
                {config.label}
              </span>
              <span className="text-sm font-bold text-slate-300 w-10 text-right">
                {Math.round(result.score)}
              </span>
            </div>
          </div>
          <div className="mt-1.5">
            <Progress value={result.score} />
          </div>
        </div>
        <div className="ml-2 flex-shrink-0">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-slate-700/30">
          {details?.message ? (
            <p className="text-sm text-slate-300 mb-3">{String(details.message)}</p>
          ) : null}

          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
            <span className="text-slate-500">Duration:</span>
            <span className="text-slate-300">{result.duration_ms.toFixed(1)}ms</span>
          </div>

          {Object.entries(details).map(([key, value]) => {
            if (key === 'message') return null;
            if (Array.isArray(value) && value.length === 0) return null;
            const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

            if (Array.isArray(value) && value.length > 0) {
              return (
                <div key={key} className="mt-2">
                  <span className="text-xs text-slate-500">{displayKey}:</span>
                  <ul className="mt-1 space-y-1">
                    {(value as unknown[]).slice(0, 5).map((item, i) => (
                      <li key={i} className="text-xs text-red-400 font-mono bg-slate-800/50 px-2 py-1 rounded truncate">
                        {String(item)}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            }

            if (typeof value === 'boolean') {
              return (
                <div key={key} className="grid grid-cols-2 gap-x-6 mt-1 text-xs">
                  <span className="text-slate-500">{displayKey}:</span>
                  <span className={value ? 'text-green-400' : 'text-red-400'}>
                    {value ? 'Yes' : 'No'}
                  </span>
                </div>
              );
            }

            if (typeof value === 'number' || typeof value === 'string') {
              return (
                <div key={key} className="grid grid-cols-2 gap-x-6 mt-1 text-xs">
                  <span className="text-slate-500">{displayKey}:</span>
                  <span className="text-slate-300">{String(value)}</span>
                </div>
              );
            }

            return null;
          })}
        </div>
      )}
    </div>
  );
}
