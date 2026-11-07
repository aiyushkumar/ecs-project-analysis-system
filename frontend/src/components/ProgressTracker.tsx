import React from 'react';
import { CheckCircle2, CircleDashed, AlertTriangle, FileText, Search, GitBranch, BookOpen, Cpu, ShieldCheck } from 'lucide-react';
import type { JobStatusResponse, ProcessingStage } from '../types';

interface ProgressTrackerProps {
  job: JobStatusResponse;
}

const STAGES: { stage: ProcessingStage; label: string; icon: React.ElementType }[] = [
  { stage: 'Upload Validation', label: '1. Upload Validation', icon: ShieldCheck },
  { stage: 'PDF Text Extraction', label: '2. PDF Text Extraction', icon: FileText },
  { stage: 'Document Understanding', label: '3. Document Understanding', icon: Search },
  { stage: 'GitHub Source Discovery', label: '4. GitHub Source Discovery', icon: GitBranch },
  { stage: 'Research Paper Analysis', label: '5. Research Paper Analysis', icon: BookOpen },
  { stage: 'Internet Source Analysis', label: '6. Internet Source Analysis', icon: Search },
  { stage: 'Similarity Detection', label: '7. Similarity Detection', icon: Cpu },
  { stage: 'PDF Report Generation', label: '8. PDF Report Generation', icon: FileText },
];

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ job }) => {
  const getStageStatus = (stageName: ProcessingStage, _index: number) => {
    const stageOrder: ProcessingStage[] = [
      'Upload Validation',
      'PDF Text Extraction',
      'Document Understanding',
      'GitHub Source Discovery',
      'Research Paper Analysis',
      'Internet Source Analysis',
      'Similarity Detection',
      'PDF Report Generation',
      'Analysis Completed'
    ];

    const currentIdx = stageOrder.indexOf(job.stage);
    const targetIdx = stageOrder.indexOf(stageName);

    if (job.status === 'failed' && currentIdx === targetIdx) {
      return 'failed';
    }
    if (job.status === 'completed' || currentIdx > targetIdx) {
      return 'completed';
    }
    if (currentIdx === targetIdx) {
      return 'current';
    }
    return 'pending';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl max-w-4xl mx-auto my-8">
      {/* File & Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
            Real-Time Analysis Pipeline
          </span>
          <h3 className="text-xl font-bold text-white mt-1 truncate max-w-md">
            {job.original_filename}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Job ID: <span className="font-mono text-slate-300">{job.job_id}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Overall Progress</span>
            <span className="text-2xl font-black text-cyan-400">
              {job.status === 'completed' ? '100%' : `${job.stage_progress}%`}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-2.5 my-6 overflow-hidden border border-slate-800">
        <div
          className="bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500 h-2.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${job.status === 'completed' ? 100 : job.stage_progress}%` }}
        />
      </div>

      {/* 8 Distinct Stages Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {STAGES.map((s, idx) => {
          const status = getStageStatus(s.stage, idx);
          const Icon = s.icon;

          return (
            <div
              key={s.stage}
              className={`p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                status === 'completed'
                  ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
                  : status === 'current'
                  ? 'bg-cyan-950/40 border-cyan-500/60 text-cyan-100 shadow-md shadow-cyan-950/50'
                  : status === 'failed'
                  ? 'bg-rose-950/40 border-rose-800/60 text-rose-200'
                  : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div className="flex items-center gap-3 truncate">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                    status === 'completed'
                      ? 'bg-emerald-900/60 text-emerald-400'
                      : status === 'current'
                      ? 'bg-cyan-900/80 text-cyan-300'
                      : status === 'failed'
                      ? 'bg-rose-900/60 text-rose-400'
                      : 'bg-slate-900 text-slate-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-xs sm:text-sm font-medium truncate">{s.label}</span>
              </div>

              <div>
                {status === 'completed' && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                )}
                {status === 'current' && (
                  <CircleDashed className="w-5 h-5 text-cyan-400 animate-spin" />
                )}
                {status === 'failed' && (
                  <AlertTriangle className="w-5 h-5 text-rose-400" />
                )}
                {status === 'pending' && (
                  <span className="text-xs text-slate-600">Pending</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {job.error_message && (
        <div className="mt-6 p-4 rounded-xl bg-rose-950/50 border border-rose-800/60 text-rose-200 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Processing Error</span>
            <p className="text-xs mt-0.5 text-rose-300">{job.error_message}</p>
          </div>
        </div>
      )}
    </div>
  );
};
