import React from 'react';
import { GitBranch, BookOpen, Globe, FileCode, CheckCircle2, Shield, ArrowDown, Sparkles } from 'lucide-react';

export const HeroSection: React.FC = () => {
  return (
    <section id="hero" className="relative pt-12 pb-16 overflow-hidden">
      {/* Background radial gradient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-gradient-to-tr from-cyan-600/15 via-sky-500/10 to-indigo-600/15 blur-[120px] pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        {/* Pill Tag */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/90 border border-cyan-500/30 text-xs text-cyan-300 mb-6 shadow-lg shadow-cyan-950/40">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Intelligent Project Similarity Analysis. Transparent. Evidence-Based.</span>
        </div>

        {/* Main Heading */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl mx-auto">
          Analyze Your Project.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400">
            Discover Its Similarities.
          </span>
        </h1>

        {/* Description */}
        <p className="mt-6 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Upload any student project report in PDF format and receive a downloadable, publication-grade
          similarity report modeled after academic peer-review standards. Instant verification against public
          codebases, research archives, and open-access sources with zero registration.
        </p>

        {/* Source connectors badges */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 text-xs font-medium shadow-sm">
            <GitBranch className="w-4 h-4 text-orange-400" />
            <span>Public GitHub Repositories</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 text-xs font-medium shadow-sm">
            <BookOpen className="w-4 h-4 text-sky-400" />
            <span>Crossref, OpenAlex & arXiv</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 text-xs font-medium shadow-sm">
            <Globe className="w-4 h-4 text-emerald-400" />
            <span>Public Internet Pages</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-200 text-xs font-medium shadow-sm">
            <FileCode className="w-4 h-4 text-purple-400" />
            <span>RPi_CSR PDF Report Output</span>
          </div>
        </div>

        {/* Key Guarantees */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-3xl mx-auto text-left">
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-slate-100">No Student Accounts</p>
              <p className="text-xs text-slate-400 mt-0.5">Submit directly through a single public URL without barriers.</p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-slate-100">300+ Batch Queue</p>
              <p className="text-xs text-slate-400 mt-0.5">Celery + Redis asynchronous processing for large university cohorts.</p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-start gap-3">
            <Shield className="w-5 h-5 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-slate-100">Cryptographic Tokens</p>
              <p className="text-xs text-slate-400 mt-0.5">Private high-entropy result links protect submissions.</p>
            </div>
          </div>
        </div>

        {/* Scroll CTA */}
        <div className="mt-10">
          <a
            href="#upload-section"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <span>Proceed to Upload Section</span>
            <ArrowDown className="w-4 h-4 animate-bounce" />
          </a>
        </div>
      </div>
    </section>
  );
};
