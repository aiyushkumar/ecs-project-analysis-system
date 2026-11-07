import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { UploadZone } from './components/UploadZone';
import { ProgressTracker } from './components/ProgressTracker';
import { ResultCard } from './components/ResultCard';
import { BatchOverview } from './components/BatchOverview';
import { HowItWorks } from './components/HowItWorks';
import { AboutSection } from './components/AboutSection';
import { Footer } from './components/Footer';

import {
  uploadSingleOrMultiReports,
  uploadBatchZip,
  fetchJobStatus,
  fetchJobResult,
  fetchBatchStatus
} from './services/api';
import type {
  JobStatusResponse,
  BatchStatusResponse,
  AnalysisResultResponse
} from './types';

export const App: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [currentJob, setCurrentJob] = useState<JobStatusResponse | null>(null);
  const [currentResult, setCurrentResult] = useState<AnalysisResultResponse | null>(null);
  const [currentToken, setCurrentToken] = useState<string>('');

  const [currentBatch, setCurrentBatch] = useState<BatchStatusResponse | null>(null);
  const [batchToken, setBatchToken] = useState<string>('');

  const [error, setError] = useState<string | null>(null);

  // Polling intervals
  const jobPollRef = useRef<number | null>(null);
  const batchPollRef = useRef<number | null>(null);

  // Check URL query parameters for returning students (private link access)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryJobId = params.get('job_id');
    const queryBatchId = params.get('batch_id');
    const queryToken = params.get('token');

    if (queryJobId && queryToken) {
      setCurrentToken(queryToken);
      fetchJobStatus(queryJobId)
        .then((job) => {
          setCurrentJob(job);
          if (job.status === 'completed') {
            fetchJobResult(queryJobId, queryToken).then(setCurrentResult);
          } else if (job.status !== 'failed') {
            startJobPolling(queryJobId, queryToken);
          }
        })
        .catch((err) => setError(err.message));
    } else if (queryBatchId && queryToken) {
      setBatchToken(queryToken);
      fetchBatchStatus(queryBatchId)
        .then((batch) => {
          setCurrentBatch(batch);
          if (batch.status !== 'completed') {
            startBatchPolling(queryBatchId, queryToken);
          }
        })
        .catch((err) => setError(err.message));
    }

    return () => {
      stopAllPolling();
    };
  }, []);

  const stopAllPolling = () => {
    if (jobPollRef.current) clearInterval(jobPollRef.current);
    if (batchPollRef.current) clearInterval(batchPollRef.current);
  };

  const startJobPolling = (jobId: string, token: string) => {
    stopAllPolling();
    jobPollRef.current = window.setInterval(async () => {
      try {
        const job = await fetchJobStatus(jobId);
        setCurrentJob(job);

        if (job.status === 'completed') {
          stopAllPolling();
          const result = await fetchJobResult(jobId, token);
          setCurrentResult(result);
        } else if (job.status === 'failed') {
          stopAllPolling();
        }
      } catch (err: any) {
        console.error("Job polling error:", err);
      }
    }, 1200);
  };

  const startBatchPolling = (batchId: string, _token?: string) => {
    stopAllPolling();
    batchPollRef.current = window.setInterval(async () => {
      try {
        const batch = await fetchBatchStatus(batchId);
        setCurrentBatch(batch);
        if (batch.status === 'completed') {
          stopAllPolling();
        }
      } catch (err: any) {
        console.error("Batch polling error:", err);
      }
    }, 1500);
  };

  const handleUploadSingleOrMulti = async (files: File[]) => {
    setIsUploading(true);
    setError(null);
    setCurrentResult(null);
    setCurrentBatch(null);

    try {
      const createdJobs = await uploadSingleOrMultiReports(files);
      if (createdJobs.length > 0) {
        const firstJob = createdJobs[0];
        setCurrentToken(firstJob.private_token);

        // Fetch initial status
        const initialStatus = await fetchJobStatus(firstJob.job_id);
        setCurrentJob(initialStatus);

        // Start polling
        startJobPolling(firstJob.job_id, firstJob.private_token);

        // Update URL query string without reloading page
        const newUrl = `${window.location.pathname}?job_id=${firstJob.job_id}&token=${encodeURIComponent(firstJob.private_token)}`;
        window.history.pushState({}, '', newUrl);
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadZip = async (zipFile: File) => {
    setIsUploading(true);
    setError(null);
    setCurrentJob(null);
    setCurrentResult(null);

    try {
      const batchResp = await uploadBatchZip(zipFile);
      setBatchToken(batchResp.private_token);

      const initialBatch = await fetchBatchStatus(batchResp.batch_id);
      setCurrentBatch(initialBatch);

      // Start polling batch
      startBatchPolling(batchResp.batch_id, batchResp.private_token);

      // Update URL query string
      const newUrl = `${window.location.pathname}?batch_id=${batchResp.batch_id}&token=${encodeURIComponent(batchResp.private_token)}`;
      window.history.pushState({}, '', newUrl);
    } catch (err: any) {
      setError(err.message || 'Batch upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    stopAllPolling();
    setCurrentJob(null);
    setCurrentResult(null);
    setCurrentBatch(null);
    setCurrentToken('');
    setBatchToken('');
    setError(null);
    window.history.pushState({}, '', window.location.pathname);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Navigation */}
      <Navbar onReset={handleReset} />

      <main className="flex-1">
        {/* Hero Section */}
        <HeroSection />

        {/* Global Error Banner */}
        {error && (
          <div className="max-w-4xl mx-auto px-4 my-4">
            <div className="p-4 rounded-2xl bg-rose-950/60 border border-rose-800 text-rose-200 text-sm flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-xs uppercase font-bold text-rose-300 hover:text-white cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Upload Zone (Always accessible or when no active job is running) */}
        {!currentJob && !currentBatch && (
          <UploadZone
            onUploadSingleOrMulti={handleUploadSingleOrMulti}
            onUploadZip={handleUploadZip}
            isUploading={isUploading}
          />
        )}

        {/* Active Single / Multi Job Progress */}
        {currentJob && currentJob.status !== 'completed' && (
          <ProgressTracker job={currentJob} />
        )}

        {/* Completed Single Job Result Card */}
        {currentResult && (
          <ResultCard result={currentResult} privateToken={currentToken} />
        )}

        {/* Batch Overview Tracker */}
        {currentBatch && (
          <BatchOverview
            batch={currentBatch}
            privateToken={batchToken}
            onRefresh={() => {
              if (currentBatch) {
                fetchBatchStatus(currentBatch.batch_id).then(setCurrentBatch);
              }
            }}
          />
        )}

        {/* Return to Upload button if job is finished */}
        {(currentJob || currentBatch) && (
          <div className="text-center my-8">
            <button
              onClick={handleReset}
              className="px-6 py-2.5 rounded-full bg-slate-900 border border-slate-700 hover:border-cyan-500 text-xs font-semibold text-slate-300 hover:text-white transition-all cursor-pointer shadow-md"
            >
              ← Analyze Another Report or Batch
            </button>
          </div>
        )}

        {/* How It Works Section */}
        <HowItWorks />

        {/* About System & Architecture */}
        <AboutSection />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default App;
