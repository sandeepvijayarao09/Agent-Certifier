'use client';

import { CheckCircle, XCircle, AlertTriangle, Download, Award } from 'lucide-react';
import { CertificationBadge } from '@/components/CertificationBadge';
import { ScoreGauge } from '@/components/ScoreGauge';
import { Progress } from '@/components/ui/Progress';
import type { Report } from '@/lib/types';

interface ReportViewerProps {
  report: Report;
}

const CATEGORY_LABELS: Record<string, string> = {
  security: 'Security',
  stability: 'Stability',
  performance: 'Performance',
  informatics: 'Informatics',
  compliance: 'Compliance',
  ethics: 'Ethics',
};

export function ReportViewer({ report }: ReportViewerProps) {
  const handleDownload = () => {
    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${report.agent_name}-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 bg-slate-900 border border-slate-700/50 rounded-xl p-6">
        <div className="flex items-start gap-6">
          <ScoreGauge score={report.overall_score} size="lg" />
          <div>
            <h2 className="text-2xl font-bold text-slate-100">{report.agent_name}</h2>
            <p className="text-slate-400 mt-1">{report.filename} &bull; {report.language}</p>
            <div className="mt-3">
              <CertificationBadge level={report.certification_level} size="lg" showDescription />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
              <span className="text-slate-500">Test Date:</span>
              <span className="text-slate-300">{new Date(report.test_date).toLocaleDateString()}</span>
              <span className="text-slate-500">Valid Until:</span>
              <span className="text-slate-300">{new Date(report.certification_valid_until).toLocaleDateString()}</span>
              <span className="text-slate-500">Total Tests:</span>
              <span className="text-slate-300">{report.total_tests}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-green-900/20 border border-green-700/30 rounded-lg px-3 py-2">
              <div className="text-xl font-bold text-green-400">{report.passed_tests}</div>
              <div className="text-xs text-slate-500">Passed</div>
            </div>
            <div className="bg-red-900/20 border border-red-700/30 rounded-lg px-3 py-2">
              <div className="text-xl font-bold text-red-400">{report.failed_tests}</div>
              <div className="text-xs text-slate-500">Failed</div>
            </div>
            <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-lg px-3 py-2">
              <div className="text-xl font-bold text-yellow-400">{report.warning_tests}</div>
              <div className="text-xs text-slate-500">Warnings</div>
            </div>
          </div>
          <button
            onClick={handleDownload}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-600/50 rounded-lg text-sm text-slate-300 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download JSON
          </button>
        </div>
      </div>

      {/* Category Scores */}
      <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">Category Breakdown</h3>
        <div className="space-y-4">
          {Object.entries(report.category_scores).map(([cat, data]) => (
            <div key={cat}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-300">
                    {CATEGORY_LABELS[cat] || cat}
                  </span>
                  <span className="text-xs text-slate-500">
                    (weight: {Math.round(data.weight * 100)}%)
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="text-green-400">{data.passed}✓</span>
                  <span className="text-red-400">{data.failed}✗</span>
                  <span className="text-yellow-400">{data.warnings}!</span>
                  <span className="text-slate-300 font-bold text-sm">{data.score}</span>
                </div>
              </div>
              <Progress value={data.score} />
            </div>
          ))}
        </div>
      </div>

      {/* Critical Issues */}
      {report.critical_issues.length > 0 && (
        <div className="bg-slate-900 border border-red-700/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-red-400 mb-4 flex items-center gap-2">
            <XCircle className="w-5 h-5" />
            Critical Issues ({report.critical_issues.length})
          </h3>
          <div className="space-y-3">
            {report.critical_issues.map((issue, i) => (
              <div key={i} className="bg-red-900/10 border border-red-800/30 rounded-lg px-4 py-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-red-300 capitalize">
                      {issue.category} &rsaquo; {issue.test_name.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {String(issue.details?.message || 'No details available')}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-red-400 flex-shrink-0">
                    {Math.round(issue.score)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {report.warnings.length > 0 && (
        <div className="bg-slate-900 border border-yellow-700/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-yellow-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Warnings ({report.warnings.length})
          </h3>
          <div className="space-y-2">
            {report.warnings.slice(0, 10).map((w, i) => (
              <div key={i} className="bg-yellow-900/10 border border-yellow-800/30 rounded-lg px-4 py-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-yellow-300 capitalize">
                      {w.category} &rsaquo; {w.test_name.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {String(w.details?.message || '')}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-yellow-400 flex-shrink-0">
                    {Math.round(w.score)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="bg-slate-900 border border-blue-700/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-400 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Recommendations
          </h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <span className="text-blue-400 mt-0.5 flex-shrink-0">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Certificate Section */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700/50 rounded-xl p-8 text-center">
        <Award className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
        <h3 className="text-2xl font-bold text-slate-100">{report.agent_name}</h3>
        <p className="text-slate-400 mt-1">has been tested by Agent Certifier Platform</p>
        <div className="mt-4 flex justify-center">
          <CertificationBadge level={report.certification_level} size="lg" showDescription />
        </div>
        <p className="text-3xl font-bold mt-4 text-slate-100">{report.overall_score}</p>
        <p className="text-slate-500 text-sm">Overall Score</p>
        <div className="mt-4 text-xs text-slate-500">
          Certified on {new Date(report.test_date).toLocaleDateString()} &bull; Valid until {new Date(report.certification_valid_until).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}
