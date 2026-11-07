import React from 'react';
import { UploadCloud, FileSearch, Network, FileCheck2 } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Frictionless Upload',
      desc: 'Submit single PDFs or bulk batches exceeding 300 reports in ZIP format. No account registration or student credentials required.',
      icon: UploadCloud,
    },
    {
      step: '02',
      title: 'Structural PDF & OCR Extraction',
      desc: 'PyMuPDF and Tesseract extract paragraphs, coordinates, headings, code fragments, tables, and isolate bibliographic references.',
      icon: FileSearch,
    },
    {
      step: '03',
      title: 'Multi-Signal AI Similarity Analysis',
      desc: 'Queries public GitHub repositories, Crossref metadata, arXiv papers, and internet sources using 4 hybrid NLP and code-matching methods.',
      icon: Network,
    },
    {
      step: '04',
      title: 'RPi_CSR PDF Report Generation',
      desc: 'ReportLab synthesizes a Turnitin-style similarity report with colored highlights, circular source badges, clickable URLs, and database percentages.',
      icon: FileCheck2,
    },
  ];

  return (
    <section id="how-it-works" className="py-16 border-t border-slate-800/80 scroll-mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="text-xs font-bold uppercase tracking-widest text-cyan-400">
            Transparent Workflow
          </span>
          <h2 className="text-3xl font-extrabold text-white mt-2">
            How The Analysis Engine Works
          </h2>
          <p className="text-sm text-slate-400 mt-3 leading-relaxed">
            Every submission is processed through an automated 8-stage asynchronous verification pipeline
            designed for explainability, accuracy, and student privacy.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {steps.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.step}
                className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all group relative"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="w-12 h-12 rounded-xl bg-slate-800/90 group-hover:bg-cyan-500/10 border border-slate-700 group-hover:border-cyan-500/30 flex items-center justify-center text-cyan-400 transition-colors">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-2xl font-black text-slate-700 group-hover:text-slate-500 transition-colors">
                    {s.step}
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mb-2">{s.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
