import React, { useState } from 'react';
import { Download, CheckCircle2, ExternalLink, Copy, Check, Share2 } from 'lucide-react';
import type { AnalysisResultResponse } from '../types';
import { getJobDownloadUrl } from '../services/api';

interface ResultCardProps {
  result: AnalysisResultResponse;
  privateToken: string;
}

const BADGE_COLOR_CLASSES = [
  'bg-[#0082c8]', // 1 Turnitin Blue
  'bg-[#00a887]', // 2 Teal
  'bg-[#6b5b95]', // 3 Purple
  'bg-[#2e7d32]', // 4 Green
  'bg-[#d9534f]', // 5 Red/Coral
  'bg-[#0288d1]', // 6 Light Blue
  'bg-[#00897b]', // 7 Mint
  'bg-[#5c6bc0]', // 8 Indigo
  'bg-[#43a047]', // 9 Forest
  'bg-[#e65100]', // 10 Orange
  'bg-[#00acc1]', // 11 Cyan
  'bg-[#8e24aa]', // 12 Violet
];

export const ResultCard: React.FC<ResultCardProps> = ({ result, privateToken }) => {
  const [copied, setCopied] = useState(false);
  const downloadUrl = getJobDownloadUrl(result.job_id, privateToken);
  const privateShareUrl = `${window.location.origin}?job_id=${result.job_id}&token=${encodeURIComponent(privateToken)}`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(privateShareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const sim = result.similarity_summary;
  const simVal = Math.round(sim.overall_similarity);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl max-w-4xl mx-auto my-8 space-y-8 animate-fadeIn">
      {/* Success Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-emerald-900/60 flex items-center justify-center shrink-0">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="font-bold text-lg text-emerald-100">Analysis Completed</h3>
            <p className="text-xs text-emerald-300">
              Report generated successfully in accordance with RPi_CSR academic reporting standards.
            </p>
          </div>
        </div>

        <a
          href={downloadUrl}
          download
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-white font-bold text-sm shadow-lg shadow-cyan-500/25 transition-all hover:scale-105 active:scale-95 shrink-0 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Download PDF Report</span>
        </a>
      </div>

      {/* Turnitin / RPi_CSR Style Metric Overview */}
      <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-6 sm:p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* Main Similarity Dial / Number */}
          <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-slate-900/80 border border-slate-800">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-4xl sm:text-5xl font-black text-white">{simVal}%</span>
            </div>
            <span className="text-xs uppercase font-bold tracking-widest text-slate-400 text-center">
              Overall Similarity
            </span>
            <span className="text-[11px] text-slate-500 text-center mt-2">
              Combined non-overlapping matches
            </span>
          </div>

          {/* Database Breakdown */}
          <div className="md:col-span-2 space-y-3.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Database Distribution
            </span>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center text-slate-300">
                <span>• Internet database</span>
                <span className="font-bold text-white">{Math.round(sim.internet_percentage)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div className="bg-cyan-400 h-1.5 rounded-full" style={{ width: `${sim.internet_percentage}%` }} />
              </div>

              <div className="flex justify-between items-center text-slate-300 pt-1">
                <span>• Publications & Crossref</span>
                <span className="font-bold text-white">{Math.round(sim.publications_percentage + sim.crossref_percentage)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div className="bg-indigo-400 h-1.5 rounded-full" style={{ width: `${sim.publications_percentage + sim.crossref_percentage}%` }} />
              </div>

              <div className="flex justify-between items-center text-slate-300 pt-1">
                <span>• Submitted Works / GitHub</span>
                <span className="font-bold text-white">{Math.round(sim.github_percentage)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div className="bg-emerald-400 h-1.5 rounded-full" style={{ width: `${sim.github_percentage}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Document Stats Strip */}
        <div className="mt-6 pt-6 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Word Count</span>
            <span className="text-sm font-semibold text-slate-200">{result.word_count.toLocaleString()} Words</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Page Count</span>
            <span className="text-sm font-semibold text-slate-200">{result.page_count} Pages</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">File Size</span>
            <span className="text-sm font-semibold text-slate-200">{result.file_size_mb} MB</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Processing Time</span>
            <span className="text-sm font-semibold text-slate-200">{result.processing_duration_seconds.toFixed(1)}s</span>
          </div>
        </div>
      </div>

      {/* Top Sources List (Turnitin Style) */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-base font-bold text-white flex items-center gap-2">
            <span>Top Identified Sources</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
              {result.top_sources.length} sources
            </span>
          </h4>
        </div>

        {result.top_sources.length === 0 ? (
          <div className="p-6 rounded-2xl bg-slate-950/40 border border-slate-800 text-center text-slate-400 text-sm">
            No external sources matched above threshold. The report demonstrates high originality.
          </div>
        ) : (
          <div className="space-y-2.5">
            {result.top_sources.map((source) => {
              const colorClass = BADGE_COLOR_CLASSES[(source.source_number - 1) % BADGE_COLOR_CLASSES.length];
              const pctStr = source.percentage >= 1.0 ? `${Math.round(source.percentage)}%` : '<1%';

              return (
                <div
                  key={source.source_id}
                  className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-3.5 truncate">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 ${colorClass}`}>
                      {source.source_number}
                    </div>
                    <div className="truncate">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-200 truncate">{source.title}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>{source.category}</span>
                        <span>•</span>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-cyan-400 hover:underline inline-flex items-center gap-1 truncate"
                        >
                          <span className="truncate">{source.url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      </div>
                    </div>
                  </div>

                  <div className="text-right shrink-0 ml-4">
                    <span className="text-sm font-bold text-cyan-400">{pctStr}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Matched Passages Preview */}
      {result.matches.length > 0 && (
        <div>
          <h4 className="text-base font-bold text-white mb-4">
            Highlighted Excerpts & Page Evidence
          </h4>
          <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
            {result.matches.slice(0, 8).map((m) => {
              const colorClass = BADGE_COLOR_CLASSES[(m.source_number - 1) % BADGE_COLOR_CLASSES.length];
              return (
                <div
                  key={m.match_id}
                  className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-sm space-y-2"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold ${colorClass}`}>
                        {m.source_number}
                      </span>
                      <span className="font-semibold text-slate-300">Page {m.page_number}</span>
                      <span>•</span>
                      <span>{m.section_name}</span>
                    </div>
                    <span className="text-cyan-400 font-medium">{m.match_type} ({Math.round(m.confidence * 100)}%)</span>
                  </div>
                  <p className="text-slate-200 text-xs sm:text-sm bg-slate-900/60 p-2.5 rounded-lg border-l-2 border-cyan-400 italic">
                    "{m.matched_text}"
                  </p>
                  <div className="text-[11px] text-slate-500 truncate">
                    Matched from: <span className="text-slate-400 font-medium">{m.source_title}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Private Shareable Result Link */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-950 border border-cyan-900/40 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
            <Share2 className="w-3.5 h-3.5" />
            <span>Private Result Link (Save or Share with Faculty)</span>
          </span>
          <span className="text-[11px] text-slate-500">Expiring in 48 hours</span>
        </div>
        <p className="text-xs text-slate-400">
          You do not need an account. Bookmark or copy this private URL to revisit these results and download your PDF report at any time:
        </p>
        <div className="flex items-center gap-2 pt-1">
          <input
            type="text"
            readOnly
            value={privateShareUrl}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-300 focus:outline-none"
          />
          <button
            onClick={handleCopyLink}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors cursor-pointer shrink-0"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
