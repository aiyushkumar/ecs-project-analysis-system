import React, { useState } from 'react';
import { Archive, Download, RefreshCw, CheckCircle2, AlertTriangle, CircleDashed, Search } from 'lucide-react';
import type { BatchStatusResponse } from '../types';
import { getBatchZipDownloadUrl, getJobDownloadUrl, retryFailedInBatch } from '../services/api';

interface BatchOverviewProps {
  batch: BatchStatusResponse;
  privateToken: string;
  onRefresh: () => void;
}

export const BatchOverview: React.FC<BatchOverviewProps> = ({ batch, privateToken, onRefresh }) => {
  const [filter, setFilter] = useState<'all' | 'completed' | 'failed' | 'processing'>('all');
  const [search, setSearch] = useState('');
  const [isRetrying, setIsRetrying] = useState(false);

  const zipDownloadUrl = getBatchZipDownloadUrl(batch.batch_id, privateToken);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await retryFailedInBatch(batch.batch_id, privateToken);
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRetrying(false);
    }
  };

  const filteredJobs = batch.jobs.filter((j) => {
    const matchesFilter = filter === 'all' || j.status === filter;
    const matchesSearch = j.original_filename.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl max-w-5xl mx-auto my-8 space-y-6">
      {/* Batch Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
              Batch Queue Manager
            </span>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-300 font-mono">
              {batch.batch_id}
            </span>
          </div>
          <h3 className="text-2xl font-bold text-white mt-1">
            Batch Analysis ({batch.total_files} Reports)
          </h3>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
            title="Refresh Status"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {batch.zip_download_available && (
            <a
              href={zipDownloadUrl}
              download
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition-all cursor-pointer"
            >
              <Archive className="w-4 h-4" />
              <span>Download All Reports (ZIP)</span>
            </a>
          )}
        </div>
      </div>

      {/* Progress Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
          <span className="text-xs text-slate-400 block">Total Files</span>
          <span className="text-2xl font-bold text-white mt-1 block">{batch.total_files}</span>
        </div>
        <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-center">
          <span className="text-xs text-emerald-400 block">Completed</span>
          <span className="text-2xl font-bold text-emerald-300 mt-1 block">{batch.completed_files}</span>
        </div>
        <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-800/40 text-center">
          <span className="text-xs text-cyan-400 block">Processing</span>
          <span className="text-2xl font-bold text-cyan-300 mt-1 block">{batch.processing_files}</span>
        </div>
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 text-center">
          <span className="text-xs text-rose-400 block">Failed</span>
          <span className="text-2xl font-bold text-rose-300 mt-1 block">{batch.failed_files}</span>
        </div>
      </div>

      {/* Overall Batch Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Batch Progress</span>
          <span className="font-bold text-cyan-400">{batch.progress_percentage}%</span>
        </div>
        <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${batch.progress_percentage}%` }}
          />
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          {(['all', 'completed', 'processing', 'failed'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer ${
                filter === tab
                  ? 'bg-cyan-500 text-white shadow-md'
                  : 'bg-slate-800/60 text-slate-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {batch.failed_files > 0 && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="px-3 py-1.5 rounded-lg bg-rose-900/60 hover:bg-rose-800 text-rose-200 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
              <span>Retry Failed</span>
            </button>
          )}

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search file name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>

      {/* Jobs List Table */}
      <div className="border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/40">
        <div className="max-h-96 overflow-y-auto divide-y divide-slate-800/60">
          {filteredJobs.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              No reports matching the selected filter.
            </div>
          ) : (
            filteredJobs.map((job) => {
              const isCompleted = job.status === 'completed';
              const downloadUrl = isCompleted ? getJobDownloadUrl(job.job_id, privateToken) : null;

              return (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between p-3.5 sm:p-4 hover:bg-slate-900/40 transition-colors"
                >
                  <div className="flex items-center gap-3 truncate">
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : job.status === 'failed' ? (
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : (
                      <CircleDashed className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                    )}

                    <div className="truncate">
                      <span className="text-xs sm:text-sm font-medium text-slate-200 truncate block">
                        {job.original_filename}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        {job.stage} {job.status === 'processing' && `(${job.stage_progress}%)`}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    {isCompleted && (
                      <div className="text-right">
                        <span className="text-xs font-bold text-cyan-400 block">
                          {Math.round(job.overall_similarity)}% Sim
                        </span>
                        <span className="text-[10px] text-slate-500 block">
                          {job.page_count}p • {job.word_count.toLocaleString()}w
                        </span>
                      </div>
                    )}

                    {downloadUrl && (
                      <a
                        href={downloadUrl}
                        download
                        className="p-2 rounded-lg bg-slate-800 hover:bg-cyan-500 text-slate-300 hover:text-white transition-colors cursor-pointer"
                        title="Download Report"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
