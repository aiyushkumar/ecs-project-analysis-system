import type {
  JobCreateResponse,
  BatchCreateResponse,
  JobStatusResponse,
  BatchStatusResponse,
  AnalysisResultResponse
} from '../types';

const API_BASE = '/api/analyze';

export async function uploadSingleOrMultiReports(files: File[]): Promise<JobCreateResponse[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function uploadBatchZip(zipFile: File): Promise<BatchCreateResponse> {
  const formData = new FormData();
  formData.append('file', zipFile);

  const response = await fetch(`${API_BASE}/batch`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Batch upload failed' }));
    throw new Error(errorData.detail || `Batch upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/status/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch job status for ${jobId}`);
  }
  return response.json();
}

export async function fetchJobResult(jobId: string, token: string): Promise<AnalysisResultResponse> {
  const response = await fetch(`${API_BASE}/result/${jobId}?token=${encodeURIComponent(token)}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch result' }));
    throw new Error(errorData.detail || `Failed to fetch result: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchBatchStatus(batchId: string): Promise<BatchStatusResponse> {
  const response = await fetch(`${API_BASE}/batch/${batchId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch batch status for ${batchId}`);
  }
  return response.json();
}

export function getJobDownloadUrl(jobId: string, token: string): string {
  return `${API_BASE}/download/${jobId}?token=${encodeURIComponent(token)}`;
}

export function getBatchZipDownloadUrl(batchId: string, token: string): string {
  return `${API_BASE}/batch/${batchId}/download?token=${encodeURIComponent(token)}`;
}

export async function retryFailedInBatch(batchId: string, token: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/batch/${batchId}/retry-failed?token=${encodeURIComponent(token)}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to trigger retry');
  }
  return response.json();
}
