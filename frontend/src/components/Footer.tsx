import React from 'react';
import { Cpu } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 py-12 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center text-white">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <span className="font-extrabold text-sm tracking-wider text-white">
                ECS PROJECT ANALYSIS SYSTEM
              </span>
              <p className="text-[11px] text-slate-500">
                AI-Powered Project Similarity Detection and PDF Reporting Platform
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs text-slate-400">
            <a href="#hero" className="hover:text-cyan-400 transition-colors">Home</a>
            <a href="#upload-section" className="hover:text-cyan-400 transition-colors">Upload & Analyze</a>
            <a href="#how-it-works" className="hover:text-cyan-400 transition-colors">How It Works</a>
            <a href="#about-system" className="hover:text-cyan-400 transition-colors">About & Tech Stack</a>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-900 grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] text-slate-500">
          <p>
            &copy; 2026–2027 ECS Project Analysis System. Built for academic integrity and peer-review preparation.
          </p>
          <p className="md:text-right">
            <strong>Disclaimer:</strong> Similarity metrics generated are empirical evidence for human assessment.
            Similarity does not constitute an automatic verdict of academic misconduct.
          </p>
        </div>
      </div>
    </footer>
  );
};
