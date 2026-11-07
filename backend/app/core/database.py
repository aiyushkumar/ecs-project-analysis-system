import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from backend.app.core.config import settings

DB_PATH = settings.STORAGE_DIR / "ecs.db"
_lock = threading.Lock()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Batch jobs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id TEXT PRIMARY KEY,
            total_files INTEGER DEFAULT 0,
            completed_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            zip_download_path TEXT,
            private_token_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
        """)

        # Analysis jobs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            id TEXT PRIMARY KEY,
            batch_id TEXT,
            original_filename TEXT NOT NULL,
            file_hash TEXT,
            file_size_bytes INTEGER DEFAULT 0,
            page_count INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            character_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            stage TEXT DEFAULT 'Queued for Processing',
            stage_progress INTEGER DEFAULT 0,
            error_message TEXT,
            overall_similarity REAL DEFAULT 0.0,
            internet_percentage REAL DEFAULT 0.0,
            publications_percentage REAL DEFAULT 0.0,
            crossref_percentage REAL DEFAULT 0.0,
            github_percentage REAL DEFAULT 0.0,
            exact_similarity REAL DEFAULT 0.0,
            lexical_similarity REAL DEFAULT 0.0,
            semantic_similarity REAL DEFAULT 0.0,
            code_similarity REAL DEFAULT 0.0,
            sections_json TEXT DEFAULT '[]',
            report_path TEXT,
            private_token_hash TEXT NOT NULL,
            processing_duration_sec REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES batch_jobs(id)
        )
        """)

        # Sources
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            source_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT NOT NULL,
            author_or_owner TEXT,
            publication_or_repo TEXT,
            percentage REAL DEFAULT 0.0,
            match_count INTEGER DEFAULT 0,
            retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES analysis_jobs(id)
        )
        """)

        # Matches
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS similarity_matches (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            source_id TEXT,
            source_number INTEGER NOT NULL,
            source_title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_category TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            matched_text TEXT NOT NULL,
            source_excerpt TEXT NOT NULL,
            match_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            start_char INTEGER DEFAULT 0,
            end_char INTEGER DEFAULT 0,
            FOREIGN KEY (job_id) REFERENCES analysis_jobs(id)
        )
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_batch ON analysis_jobs(batch_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON analysis_jobs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_job ON sources(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_job ON similarity_matches(job_id)")
        
        conn.commit()
        conn.close()

# Initialize DB on import
init_db()

class DatabaseManager:
    @staticmethod
    def create_batch(batch_id: str, total_files: int, token_hash: str) -> dict:
        expires = datetime.utcnow() + timedelta(hours=settings.RETENTION_HOURS)
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batch_jobs (id, total_files, status, private_token_hash, expires_at)
                VALUES (?, ?, 'processing', ?, ?)
            """, (batch_id, total_files, token_hash, expires.isoformat()))
            conn.commit()
            conn.close()
        return DatabaseManager.get_batch(batch_id)

    @staticmethod
    def get_batch(batch_id: str) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batch_jobs WHERE id = ?", (batch_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create_job(job_id: str, original_filename: str, token_hash: str, batch_id: str | None = None, file_size: int = 0) -> dict:
        expires = datetime.utcnow() + timedelta(hours=settings.RETENTION_HOURS)
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analysis_jobs (
                    id, batch_id, original_filename, file_size_bytes, status, stage, private_token_hash, expires_at
                ) VALUES (?, ?, ?, ?, 'pending', 'Queued for Processing', ?, ?)
            """, (job_id, batch_id, original_filename, file_size, token_hash, expires.isoformat()))
            conn.commit()
            conn.close()
        return DatabaseManager.get_job(job_id)

    @staticmethod
    def get_job(job_id: str) -> dict | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_job_stage(job_id: str, stage: str, stage_progress: int = 0, status: str = "processing"):
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE analysis_jobs
                SET stage = ?, stage_progress = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (stage, stage_progress, status, job_id))
            conn.commit()
            conn.close()

    @staticmethod
    def complete_job(
        job_id: str,
        page_count: int,
        word_count: int,
        char_count: int,
        file_hash: str,
        overall_similarity: float,
        internet_percentage: float,
        publications_percentage: float,
        crossref_percentage: float,
        github_percentage: float,
        exact_similarity: float,
        lexical_similarity: float,
        semantic_similarity: float,
        code_similarity: float,
        sections: list[str],
        report_path: str,
        duration_sec: float,
        sources: list[dict],
        matches: list[dict]
    ):
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Update job record
            cursor.execute("""
                UPDATE analysis_jobs
                SET status = 'completed',
                    stage = 'Analysis Completed',
                    stage_progress = 100,
                    page_count = ?,
                    word_count = ?,
                    character_count = ?,
                    file_hash = ?,
                    overall_similarity = ?,
                    internet_percentage = ?,
                    publications_percentage = ?,
                    crossref_percentage = ?,
                    github_percentage = ?,
                    exact_similarity = ?,
                    lexical_similarity = ?,
                    semantic_similarity = ?,
                    code_similarity = ?,
                    sections_json = ?,
                    report_path = ?,
                    processing_duration_sec = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                page_count, word_count, char_count, file_hash,
                overall_similarity, internet_percentage, publications_percentage,
                crossref_percentage, github_percentage, exact_similarity,
                lexical_similarity, semantic_similarity, code_similarity,
                json.dumps(sections), report_path, duration_sec, job_id
            ))

            # Insert sources
            for s in sources:
                cursor.execute("""
                    INSERT INTO sources (id, job_id, source_number, title, url, category, author_or_owner, publication_or_repo, percentage, match_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s["source_id"], job_id, s["source_number"], s["title"], s["url"],
                    s["category"], s.get("author_or_owner", "Unknown"),
                    s.get("publication_or_repo", ""), s.get("percentage", 0.0), s.get("match_count", 0)
                ))

            # Insert matches
            for m in matches:
                cursor.execute("""
                    INSERT INTO similarity_matches (
                        id, job_id, source_id, source_number, source_title, source_url,
                        source_category, page_number, section_name, matched_text,
                        source_excerpt, match_type, confidence, start_char, end_char
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m["match_id"], job_id, m.get("source_id"), m["source_number"],
                    m["source_title"], m["source_url"], m["source_category"],
                    m["page_number"], m["section_name"], m["matched_text"],
                    m["source_excerpt"], m["match_type"], m["confidence"],
                    m.get("start_char", 0), m.get("end_char", 0)
                ))

            # Check if part of batch
            cursor.execute("SELECT batch_id FROM analysis_jobs WHERE id = ?", (job_id,))
            b_row = cursor.fetchone()
            if b_row and b_row["batch_id"]:
                batch_id = b_row["batch_id"]
                cursor.execute("""
                    UPDATE batch_jobs
                    SET completed_files = completed_files + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (batch_id,))
                
                # Check if batch is fully done
                cursor.execute("SELECT total_files, completed_files, failed_files FROM batch_jobs WHERE id = ?", (batch_id,))
                b_info = cursor.fetchone()
                if b_info and (b_info["completed_files"] + b_info["failed_files"] >= b_info["total_files"]):
                    cursor.execute("UPDATE batch_jobs SET status = 'completed' WHERE id = ?", (batch_id,))

            conn.commit()
            conn.close()

    @staticmethod
    def fail_job(job_id: str, error_msg: str):
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE analysis_jobs
                SET status = 'failed',
                    stage = 'Analysis Failed',
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (error_msg, job_id))

            cursor.execute("SELECT batch_id FROM analysis_jobs WHERE id = ?", (job_id,))
            b_row = cursor.fetchone()
            if b_row and b_row["batch_id"]:
                batch_id = b_row["batch_id"]
                cursor.execute("""
                    UPDATE batch_jobs
                    SET failed_files = failed_files + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (batch_id,))
                
                cursor.execute("SELECT total_files, completed_files, failed_files FROM batch_jobs WHERE id = ?", (batch_id,))
                b_info = cursor.fetchone()
                if b_info and (b_info["completed_files"] + b_info["failed_files"] >= b_info["total_files"]):
                    cursor.execute("UPDATE batch_jobs SET status = 'completed' WHERE id = ?", (batch_id,))

            conn.commit()
            conn.close()

    @staticmethod
    def get_job_sources(job_id: str) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE job_id = ? ORDER BY percentage DESC, source_number ASC", (job_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_job_matches(job_id: str) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM similarity_matches WHERE job_id = ? ORDER BY page_number ASC, start_char ASC", (job_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_batch_jobs(batch_id: str) -> list[dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_jobs WHERE batch_id = ? ORDER BY created_at ASC", (batch_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def set_batch_zip(batch_id: str, zip_path: str):
        with _lock:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE batch_jobs SET zip_download_path = ? WHERE id = ?", (zip_path, batch_id))
            conn.commit()
            conn.close()
