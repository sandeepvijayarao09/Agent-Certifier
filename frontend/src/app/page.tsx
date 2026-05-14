'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Shield, Zap, BarChart3, Scale, Heart, Code2, ArrowRight, Github } from 'lucide-react';
import { AgentUploader } from '@/components/AgentUploader';
import type { Agent } from '@/lib/types';

const FEATURES = [
  {
    icon: Shield,
    title: 'Security Analysis',
    description: 'Injection vulnerabilities, hardcoded secrets, prompt injection resistance, and 7 more security checks.',
    color: 'text-red-400',
    bg: 'bg-red-900/20',
    border: 'border-red-700/30',
  },
  {
    icon: Zap,
    title: 'Stability Testing',
    description: 'Error handling, infinite loop detection, resource leaks, timeouts, and concurrency safety.',
    color: 'text-yellow-400',
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-700/30',
  },
  {
    icon: BarChart3,
    title: 'Performance Review',
    description: 'Caching, async I/O, batch processing, connection pooling, and algorithm complexity.',
    color: 'text-blue-400',
    bg: 'bg-blue-900/20',
    border: 'border-blue-700/30',
  },
  {
    icon: Code2,
    title: 'Code Informatics',
    description: 'Complexity scoring, documentation coverage, type annotations, naming conventions.',
    color: 'text-green-400',
    bg: 'bg-green-900/20',
    border: 'border-green-700/30',
  },
  {
    icon: Scale,
    title: 'Compliance Checks',
    description: 'PII handling, GDPR indicators, audit logging, data retention, and regulatory awareness.',
    color: 'text-purple-400',
    bg: 'bg-purple-900/20',
    border: 'border-purple-700/30',
  },
  {
    icon: Heart,
    title: 'Ethics Evaluation',
    description: 'Bias detection, transparency, human oversight, refusal mechanisms, and harm prevention.',
    color: 'text-pink-400',
    bg: 'bg-pink-900/20',
    border: 'border-pink-700/30',
  },
];

const LANGUAGES = [
  { ext: 'Python', icon: '🐍', color: 'text-yellow-400' },
  { ext: 'JavaScript', icon: '🟨', color: 'text-yellow-300' },
  { ext: 'TypeScript', icon: '🔷', color: 'text-blue-400' },
  { ext: 'Go', icon: '🔵', color: 'text-cyan-400' },
  { ext: 'Java', icon: '☕', color: 'text-orange-400' },
  { ext: 'Ruby', icon: '💎', color: 'text-red-400' },
  { ext: 'Rust', icon: '🦀', color: 'text-orange-500' },
  { ext: 'C++', icon: '⚙️', color: 'text-blue-300' },
  { ext: 'C#', icon: '🔵', color: 'text-purple-400' },
  { ext: 'PHP', icon: '🐘', color: 'text-indigo-400' },
];

export default function Home() {
  const router = useRouter();

  const handleUploadComplete = (agent: Agent) => {
    setTimeout(() => {
      router.push(`/agent/${agent.id}`);
    }, 800);
  };

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Nav */}
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-400" />
            <span className="font-bold text-slate-100">Agent Certifier</span>
          </div>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-900/30 border border-blue-700/50 rounded-full text-blue-300 text-sm mb-6">
          <Shield className="w-3.5 h-3.5" />
          Professional AI Agent Testing & Certification
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-slate-100 tracking-tight mb-6">
          Agent{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
            Certifier
          </span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-12">
          Upload your AI agent code and get a comprehensive analysis across 60 tests covering
          Security, Stability, Performance, Informatics, Compliance, and Ethics.
        </p>

        {/* Upload Zone */}
        <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-700/50 rounded-2xl p-8">
          <h2 className="text-lg font-semibold text-slate-200 mb-6">Upload Your Agent</h2>
          <AgentUploader onUploadComplete={handleUploadComplete} />
        </div>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 mt-6 text-slate-400 hover:text-slate-200 transition-colors text-sm"
        >
          Or view existing agents
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Certification Levels */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-slate-100 text-center mb-8">Certification Levels</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { level: 'PLATINUM', min: 90, emoji: '💎', color: 'text-purple-300', bg: 'bg-purple-900/20', border: 'border-purple-500/30' },
            { level: 'GOLD', min: 80, emoji: '🥇', color: 'text-yellow-300', bg: 'bg-yellow-900/20', border: 'border-yellow-500/30' },
            { level: 'SILVER', min: 70, emoji: '🥈', color: 'text-slate-300', bg: 'bg-slate-700/20', border: 'border-slate-400/30' },
            { level: 'BRONZE', min: 60, emoji: '🥉', color: 'text-orange-300', bg: 'bg-orange-900/20', border: 'border-orange-500/30' },
            { level: 'NOT CERTIFIED', min: 0, emoji: '✗', color: 'text-red-300', bg: 'bg-red-900/20', border: 'border-red-500/30' },
          ].map((cert) => (
            <div
              key={cert.level}
              className={`${cert.bg} border ${cert.border} rounded-xl p-4 text-center`}
            >
              <div className="text-3xl mb-2">{cert.emoji}</div>
              <div className={`font-bold text-sm ${cert.color}`}>{cert.level}</div>
              <div className="text-xs text-slate-500 mt-1">
                {cert.min > 0 ? `${cert.min}+ score` : '< 60 score'}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-slate-100 text-center mb-3">
          60 Tests Across 6 Categories
        </h2>
        <p className="text-slate-400 text-center mb-10">
          Weighted analysis: Security (30%) + Stability (20%) + Performance (15%) + Informatics (15%) + Compliance (10%) + Ethics (10%)
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((feat) => {
            const Icon = feat.icon;
            return (
              <div
                key={feat.title}
                className={`${feat.bg} border ${feat.border} rounded-xl p-5`}
              >
                <div className={`${feat.color} mb-3`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className={`font-semibold ${feat.color} mb-1`}>{feat.title}</h3>
                <p className="text-slate-400 text-sm">{feat.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Supported Languages */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-slate-100 text-center mb-8">Supported Languages</h2>
        <div className="flex flex-wrap justify-center gap-3">
          {LANGUAGES.map((lang) => (
            <div
              key={lang.ext}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg"
            >
              <span className="text-xl">{lang.icon}</span>
              <span className={`text-sm font-medium ${lang.color}`}>{lang.ext}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 mt-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-slate-500 text-sm">
          Agent Certifier Platform &bull; Professional AI Agent Testing
        </div>
      </footer>
    </main>
  );
}
