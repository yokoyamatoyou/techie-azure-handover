# -*- coding: utf-8 -*-
"""分析結果の SQLite persistence helpers."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from core.config import config

DB_PATH = config.DATA_DIR / "analysis_history.db"

_SORTABLE_HISTORY_FIELDS = {
    "id": "id",
    "analyzed_at": "analyzed_at",
    "url": "url",
    "seo_score": "seo_score",
    "aio_score": "aio_score",
    "legal_score": "legal_score",
    "total_issues": "total_issues",
}


def get_connection() -> sqlite3.Connection:
    """Return a sqlite connection with Row objects."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {str(row[1]) for row in cursor.fetchall()}


def _ensure_analysis_runs_columns(cursor: sqlite3.Cursor) -> None:
    existing = _get_table_columns(cursor, "analysis_runs")
    if "result_path" not in existing:
        cursor.execute("ALTER TABLE analysis_runs ADD COLUMN result_path TEXT")
    if "snapshot_json" not in existing:
        cursor.execute("ALTER TABLE analysis_runs ADD COLUMN snapshot_json TEXT")
    if "pdf_path" not in existing:
        cursor.execute("ALTER TABLE analysis_runs ADD COLUMN pdf_path TEXT")


def init_database() -> None:
    """Initialize database tables and apply lightweight migrations."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_ec BOOLEAN,
            seo_score INTEGER,
            aio_score INTEGER,
            legal_score INTEGER,
            total_issues INTEGER,
            pdf_path TEXT,
            result_path TEXT,
            snapshot_json TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES analysis_runs(id),
            type TEXT,
            severity TEXT,
            title TEXT,
            detail TEXT,
            html_snippet TEXT,
            location TEXT,
            resolved BOOLEAN DEFAULT FALSE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS crawl_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES analysis_runs(id),
            url TEXT,
            depth INTEGER,
            status_code INTEGER,
            has_schema BOOLEAN
        )
        """
    )

    _ensure_analysis_runs_columns(cursor)

    conn.commit()
    conn.close()


def _get_initialized_connection() -> sqlite3.Connection:
    """Return a connection after ensuring the schema exists."""
    init_database()
    return get_connection()


def save_analysis_run(
    url: str,
    scores: Dict[str, int],
    issues: List[Dict[str, Any]],
    is_ec: bool = True,
    result_path: Optional[str] = None,
    snapshot_json: Optional[str] = None,
) -> int:
    """Persist a run and its flattened issue list."""
    init_database()
    conn = _get_initialized_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO analysis_runs (
            url, is_ec, seo_score, aio_score, legal_score, total_issues, pdf_path, result_path, snapshot_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            url,
            bool(is_ec),
            int(scores.get("seo", 0)),
            int(scores.get("aio", 0)),
            int(scores.get("legal", 0)),
            len(issues),
            None,
            result_path,
            snapshot_json,
        ),
    )

    run_id = int(cursor.lastrowid)

    for issue in issues:
        cursor.execute(
            """
            INSERT INTO issues (run_id, type, severity, title, detail, html_snippet, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                issue.get("type"),
                issue.get("severity"),
                issue.get("title"),
                issue.get("detail"),
                issue.get("html_snippet"),
                issue.get("location"),
            ),
        )

    conn.commit()
    conn.close()
    return run_id


def save_crawl_pages(run_id: int, pages: List[Dict[str, Any]]) -> int:
    """Persist crawl page metadata."""
    if not run_id or not pages:
        return 0

    conn = _get_initialized_connection()
    cursor = conn.cursor()
    saved = 0
    for page in pages:
        if not page or not page.get("url"):
            continue
        cursor.execute(
            """
            INSERT INTO crawl_pages (run_id, url, depth, status_code, has_schema)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                page.get("url"),
                page.get("depth"),
                page.get("status_code"),
                page.get("has_schema"),
            ),
        )
        saved += 1

    conn.commit()
    conn.close()
    return saved


def update_run_artifacts(
    run_id: int,
    *,
    result_path: Optional[str] = None,
    snapshot_json: Optional[str] = None,
) -> None:
    """Update optional artifact pointers for a saved run."""
    if not run_id:
        return

    updates: List[str] = []
    values: List[Any] = []
    if result_path is not None:
        updates.append("result_path = ?")
        values.append(str(result_path))
    if snapshot_json is not None:
        updates.append("snapshot_json = ?")
        values.append(snapshot_json)
    if not updates:
        return

    values.append(int(run_id))
    conn = _get_initialized_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE analysis_runs SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_run(run_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single run row."""
    conn = _get_initialized_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_runs WHERE id = ?", (int(run_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_history(
    url: Optional[str] = None,
    limit: int = 10,
    *,
    search: Optional[str] = None,
    sort_by: str = "analyzed_at",
    descending: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch recent history rows with optional URL filter and search."""
    sort_field = _SORTABLE_HISTORY_FIELDS.get(sort_by, "analyzed_at")
    direction = "DESC" if descending else "ASC"

    clauses: List[str] = []
    values: List[Any] = []
    if url:
        clauses.append("url = ?")
        values.append(url)
    if search:
        clauses.append("url LIKE ?")
        values.append(f"%{search}%")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = (
        f"SELECT * FROM analysis_runs {where_sql} "
        f"ORDER BY {sort_field} {direction}, id DESC LIMIT ?"
    )
    values.append(int(limit))

    conn = _get_initialized_connection()
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_previous_run(url: str, current_run_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetch the previous run for the same URL."""
    if not url:
        return None

    conn = _get_initialized_connection()
    cursor = conn.cursor()
    if current_run_id:
        cursor.execute(
            """
            SELECT *
            FROM analysis_runs
            WHERE url = ? AND id != ?
            ORDER BY analyzed_at DESC, id DESC
            LIMIT 1
            """,
            (url, int(current_run_id)),
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM analysis_runs
            WHERE url = ?
            ORDER BY analyzed_at DESC, id DESC
            LIMIT 1
            """,
            (url,),
        )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_run_detail(run_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a run row together with issue and crawl metadata."""
    run_row = get_run(run_id)
    if not run_row:
        return None

    conn = _get_initialized_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM issues WHERE run_id = ? ORDER BY id ASC",
        (int(run_id),),
    )
    issues = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        "SELECT * FROM crawl_pages WHERE run_id = ? ORDER BY id ASC",
        (int(run_id),),
    )
    crawl_pages = [dict(row) for row in cursor.fetchall()]
    conn.close()

    run_row["issues"] = issues
    run_row["crawl_pages"] = crawl_pages
    return run_row


def compare_runs(run_id_1: int, run_id_2: int) -> Dict[str, Any]:
    """Compare two saved runs by score deltas."""
    conn = _get_initialized_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_runs WHERE id IN (?, ?)", (run_id_1, run_id_2))
    runs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if len(runs) != 2:
        return {"error": "指定されたIDが見つかりません"}

    runs.sort(key=lambda item: int(item.get("id", 0)))
    run1, run2 = runs[0], runs[1]
    return {
        "seo_diff": int(run2.get("seo_score", 0) or 0) - int(run1.get("seo_score", 0) or 0),
        "aio_diff": int(run2.get("aio_score", 0) or 0) - int(run1.get("aio_score", 0) or 0),
        "legal_diff": int(run2.get("legal_score", 0) or 0) - int(run1.get("legal_score", 0) or 0),
        "issues_diff": int(run2.get("total_issues", 0) or 0) - int(run1.get("total_issues", 0) or 0),
        "run1": run1,
        "run2": run2,
    }


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at: {DB_PATH}")
