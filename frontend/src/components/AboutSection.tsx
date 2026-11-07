import React from 'react';
import { Database, Cpu, Lock, Sparkles, Scale } from 'lucide-react';

export const AboutSection: React.FC = () => {
  return (
    <section id="about-system" className="py-16 border-t border-slate-800/80 scroll-mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column */}
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-cyan-400 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Architectural Principles</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              Evidence-Grounded AI.<br />Free-First Open Source Foundation.
            </h2>
            <p className="mt-4 text-sm text-slate-300 leading-relaxed">
              The ECS Project Analysis System was engineered from the ground up to eliminate commercial paywalls
              and restrictive institutional locks. Powered entirely by free and open-source models, it provides
              undergraduate and graduate engineering students with transparent, verifiable similarity diagnostics.
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex items-start gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center shrink-0 text-cyan-400 mt-1">
                  <Lock className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Cryptographic Privacy Protocol</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    No student names, email addresses, or academic credentials are ever requested or stored. Access to reports is governed by unguessable 32-byte cryptographic tokens.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center shrink-0 text-indigo-400 mt-1">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">48-Hour Ephemeral Retention</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Temporary PDF uploads and generated reports are automatically purged from disk after 48 hours to preserve document sovereignty and institutional confidentiality.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center shrink-0 text-emerald-400 mt-1">
                  <Scale className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Evidence vs. Plagiarism Distinction</h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    A high similarity score is an empirical indicator for academic faculty and student review—not an automated accusation of misconduct. Citations and boilerplate are explicitly isolated.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Technology Stack Grid */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-cyan-400" />
              <span>Technology Stack Architecture</span>
            </h3>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">Frontend</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">React.js, Vite & Tailwind CSS</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">Backend</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">Python FastAPI & Pydantic v2</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">Queue & Workers</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">Redis & Celery (300+ Batch Queue)</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">PDF & OCR Engine</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">PyMuPDF, pdfplumber & Tesseract</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">AI / NLP Similarity</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">Sentence Transformers & BM25</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 block uppercase font-mono text-[10px]">PDF Report Generator</span>
                <span className="font-semibold text-slate-200 mt-0.5 block">ReportLab (RPi_CSR Design)</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-900/40 text-[11px] text-slate-400 leading-relaxed">
              <strong className="text-cyan-300">Zero Mandatory Commercial AI Dependencies:</strong> The platform runs entirely with local weights and free tier open-access research APIs (Crossref, OpenAlex, arXiv, GitHub REST).
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
