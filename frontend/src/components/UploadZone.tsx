import React, { useState, useRef } from 'react';
import { Upload, FileText, Archive, X, AlertCircle, ArrowUpCircle } from 'lucide-react';

interface UploadZoneProps {
  onUploadSingleOrMulti: (files: File[]) => void;
  onUploadZip: (zipFile: File) => void;
  isUploading: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onUploadSingleOrMulti,
  onUploadZip,
  isUploading,
}) => {
  const [activeTab, setActiveTab] = useState<'pdf' | 'zip'>('pdf');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedZip, setSelectedZip] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files);
      const validPdfs = filesArray.filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (validPdfs.length !== filesArray.length) {
        setErrorMsg("Some non-PDF files were excluded.");
      } else {
        setErrorMsg(null);
      }
      setSelectedFiles(prev => [...prev, ...validPdfs]);
    }
  };

  const handleZipChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.toLowerCase().endsWith('.zip')) {
        setSelectedZip(file);
        setErrorMsg(null);
      } else {
        setErrorMsg("Please upload a valid .zip archive file.");
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const filesArray = Array.from(e.dataTransfer.files);
      if (activeTab === 'zip') {
        const zipFile = filesArray.find(f => f.name.toLowerCase().endsWith('.zip'));
        if (zipFile) {
          setSelectedZip(zipFile);
          setErrorMsg(null);
        } else {
          setErrorMsg("Please drop a valid .zip file.");
        }
      } else {
        const validPdfs = filesArray.filter(f => f.name.toLowerCase().endsWith('.pdf'));
        if (validPdfs.length > 0) {
          setSelectedFiles(prev => [...prev, ...validPdfs]);
          setErrorMsg(null);
        } else {
          setErrorMsg("Only PDF files are supported in this mode.");
        }
      }
    }
  };

  const removePdf = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearZip = () => {
    setSelectedZip(null);
  };

  const handleSubmit = () => {
    if (activeTab === 'pdf') {
      if (selectedFiles.length === 0) {
        setErrorMsg("Please select at least one PDF file to analyze.");
        return;
      }
      onUploadSingleOrMulti(selectedFiles);
    } else {
      if (!selectedZip) {
        setErrorMsg("Please select a ZIP archive containing project reports.");
        return;
      }
      onUploadZip(selectedZip);
    }
  };

  return (
    <section id="upload-section" className="py-8 scroll-mt-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
          {/* Subtle accent border top */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500" />

          {/* Mode Switcher */}
          <div className="flex items-center justify-center gap-3 mb-8">
            <button
              onClick={() => { setActiveTab('pdf'); setErrorMsg(null); }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all cursor-pointer ${
                activeTab === 'pdf'
                  ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Select PDF(s)</span>
              {selectedFiles.length > 0 && (
                <span className="ml-1.5 px-2 py-0.5 rounded-full bg-slate-950/40 text-xs font-bold text-white">
                  {selectedFiles.length}
                </span>
              )}
            </button>

            <button
              onClick={() => { setActiveTab('zip'); setErrorMsg(null); }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all cursor-pointer ${
                activeTab === 'zip'
                  ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/25'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Archive className="w-4 h-4" />
              <span>Batch ZIP Upload (300+ Reports)</span>
              {selectedZip && (
                <span className="ml-1.5 px-2 py-0.5 rounded-full bg-slate-950/40 text-xs font-bold text-white">
                  1
                </span>
              )}
            </button>
          </div>

          {/* Dropzone Container */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all cursor-pointer ${
              dragOver
                ? 'border-cyan-400 bg-cyan-950/20 scale-[0.99]'
                : 'border-slate-700/80 hover:border-slate-600 bg-slate-950/40'
            }`}
            onClick={() => {
              if (activeTab === 'pdf') fileInputRef.current?.click();
              else zipInputRef.current?.click();
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf"
              multiple
              className="hidden"
            />
            <input
              type="file"
              ref={zipInputRef}
              onChange={handleZipChange}
              accept=".zip"
              className="hidden"
            />

            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-cyan-400 shadow-inner group-hover:scale-110 transition-transform">
              <Upload className="w-8 h-8 animate-pulse" />
            </div>

            <h3 className="text-lg font-semibold text-white">
              {activeTab === 'pdf' ? 'Drag and drop your project report PDF(s)' : 'Drag and drop a ZIP archive containing PDFs'}
            </h3>
            <p className="mt-2 text-sm text-slate-400 max-w-md mx-auto">
              or <span className="text-cyan-400 font-semibold underline underline-offset-2">browse files</span> on your computer.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-500">
              <span className="px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/50">
                Max size: 50MB per file
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/50">
                Page limit: Up to 300 pages
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800/60 border border-slate-700/50">
                Supports batches &gt; 300 reports
              </span>
            </div>
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="mt-4 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-center gap-3 text-sm text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Selected File Previews */}
          {activeTab === 'pdf' && selectedFiles.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Selected Files ({selectedFiles.length})
                </span>
                <button
                  onClick={() => setSelectedFiles([])}
                  className="text-xs text-rose-400 hover:text-rose-300 transition-colors cursor-pointer"
                >
                  Clear all
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
                {selectedFiles.map((file, idx) => (
                  <div
                    key={`${file.name}-${idx}`}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-sm"
                  >
                    <div className="flex items-center gap-3 truncate">
                      <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
                      <span className="truncate text-slate-200">{file.name}</span>
                      <span className="text-xs text-slate-500 shrink-0">
                        ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); removePdf(idx); }}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'zip' && selectedZip && (
            <div className="mt-6 p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-sm">
              <div className="flex items-center gap-3 truncate">
                <Archive className="w-5 h-5 text-indigo-400 shrink-0" />
                <div>
                  <span className="text-slate-200 font-medium block truncate">{selectedZip.name}</span>
                  <span className="text-xs text-slate-500">
                    {(selectedZip.size / (1024 * 1024)).toFixed(2)} MB • Batch archive
                  </span>
                </div>
              </div>
              <button
                onClick={clearZip}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Action Button */}
          <div className="mt-8">
            <button
              onClick={handleSubmit}
              disabled={isUploading || (activeTab === 'pdf' ? selectedFiles.length === 0 : !selectedZip)}
              className="w-full flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-600 hover:from-cyan-400 hover:via-sky-400 hover:to-indigo-500 text-white font-bold text-base shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] cursor-pointer"
            >
              <ArrowUpCircle className="w-5 h-5" />
              <span>
                {isUploading ? 'Validating and Uploading...' : 'Upload & Analyze Project Report'}
              </span>
            </button>
            <p className="mt-3 text-center text-[11px] text-slate-500">
              By uploading, you agree to lawful similarity verification. Submissions are temporarily held and deleted after 48 hours.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
