'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileCode, X, CheckCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import type { Agent } from '@/lib/types';

interface AgentUploaderProps {
  onUploadComplete?: (agent: Agent) => void;
}

const ALLOWED_EXTENSIONS = ['.py', '.js', '.ts', '.go', '.java', '.rb', '.rs', '.cpp', '.cc', '.cs', '.php'];

const LANGUAGE_ICONS: Record<string, string> = {
  '.py': '🐍', '.js': '🟨', '.ts': '🔷', '.go': '🔵',
  '.java': '☕', '.rb': '💎', '.rs': '🦀', '.cpp': '⚙️',
  '.cc': '⚙️', '.cs': '🔵', '.php': '🐘',
};

export function AgentUploader({ onUploadComplete }: AgentUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (f.size > 10 * 1024 * 1024) {
      return 'File too large (max 10MB)';
    }
    return null;
  };

  const handleFile = (f: File) => {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
      return;
    }
    setFile(f);
    setError(null);
    setSuccess(false);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) handleFile(selected);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const agent = await api.uploadAgent(file);
      setSuccess(true);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      onUploadComplete?.(agent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const getFileExt = (filename: string) => '.' + filename.split('.').pop()?.toLowerCase();

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200',
          dragging
            ? 'border-blue-500 bg-blue-900/20'
            : file
            ? 'border-green-500/50 bg-green-900/10'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/30 hover:bg-slate-800/50'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleInputChange}
          className="hidden"
        />

        {file ? (
          <div className="flex flex-col items-center gap-3">
            <div className="text-4xl">
              {LANGUAGE_ICONS[getFileExt(file.name)] || '📄'}
            </div>
            <div>
              <p className="text-slate-200 font-medium">{file.name}</p>
              <p className="text-slate-400 text-sm mt-1">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="text-slate-500 hover:text-red-400 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        ) : success ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle className="w-12 h-12 text-green-400" />
            <p className="text-green-400 font-medium">Agent uploaded successfully!</p>
            <p className="text-slate-400 text-sm">Drop another file to upload more</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className={clsx(
              'p-4 rounded-full transition-colors',
              dragging ? 'bg-blue-800/50' : 'bg-slate-700/50'
            )}>
              <Upload className={clsx('w-8 h-8', dragging ? 'text-blue-400' : 'text-slate-400')} />
            </div>
            <div>
              <p className="text-slate-300 font-medium">
                {dragging ? 'Drop your agent file here' : 'Drag & drop your agent file'}
              </p>
              <p className="text-slate-500 text-sm mt-1">or click to browse</p>
            </div>
            <div className="flex flex-wrap justify-center gap-1.5 mt-2">
              {ALLOWED_EXTENSIONS.map((ext) => (
                <span key={ext} className="text-xs px-2 py-0.5 bg-slate-700/50 text-slate-400 rounded">
                  {LANGUAGE_ICONS[ext]} {ext}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg px-4 py-2">
          <X className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {file && (
        <Button onClick={handleUpload} loading={uploading} size="lg" className="w-full">
          <FileCode className="w-5 h-5" />
          {uploading ? 'Uploading...' : 'Upload & Analyze Agent'}
        </Button>
      )}
    </div>
  );
}
