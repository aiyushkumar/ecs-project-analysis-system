import React from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';

interface NavbarProps {
  onReset?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onReset }) => {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={onReset}
          className="flex items-center gap-3.5 cursor-pointer group transition-transform active:scale-95"
        >
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 via-sky-600 to-indigo-600 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Cpu className="w-6 h-6 text-cyan-400 group-hover:rotate-12 transition-transform duration-300" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-wider text-white">ECS</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-500/30 text-cyan-400">
                PUBLIC
              </span>
            </div>
            <p className="text-[11px] font-medium tracking-widest uppercase text-slate-400 group-hover:text-cyan-300 transition-colors">
              Project Analysis System
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#hero" className="hover:text-cyan-400 transition-colors">
            Home
          </a>
          <a href="#upload-section" className="hover:text-cyan-400 transition-colors">
            Upload & Analyze
          </a>
          <a href="#how-it-works" className="hover:text-cyan-400 transition-colors">
            How It Works
          </a>
          <a href="#about-system" className="hover:text-cyan-400 transition-colors">
            About System
          </a>
        </nav>

        {/* Public Access Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-700/80 text-xs text-slate-300 shadow-inner">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-200">100% Anonymous</span>
          <span className="text-slate-500">•</span>
          <span className="hidden sm:inline text-slate-400">No Login Required</span>
        </div>
      </div>
    </header>
  );
};
