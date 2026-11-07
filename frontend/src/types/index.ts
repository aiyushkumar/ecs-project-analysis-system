export type ProcessingStage =
  | 'Queued for Processing'
  | 'Upload Validation'
  | 'PDF Text Extraction'
  | 'Document Understanding'
  | 'GitHub Source Discovery'
  | 'Research Paper Analysis'
  | 'Internet Source Analysis'
  | 'Similarity Detection'
  | 'PDF Report Generation'
  | 'Analysis Completed'
  | 'Analysis Failed';

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface SourceEvidence {
  source_id: string;
  source_number: number;
  title: string;
  url: string;
  category: string;
  author_or_owner: string;
  publication_or_repo: string;
  percentage: number;
  match_count: number;
  retrieved_at: string;
}

export interface SimilarityMatchEvidence {
  match_id: string;
  source_number: number;
  source_title: string;
  source_url: string;
  source_category: string;
  page_number: number;
  section_name: string;
  matched_text: string;
  source_excerpt: string;
  match_type: string;
  confidence: number;
  start_char: number;
  end_char: number;
}

export interface SimilaritySummary {
  overall_similarity: number;
  internet_percentage: number;
  publications_percentage: number;
  crossref_percentage: number;
  github_percentage: number;
  exact_similarity: number;
  lexical_similarity: number;
  semantic_similarity: number;
  code_similarity: number;
  calculation_method: string;
  disclaimer: string;
}

export interface JobStatusResponse {
  job_id: string;
  batch_id?: string | null;
  original_filename: string;
  file_size_bytes: number;
  page_count: number;
  word_count: number;
  character_count: number;
  status: JobStatus;
  stage: ProcessingStage;
  stage_progress: number;
  overall_similarity: number;
  error_message?: string | null;
  processing_duration_sec?: number | null;
  download_available: boolean;
  download_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResultResponse {
  job_id: string;
  original_filename: string;
  report_id: string;
  word_count: number;
  character_count: number;
  page_count: number;
  file_size_mb: number;
  submission_date: string;
  report_date: string;
  processing_duration_seconds: number;
  similarity_summary: SimilaritySummary;
  top_sources: SourceEvidence[];
  matches: SimilarityMatchEvidence[];
  sections_detected: string[];
  download_url: string;
}

export interface BatchStatusResponse {
  batch_id: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  processing_files: number;
  status: JobStatus;
  progress_percentage: number;
  jobs: JobStatusResponse[];
  zip_download_available: boolean;
  zip_download_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobCreateResponse {
  job_id: string;
  original_filename: string;
  status: JobStatus;
  stage: ProcessingStage;
  private_token: string;
  status_url: string;
  result_url: string;
  created_at: string;
}

export interface BatchCreateResponse {
  batch_id: string;
  total_files: number;
  jobs: JobCreateResponse[];
  private_token: string;
  status_url: string;
  download_url: string;
  created_at: string;
}
