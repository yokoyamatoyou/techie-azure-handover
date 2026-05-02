from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from analysis_lib import build_deterministic_score_fields, infer_answer_structure, normalize_text
from config import DB_PATH, ensure_app_dirs

ALLOWED_TABLES = frozenset(
    {
        "question_set",
        "query_plan",
        "cluster_brief",
        "schedule_plan",
        "schedule_dispatch",
        "run_session",
        "keyword_result",
        "source_url",
        "batch_job",
        "batch_job_item",
    }
)
ALLOWED_COLUMN_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
RESULT_ENRICHMENT_MAINTENANCE_USER_VERSION = 1
RESULT_ENRICHMENT_PENDING_WHERE = """
    mentioned_brands_json IS NULL
    OR citation_domains_json IS NULL
    OR answer_type_label IS NULL
    OR raw_llm_score IS NULL
    OR deterministic_score IS NULL
    OR owned_citation_count IS NULL
    OR owned_citation_share IS NULL
    OR external_only_result IS NULL
"""


class Storage:
    def __init__(self, path: Path | None = None) -> None:
        ensure_app_dirs()
        self.path = path or DB_PATH
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path.as_posix())
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _table_columns(self, con: sqlite3.Connection, table_name: str) -> set[str]:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Disallowed table name: {table_name!r}")
        cur = con.execute(f"PRAGMA table_info({table_name})")
        return {str(row["name"]) for row in cur.fetchall()}

    def _ensure_column(self, con: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Disallowed table name: {table_name!r}")
        if not ALLOWED_COLUMN_RE.match(column_name):
            raise ValueError(f"Disallowed column name: {column_name!r}")
        if column_name in self._table_columns(con, table_name):
            return
        con.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS question_set (
                    question_set_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_run_at REAL,
                    last_run_mode TEXT,
                    notes TEXT,
                    is_archived INTEGER NOT NULL DEFAULT 0,
                    archived_at REAL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_question_set_updated_at ON question_set(updated_at DESC)")
            self._ensure_column(con, "question_set", "is_archived", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "question_set", "archived_at", "REAL")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS query_plan (
                    query_plan_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    user_query_raw TEXT NOT NULL,
                    user_query_norm TEXT NOT NULL,
                    user_query_short TEXT,
                    query_was_shortened INTEGER NOT NULL DEFAULT 0,
                    shortening_note TEXT,
                    expanded_queries_json TEXT NOT NULL,
                    prompt_taxonomy_json TEXT,
                    expansion_mode TEXT NOT NULL,
                    expansion_signature TEXT NOT NULL,
                    scheduler_mode TEXT NOT NULL DEFAULT 'immediate',
                    scheduled_dispatch_at REAL,
                    provider_batch_mode TEXT NOT NULL DEFAULT 'none',
                    provider_batch_id TEXT,
                    provider_cache_policy TEXT,
                    planner_signature TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES run_session(run_id)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_query_plan_run ON query_plan(run_id, updated_at DESC)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_query_plan_query_norm ON query_plan(user_query_norm, updated_at DESC)")
            self._ensure_column(con, "query_plan", "planner_signature", "TEXT")
            self._ensure_column(con, "query_plan", "prompt_taxonomy_json", "TEXT")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS cluster_brief (
                    brief_id TEXT PRIMARY KEY,
                    cluster_kind TEXT NOT NULL,
                    cluster_key TEXT NOT NULL,
                    cluster_label TEXT NOT NULL,
                    source_run_ids_json TEXT NOT NULL,
                    source_result_ids_json TEXT NOT NULL,
                    query_count INTEGER NOT NULL DEFAULT 0,
                    generated_title TEXT NOT NULL,
                    brief_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_cluster_brief_updated_at ON cluster_brief(updated_at DESC)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_cluster_brief_scope ON cluster_brief(cluster_kind, cluster_key)")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_plan (
                    schedule_id TEXT PRIMARY KEY,
                    question_set_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    weekdays_csv TEXT NOT NULL,
                    time_of_day TEXT NOT NULL,
                    weekly_run_count INTEGER NOT NULL,
                    timezone TEXT NOT NULL,
                    execution_mode TEXT NOT NULL DEFAULT 'batch',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    cost_guardrail_usd REAL NOT NULL DEFAULT 1.2,
                    next_run_at REAL,
                    last_scheduled_slot TEXT,
                    last_run_at REAL,
                    last_status TEXT,
                    last_error TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(question_set_id) REFERENCES question_set(question_set_id)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_schedule_plan_next_run ON schedule_plan(enabled, next_run_at)")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_dispatch (
                    dispatch_id TEXT PRIMARY KEY,
                    schedule_id TEXT NOT NULL,
                    slot_key TEXT NOT NULL,
                    scheduled_for REAL NOT NULL,
                    status TEXT NOT NULL,
                    run_id TEXT,
                    batch_job_id TEXT,
                    error_text TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    UNIQUE(schedule_id, slot_key),
                    FOREIGN KEY(schedule_id) REFERENCES schedule_plan(schedule_id)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_schedule_dispatch_schedule ON schedule_dispatch(schedule_id, scheduled_for DESC)")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS run_session (
                    run_id TEXT PRIMARY KEY,
                    started_at REAL NOT NULL,
                    finished_at REAL,
                    repeat_count INTEGER NOT NULL,
                    model_name TEXT NOT NULL,
                    prompt_cache_key TEXT NOT NULL
                )
                """
            )
            self._ensure_column(con, "run_session", "run_mode", "TEXT NOT NULL DEFAULT 'manual'")
            self._ensure_column(con, "run_session", "config_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(con, "run_session", "question_set_id", "TEXT")
            self._ensure_column(con, "run_session", "question_set_name", "TEXT")
            self._ensure_column(con, "run_session", "schedule_id", "TEXT")
            self._ensure_column(con, "run_session", "scheduled_for", "REAL")
            self._ensure_column(con, "run_session", "batch_submitted_at", "REAL")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_result (
                    result_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    analyzed_at REAL NOT NULL,
                    iteration_index INTEGER NOT NULL,
                    keyword_raw TEXT NOT NULL,
                    keyword_norm TEXT NOT NULL,
                    answer_snapshot TEXT,
                    output_text TEXT,
                    output_json TEXT NOT NULL,
                    visibility_score INTEGER NOT NULL DEFAULT 0,
                    raw_llm_score INTEGER NOT NULL DEFAULT 0,
                    deterministic_score INTEGER NOT NULL DEFAULT 0,
                    input_tokens INTEGER NOT NULL DEFAULT 0,
                    cached_tokens INTEGER NOT NULL DEFAULT 0,
                    output_tokens INTEGER NOT NULL DEFAULT 0,
                    web_search_calls INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0,
                    target_domain_hit INTEGER NOT NULL DEFAULT 0,
                    brand_mention_hit INTEGER NOT NULL DEFAULT 0,
                    owned_citation_count INTEGER NOT NULL DEFAULT 0,
                    owned_citation_share REAL NOT NULL DEFAULT 0,
                    external_only_result INTEGER NOT NULL DEFAULT 0,
                    source_count INTEGER NOT NULL DEFAULT 0,
                    error_text TEXT,
                    FOREIGN KEY(run_id) REFERENCES run_session(run_id)
                )
                """
            )
            self._ensure_column(con, "keyword_result", "answer_text", "TEXT")
            self._ensure_column(con, "keyword_result", "citations_json", "TEXT")
            self._ensure_column(con, "keyword_result", "mentioned_brands_json", "TEXT")
            self._ensure_column(con, "keyword_result", "citation_domains_json", "TEXT")
            self._ensure_column(con, "keyword_result", "owned_mention_hit", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "competitor_mention_hit", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "answer_type_key", "TEXT")
            self._ensure_column(con, "keyword_result", "answer_type_label", "TEXT")
            self._ensure_column(con, "keyword_result", "query_plan_id", "TEXT")
            self._ensure_column(con, "keyword_result", "executed_query", "TEXT")
            self._ensure_column(con, "keyword_result", "executed_query_norm", "TEXT")
            self._ensure_column(con, "keyword_result", "executed_query_index", "INTEGER")
            self._ensure_column(con, "keyword_result", "raw_llm_score", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "deterministic_score", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "owned_citation_count", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "owned_citation_share", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(con, "keyword_result", "external_only_result", "INTEGER NOT NULL DEFAULT 0")
            con.execute("CREATE INDEX IF NOT EXISTS idx_keyword_result_analyzed_at ON keyword_result(analyzed_at DESC)")
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_keyword_result_run_analyzed_at ON keyword_result(run_id, analyzed_at DESC)"
            )
            con.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_keyword_result_pending_enrichment
                ON keyword_result(analyzed_at DESC)
                WHERE {RESULT_ENRICHMENT_PENDING_WHERE}
                """
            )

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS source_url (
                    source_id TEXT PRIMARY KEY,
                    result_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    kind TEXT NOT NULL,
                    FOREIGN KEY(result_id) REFERENCES keyword_result(result_id)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_source_url_result_id ON source_url(result_id)")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_job (
                    batch_job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    provider_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    completion_window TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    repeat_count INTEGER NOT NULL,
                    request_count INTEGER NOT NULL,
                    input_file_id TEXT NOT NULL,
                    output_file_id TEXT,
                    error_file_id TEXT,
                    config_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    last_checked_at REAL,
                    imported_at REAL,
                    imported_result_count INTEGER NOT NULL DEFAULT 0,
                    imported_error_count INTEGER NOT NULL DEFAULT 0,
                    request_counts_total INTEGER NOT NULL DEFAULT 0,
                    request_counts_completed INTEGER NOT NULL DEFAULT 0,
                    request_counts_failed INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    FOREIGN KEY(run_id) REFERENCES run_session(run_id)
                )
                """
            )
            self._ensure_column(con, "batch_job", "submitted_at", "REAL")
            self._ensure_column(con, "batch_job", "reserved_cost_usd", "REAL NOT NULL DEFAULT 0")

            con.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_job_item (
                    item_id TEXT PRIMARY KEY,
                    batch_job_id TEXT NOT NULL,
                    custom_id TEXT NOT NULL UNIQUE,
                    keyword_raw TEXT NOT NULL,
                    keyword_norm TEXT NOT NULL,
                    iteration_index INTEGER NOT NULL,
                    request_body_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    response_status_code INTEGER,
                    remote_request_id TEXT,
                    imported_result_id TEXT,
                    error_text TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(batch_job_id) REFERENCES batch_job(batch_job_id)
                )
                """
            )
            self._ensure_column(con, "batch_job_item", "query_plan_id", "TEXT")
            self._ensure_column(con, "batch_job_item", "user_query_raw", "TEXT")
            self._ensure_column(con, "batch_job_item", "executed_query", "TEXT")
            self._ensure_column(con, "batch_job_item", "executed_query_index", "INTEGER")
            con.execute("CREATE INDEX IF NOT EXISTS idx_batch_job_updated_at ON batch_job(updated_at DESC)")
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_batch_job_item_batch ON batch_job_item(batch_job_id, iteration_index)"
            )

    def _get_user_version(self, con: sqlite3.Connection) -> int:
        row = con.execute("PRAGMA user_version").fetchone()
        return int(row[0] or 0) if row else 0

    def _set_user_version(self, con: sqlite3.Connection, version: int) -> None:
        con.execute(f"PRAGMA user_version = {int(version)}")

    def _load_pending_result_enrichment_rows(
        self,
        con: sqlite3.Connection,
        limit: int,
    ) -> list[sqlite3.Row]:
        return con.execute(
            f"""
                SELECT
                    result_id,
                    keyword_raw,
                    answer_text,
                    citations_json,
                    output_json,
                    raw_llm_score,
                    deterministic_score,
                    target_domain_hit,
                    brand_mention_hit,
                    owned_citation_count,
                    owned_citation_share,
                    external_only_result
                FROM keyword_result
                WHERE {RESULT_ENRICHMENT_PENDING_WHERE}
                ORDER BY analyzed_at DESC
                LIMIT ?
            """,
            (max(1, int(limit or 1)),),
        ).fetchall()

    def _count_pending_result_enrichment_rows(self, con: sqlite3.Connection) -> int:
        row = con.execute(
            f"SELECT COUNT(*) FROM keyword_result WHERE {RESULT_ENRICHMENT_PENDING_WHERE}"
        ).fetchone()
        return int(row[0] or 0) if row else 0

    def _load_sources_by_result_id(
        self,
        con: sqlite3.Connection,
        result_ids: list[str],
    ) -> dict[str, list[dict[str, str]]]:
        resolved_ids = [str(result_id or "") for result_id in result_ids if str(result_id or "")]
        if not resolved_ids:
            return {}
        placeholders = ",".join("?" for _ in resolved_ids)
        sources_by_result_id: dict[str, list[dict[str, str]]] = {result_id: [] for result_id in resolved_ids}
        for source_row in con.execute(
            f"""
            SELECT result_id, url, title
            FROM source_url
            WHERE result_id IN ({placeholders})
            ORDER BY result_id ASC, rowid ASC
            """,
            resolved_ids,
        ).fetchall():
            sources_by_result_id.setdefault(str(source_row["result_id"] or ""), []).append(
                {
                    "url": str(source_row["url"] or "").strip(),
                    "title": str(source_row["title"] or "").strip(),
                }
            )
        return sources_by_result_id

    def _backfill_result_enrichment_rows(
        self,
        con: sqlite3.Connection,
        rows: list[sqlite3.Row],
        sources_by_result_id: dict[str, list[dict[str, str]]],
    ) -> int:
        updated_count = 0
        for row in rows:
            result_id = str(row["result_id"] or "")
            try:
                payload = json.loads(str(row["output_json"] or "{}")) if row["output_json"] else {}
            except Exception:
                payload = {}
            answer_text = str(row["answer_text"] or payload.get("answer_text") or "").strip()
            citations = payload.get("citations") if isinstance(payload.get("citations"), list) else []
            if not citations:
                try:
                    citations = json.loads(str(row["citations_json"] or "[]"))
                except Exception:
                    citations = []
            structured = infer_answer_structure(
                keyword=str(row["keyword_raw"] or payload.get("keyword_raw") or ""),
                answer_text=answer_text,
                citations=citations if isinstance(citations, list) else [],
                source_items=sources_by_result_id.get(result_id, []),
                payload=payload if isinstance(payload, dict) else {},
                analysis_context=(payload.get("analysis_context") or {}) if isinstance(payload, dict) else {},
            )
            score_fields = build_deterministic_score_fields(payload if isinstance(payload, dict) else {}, structured)
            if isinstance(payload, dict):
                payload["raw_llm_score"] = score_fields["raw_llm_score"]
                payload["deterministic_score"] = score_fields["deterministic_score"]
                payload["visibility_score"] = score_fields["visibility_score"]
                payload["target_domain_hit"] = bool(structured["owned_domain_hit"])
                payload["brand_mention_hit"] = bool(structured["owned_brand_hit"])
                payload["owned_citation_count"] = int(structured["owned_citation_count"])
                payload["owned_citation_share"] = float(structured["owned_citation_share"])
                payload["external_only_result"] = bool(structured["external_only_result"])
            con.execute(
                """
                UPDATE keyword_result
                SET
                    output_json = ?,
                    visibility_score = ?,
                    raw_llm_score = ?,
                    deterministic_score = ?,
                    target_domain_hit = ?,
                    brand_mention_hit = ?,
                    mentioned_brands_json = ?,
                    citation_domains_json = ?,
                    owned_mention_hit = ?,
                    owned_citation_count = ?,
                    owned_citation_share = ?,
                    competitor_mention_hit = ?,
                    external_only_result = ?,
                    answer_type_key = ?,
                    answer_type_label = ?
                WHERE result_id = ?
                """,
                (
                    json.dumps(payload, ensure_ascii=False),
                    score_fields["visibility_score"],
                    score_fields["raw_llm_score"],
                    score_fields["deterministic_score"],
                    1 if structured["owned_domain_hit"] else 0,
                    1 if structured["owned_brand_hit"] else 0,
                    json.dumps(structured["mentioned_brands"], ensure_ascii=False),
                    json.dumps(structured["citation_domains"], ensure_ascii=False),
                    1 if structured["owned_mention_hit"] else 0,
                    int(structured["owned_citation_count"] or 0),
                    float(structured["owned_citation_share"] or 0.0),
                    1 if structured["competitor_mention_hit"] else 0,
                    1 if structured["external_only_result"] else 0,
                    structured["answer_type_key"],
                    structured["answer_type_label"],
                    row["result_id"],
                ),
            )
            updated_count += 1
        return updated_count

    def run_result_enrichment_maintenance(self, limit: int = 250) -> dict[str, Any]:
        resolved_limit = max(1, min(int(limit or 250), 5000))
        with self._connect() as con:
            current_user_version = self._get_user_version(con)
            if current_user_version >= RESULT_ENRICHMENT_MAINTENANCE_USER_VERSION:
                return {
                    "skipped": True,
                    "reason": "already_completed",
                    "updated_count": 0,
                    "remaining_count": 0,
                    "user_version": current_user_version,
                }

            rows = self._load_pending_result_enrichment_rows(con, resolved_limit)
            if not rows:
                self._set_user_version(con, RESULT_ENRICHMENT_MAINTENANCE_USER_VERSION)
                return {
                    "skipped": False,
                    "reason": "no_pending_rows",
                    "updated_count": 0,
                    "remaining_count": 0,
                    "user_version": RESULT_ENRICHMENT_MAINTENANCE_USER_VERSION,
                }

            sources_by_result_id = self._load_sources_by_result_id(
                con,
                [str(row["result_id"] or "") for row in rows],
            )
            updated_count = self._backfill_result_enrichment_rows(con, rows, sources_by_result_id)
            remaining_count = self._count_pending_result_enrichment_rows(con)
            if remaining_count <= 0:
                self._set_user_version(con, RESULT_ENRICHMENT_MAINTENANCE_USER_VERSION)
            return {
                "skipped": False,
                "reason": "updated",
                "updated_count": updated_count,
                "remaining_count": remaining_count,
                "user_version": self._get_user_version(con),
            }

    def upsert_question_set(
        self,
        *,
        name: str,
        config_json: str,
        question_set_id: str | None = None,
        notes: str = "",
    ) -> str:
        now = time.time()
        resolved_id = question_set_id or f"qs_{uuid.uuid4().hex}"
        with self._connect() as con:
            existing = con.execute(
                "SELECT question_set_id FROM question_set WHERE question_set_id = ?",
                (resolved_id,),
            ).fetchone()
            if existing:
                con.execute(
                    """
                    UPDATE question_set
                    SET name = ?, config_json = ?, notes = ?, updated_at = ?
                    WHERE question_set_id = ?
                    """,
                    (name, config_json, notes, now, resolved_id),
                )
            else:
                con.execute(
                    """
                    INSERT INTO question_set (
                        question_set_id, name, config_json, created_at, updated_at, notes, is_archived, archived_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
                    """,
                    (resolved_id, name, config_json, now, now, notes),
                )
        return resolved_id

    def save_query_plan(
        self,
        *,
        run_id: str,
        user_query_raw: str,
        user_query_norm: str,
        user_query_short: str,
        query_was_shortened: bool,
        shortening_note: str,
        expanded_queries_json: str,
        prompt_taxonomy_json: str = "[]",
        expansion_mode: str,
        expansion_signature: str,
        scheduler_mode: str,
        scheduled_dispatch_at: float | None,
        provider_batch_mode: str,
        provider_batch_id: str = "",
        provider_cache_policy: str = "",
        planner_signature: str = "",
        query_plan_id: str | None = None,
    ) -> str:
        now = time.time()
        resolved_id = query_plan_id or f"qp_{uuid.uuid4().hex}"
        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO query_plan (
                    query_plan_id,
                    run_id,
                    user_query_raw,
                    user_query_norm,
                    user_query_short,
                    query_was_shortened,
                    shortening_note,
                    expanded_queries_json,
                    prompt_taxonomy_json,
                    expansion_mode,
                    expansion_signature,
                    scheduler_mode,
                    scheduled_dispatch_at,
                    provider_batch_mode,
                    provider_batch_id,
                    provider_cache_policy,
                    planner_signature,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_id,
                    run_id,
                    user_query_raw,
                    user_query_norm,
                    user_query_short,
                    1 if query_was_shortened else 0,
                    shortening_note,
                    expanded_queries_json,
                    prompt_taxonomy_json,
                    expansion_mode,
                    expansion_signature,
                    scheduler_mode,
                    scheduled_dispatch_at,
                    provider_batch_mode,
                    provider_batch_id,
                    provider_cache_policy,
                    planner_signature,
                    now,
                    now,
                ),
            )
        return resolved_id

    def get_latest_query_plan_for_query(
        self,
        user_query_norm: str,
        planner_signature: str = "",
    ) -> dict[str, Any] | None:
        if not user_query_norm:
            return None
        with self._connect() as con:
            if planner_signature:
                row = con.execute(
                    """
                    SELECT *
                    FROM query_plan
                    WHERE user_query_norm = ? AND planner_signature = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (user_query_norm, planner_signature),
                ).fetchone()
            else:
                row = con.execute(
                    """
                    SELECT *
                    FROM query_plan
                    WHERE user_query_norm = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (user_query_norm,),
                ).fetchone()
            return dict(row) if row else None

    def list_query_plans_for_run(self, run_id: str) -> list[dict[str, Any]]:
        if not run_id:
            return []
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT *
                FROM query_plan
                WHERE run_id = ?
                ORDER BY created_at ASC
                """,
                (run_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_query_plans_for_runs(self, run_ids: list[str]) -> list[dict[str, Any]]:
        resolved_ids = [str(run_id or "") for run_id in run_ids if str(run_id or "")]
        if not resolved_ids:
            return []
        placeholders = ",".join("?" for _ in resolved_ids)
        with self._connect() as con:
            cur = con.execute(
                f"""
                SELECT *
                FROM query_plan
                WHERE run_id IN ({placeholders})
                ORDER BY created_at ASC
                """,
                resolved_ids,
            )
            return [dict(row) for row in cur.fetchall()]

    def update_query_plans_batch_context(self, run_id: str, *, provider_batch_id: str, provider_batch_mode: str) -> None:
        if not run_id:
            return
        with self._connect() as con:
            con.execute(
                """
                UPDATE query_plan
                SET provider_batch_id = ?, provider_batch_mode = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (
                    provider_batch_id,
                    provider_batch_mode,
                    time.time(),
                    run_id,
                ),
            )

    def get_question_set(self, question_set_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT *
                FROM question_set
                WHERE question_set_id = ?
                """,
                (question_set_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_question_sets(self, limit: int = 50, *, include_archived: bool = True) -> list[dict[str, Any]]:
        with self._connect() as con:
            where_clause = "" if include_archived else "WHERE COALESCE(is_archived, 0) = 0"
            cur = con.execute(
                f"""
                SELECT
                    question_set_id,
                    name,
                    config_json,
                    created_at,
                    updated_at,
                    last_run_at,
                    last_run_mode,
                    notes,
                    COALESCE(is_archived, 0) AS is_archived,
                    archived_at
                FROM question_set
                {where_clause}
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def set_question_set_archived(self, question_set_id: str, archived: bool) -> None:
        if not question_set_id:
            return
        now = time.time()
        with self._connect() as con:
            con.execute(
                """
                UPDATE question_set
                SET
                    is_archived = ?,
                    archived_at = ?,
                    updated_at = ?
                WHERE question_set_id = ?
                """,
                (
                    1 if archived else 0,
                    now if archived else None,
                    now,
                    question_set_id,
                ),
            )

    def save_cluster_brief(
        self,
        *,
        cluster_kind: str,
        cluster_key: str,
        cluster_label: str,
        source_run_ids_json: str,
        source_result_ids_json: str,
        query_count: int,
        generated_title: str,
        brief_json: str,
        brief_id: str | None = None,
    ) -> str:
        now = time.time()
        resolved_id = brief_id or f"brief_{uuid.uuid4().hex}"
        with self._connect() as con:
            existing = con.execute(
                "SELECT brief_id FROM cluster_brief WHERE brief_id = ?",
                (resolved_id,),
            ).fetchone()
            if existing:
                con.execute(
                    """
                    UPDATE cluster_brief
                    SET
                        cluster_kind = ?,
                        cluster_key = ?,
                        cluster_label = ?,
                        source_run_ids_json = ?,
                        source_result_ids_json = ?,
                        query_count = ?,
                        generated_title = ?,
                        brief_json = ?,
                        updated_at = ?
                    WHERE brief_id = ?
                    """,
                    (
                        cluster_kind,
                        cluster_key,
                        cluster_label,
                        source_run_ids_json,
                        source_result_ids_json,
                        int(query_count or 0),
                        generated_title,
                        brief_json,
                        now,
                        resolved_id,
                    ),
                )
            else:
                con.execute(
                    """
                    INSERT INTO cluster_brief (
                        brief_id,
                        cluster_kind,
                        cluster_key,
                        cluster_label,
                        source_run_ids_json,
                        source_result_ids_json,
                        query_count,
                        generated_title,
                        brief_json,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resolved_id,
                        cluster_kind,
                        cluster_key,
                        cluster_label,
                        source_run_ids_json,
                        source_result_ids_json,
                        int(query_count or 0),
                        generated_title,
                        brief_json,
                        now,
                        now,
                    ),
                )
        return resolved_id

    def get_cluster_brief(self, brief_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT *
                FROM cluster_brief
                WHERE brief_id = ?
                """,
                (brief_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_cluster_briefs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    brief_id,
                    cluster_kind,
                    cluster_key,
                    cluster_label,
                    query_count,
                    generated_title,
                    created_at,
                    updated_at
                FROM cluster_brief
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def touch_question_set_run(self, question_set_id: str, *, run_mode: str, run_at: float | None = None) -> None:
        if not question_set_id:
            return
        with self._connect() as con:
            con.execute(
                """
                UPDATE question_set
                SET last_run_at = ?, last_run_mode = ?, updated_at = ?
                WHERE question_set_id = ?
                """,
                (
                    float(run_at or time.time()),
                    run_mode,
                    time.time(),
                    question_set_id,
                ),
            )

    def save_schedule(
        self,
        *,
        question_set_id: str,
        name: str,
        weekdays_csv: str,
        time_of_day: str,
        weekly_run_count: int,
        timezone: str,
        cost_guardrail_usd: float,
        enabled: bool,
        schedule_id: str | None = None,
        execution_mode: str = "batch",
    ) -> str:
        now = time.time()
        resolved_id = schedule_id or f"sch_{uuid.uuid4().hex}"
        with self._connect() as con:
            existing = con.execute(
                "SELECT schedule_id FROM schedule_plan WHERE schedule_id = ?",
                (resolved_id,),
            ).fetchone()
            if existing:
                con.execute(
                    """
                    UPDATE schedule_plan
                    SET
                        question_set_id = ?,
                        name = ?,
                        weekdays_csv = ?,
                        time_of_day = ?,
                        weekly_run_count = ?,
                        timezone = ?,
                        execution_mode = ?,
                        enabled = ?,
                        cost_guardrail_usd = ?,
                        updated_at = ?
                    WHERE schedule_id = ?
                    """,
                    (
                        question_set_id,
                        name,
                        weekdays_csv,
                        time_of_day,
                        int(weekly_run_count),
                        timezone,
                        execution_mode,
                        1 if enabled else 0,
                        float(cost_guardrail_usd or 0.0),
                        now,
                        resolved_id,
                    ),
                )
            else:
                con.execute(
                    """
                    INSERT INTO schedule_plan (
                        schedule_id,
                        question_set_id,
                        name,
                        weekdays_csv,
                        time_of_day,
                        weekly_run_count,
                        timezone,
                        execution_mode,
                        enabled,
                        cost_guardrail_usd,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        resolved_id,
                        question_set_id,
                        name,
                        weekdays_csv,
                        time_of_day,
                        int(weekly_run_count),
                        timezone,
                        execution_mode,
                        1 if enabled else 0,
                        float(cost_guardrail_usd or 0.0),
                        now,
                        now,
                    ),
                )
        return resolved_id

    def get_schedule(self, schedule_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT s.*, q.name AS question_set_name
                FROM schedule_plan s
                LEFT JOIN question_set q ON q.question_set_id = s.question_set_id
                WHERE s.schedule_id = ?
                """,
                (schedule_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def delete_schedule(self, schedule_id: str) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM schedule_plan WHERE schedule_id = ?", (schedule_id,))

    def list_schedules(self, limit: int = 50, *, enabled_only: bool | None = None) -> list[dict[str, Any]]:
        where_clause = ""
        params: list[Any] = []
        if enabled_only is True:
            where_clause = "WHERE s.enabled = 1"
        elif enabled_only is False:
            where_clause = "WHERE s.enabled = 0"
        params.append(limit)
        with self._connect() as con:
            cur = con.execute(
                f"""
                SELECT
                    s.schedule_id,
                    s.question_set_id,
                    q.name AS question_set_name,
                    s.name,
                    s.weekdays_csv,
                    s.time_of_day,
                    s.weekly_run_count,
                    s.timezone,
                    s.execution_mode,
                    s.enabled,
                    s.cost_guardrail_usd,
                    s.next_run_at,
                    s.last_scheduled_slot,
                    s.last_run_at,
                    s.last_status,
                    s.last_error,
                    s.created_at,
                    s.updated_at
                FROM schedule_plan s
                LEFT JOIN question_set q ON q.question_set_id = s.question_set_id
                {where_clause}
                ORDER BY COALESCE(s.next_run_at, s.updated_at) ASC, s.updated_at DESC
                LIMIT ?
                """,
                params,
            )
            return [dict(row) for row in cur.fetchall()]

    def update_schedule_runtime(
        self,
        schedule_id: str,
        *,
        next_run_at: float | None = None,
        last_scheduled_slot: str | None = None,
        last_run_at: float | None = None,
        last_status: str | None = None,
        last_error: str | None = None,
    ) -> None:
        updates: list[str] = ["updated_at = ?"]
        params: list[Any] = [time.time()]
        if next_run_at is not None:
            updates.append("next_run_at = ?")
            params.append(float(next_run_at))
        if last_scheduled_slot is not None:
            updates.append("last_scheduled_slot = ?")
            params.append(last_scheduled_slot)
        if last_run_at is not None:
            updates.append("last_run_at = ?")
            params.append(float(last_run_at))
        if last_status is not None:
            updates.append("last_status = ?")
            params.append(last_status)
        if last_error is not None:
            updates.append("last_error = ?")
            params.append(last_error)
        params.append(schedule_id)
        with self._connect() as con:
            con.execute(
                f"""
                UPDATE schedule_plan
                SET {", ".join(updates)}
                WHERE schedule_id = ?
                """,
                params,
            )

    def claim_schedule_dispatch(self, schedule_id: str, slot_key: str, *, scheduled_for: float) -> bool:
        if not schedule_id or not slot_key:
            return False
        now = time.time()
        with self._connect() as con:
            cur = con.execute(
                """
                INSERT OR IGNORE INTO schedule_dispatch (
                    dispatch_id,
                    schedule_id,
                    slot_key,
                    scheduled_for,
                    status,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"sdp_{uuid.uuid4().hex}",
                    schedule_id,
                    slot_key,
                    float(scheduled_for),
                    "claimed",
                    now,
                    now,
                ),
            )
            return int(cur.rowcount or 0) > 0

    def update_schedule_dispatch(
        self,
        schedule_id: str,
        slot_key: str,
        *,
        status: str,
        run_id: str | None = None,
        batch_job_id: str | None = None,
        error_text: str | None = None,
    ) -> None:
        if not schedule_id or not slot_key:
            return
        updates = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, time.time()]
        if run_id is not None:
            updates.append("run_id = ?")
            params.append(run_id)
        if batch_job_id is not None:
            updates.append("batch_job_id = ?")
            params.append(batch_job_id)
        if error_text is not None:
            updates.append("error_text = ?")
            params.append(error_text)
        params.extend([schedule_id, slot_key])
        with self._connect() as con:
            con.execute(
                f"""
                UPDATE schedule_dispatch
                SET {", ".join(updates)}
                WHERE schedule_id = ? AND slot_key = ?
                """,
                params,
            )

    def create_run_session(
        self,
        repeat_count: int,
        model_name: str,
        prompt_cache_key: str,
        *,
        run_mode: str = "manual",
        config_json: str = "{}",
        question_set_id: str = "",
        question_set_name: str = "",
        schedule_id: str = "",
        scheduled_for: float | None = None,
        batch_submitted_at: float | None = None,
    ) -> str:
        run_id = f"run_{uuid.uuid4().hex}"
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO run_session (
                    run_id,
                    started_at,
                    repeat_count,
                    model_name,
                    prompt_cache_key,
                    run_mode,
                    config_json,
                    question_set_id,
                    question_set_name,
                    schedule_id,
                    scheduled_for,
                    batch_submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    time.time(),
                    repeat_count,
                    model_name,
                    prompt_cache_key,
                    run_mode,
                    config_json,
                    question_set_id,
                    question_set_name,
                    schedule_id,
                    scheduled_for,
                    batch_submitted_at,
                ),
            )
        return run_id

    def finish_run_session(self, run_id: str) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE run_session SET finished_at = ? WHERE run_id = ?",
                (time.time(), run_id),
            )

    def save_keyword_result(
        self,
        run_id: str,
        iteration_index: int,
        result: Any,
        error_text: str = "",
        *,
        query_plan_id: str = "",
        display_query_raw: str = "",
        executed_query: str = "",
        executed_query_index: int | None = None,
    ) -> str:
        result_id = f"res_{uuid.uuid4().hex}"
        output_json = result.output_json or {}
        query_display_raw = str(display_query_raw or result.keyword_raw or output_json.get("keyword_raw") or "").strip()
        executed_query_raw = str(executed_query or result.keyword_raw or output_json.get("keyword_raw") or "").strip()
        analysis_context = output_json.get("analysis_context") or {}
        if isinstance(analysis_context, dict):
            analysis_context = dict(analysis_context)
        else:
            analysis_context = {}
        analysis_context.update(
            {
                "user_query_raw": query_display_raw,
                "executed_query": executed_query_raw,
                "executed_query_index": int(executed_query_index or 1),
            }
        )
        output_json["analysis_context"] = analysis_context
        output_json["keyword_raw"] = executed_query_raw
        output_json["keyword_norm"] = result.keyword_norm or executed_query_raw
        usage = result.usage or {}
        cached_tokens = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        answer_text = str(output_json.get("answer_text") or "").strip()
        citations = output_json.get("citations") if isinstance(output_json.get("citations"), list) else []
        citations_json = json.dumps(citations, ensure_ascii=False)
        structured = infer_answer_structure(
            keyword=executed_query_raw,
            answer_text=answer_text,
            citations=citations,
            source_items=[
                {
                    "url": str(source.url or "").strip(),
                    "title": str(source.title or "").strip(),
                }
                for source in result.sources or []
            ],
            payload=output_json,
            analysis_context=output_json.get("analysis_context") or {},
        )
        score_fields = build_deterministic_score_fields(output_json, structured)
        output_json["raw_llm_score"] = score_fields["raw_llm_score"]
        output_json["deterministic_score"] = score_fields["deterministic_score"]
        output_json["visibility_score"] = score_fields["visibility_score"]
        output_json["target_domain_hit"] = bool(structured["owned_domain_hit"])
        output_json["brand_mention_hit"] = bool(structured["owned_brand_hit"])
        output_json["owned_citation_count"] = int(structured["owned_citation_count"])
        output_json["owned_citation_share"] = float(structured["owned_citation_share"])
        output_json["external_only_result"] = bool(structured["external_only_result"])
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO keyword_result (
                    result_id,
                    run_id,
                    analyzed_at,
                    iteration_index,
                    keyword_raw,
                    keyword_norm,
                    answer_snapshot,
                    answer_text,
                    citations_json,
                    mentioned_brands_json,
                    citation_domains_json,
                    owned_mention_hit,
                    competitor_mention_hit,
                    answer_type_key,
                    answer_type_label,
                    output_text,
                    output_json,
                    visibility_score,
                    raw_llm_score,
                    deterministic_score,
                    input_tokens,
                    cached_tokens,
                    output_tokens,
                    web_search_calls,
                    estimated_cost_usd,
                    target_domain_hit,
                    brand_mention_hit,
                    owned_citation_count,
                    owned_citation_share,
                    external_only_result,
                    source_count,
                    error_text,
                    query_plan_id,
                    executed_query,
                    executed_query_norm,
                    executed_query_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    run_id,
                    time.time(),
                    iteration_index,
                    query_display_raw,
                    normalize_text(query_display_raw),
                    output_json.get("answer_snapshot", ""),
                    answer_text,
                    citations_json,
                    json.dumps(structured["mentioned_brands"], ensure_ascii=False),
                    json.dumps(structured["citation_domains"], ensure_ascii=False),
                    1 if structured["owned_mention_hit"] else 0,
                    1 if structured["competitor_mention_hit"] else 0,
                    structured["answer_type_key"],
                    structured["answer_type_label"],
                    result.output_text,
                    json.dumps(output_json, ensure_ascii=False),
                    score_fields["visibility_score"],
                    score_fields["raw_llm_score"],
                    score_fields["deterministic_score"],
                    int(usage.get("input_tokens") or 0),
                    cached_tokens,
                    int(usage.get("output_tokens") or 0),
                    int(result.web_search_calls or 0),
                    float(result.estimated_cost_usd or 0.0),
                    1 if structured["owned_domain_hit"] else 0,
                    1 if structured["owned_brand_hit"] else 0,
                    int(structured["owned_citation_count"] or 0),
                    float(structured["owned_citation_share"] or 0.0),
                    1 if structured["external_only_result"] else 0,
                    len(result.sources or []),
                    error_text,
                    query_plan_id,
                    executed_query_raw,
                    normalize_text(executed_query_raw),
                    int(executed_query_index or 1),
                ),
            )
            for source in result.sources or []:
                con.execute(
                    """
                    INSERT INTO source_url (source_id, result_id, url, title, kind)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (f"src_{uuid.uuid4().hex}", result_id, source.url, source.title, source.kind),
                )
        return result_id

    def create_batch_job(
        self,
        *,
        batch_job_id: str,
        run_id: str,
        provider_key: str,
        status: str,
        endpoint: str,
        completion_window: str,
        model_name: str,
        repeat_count: int,
        request_count: int,
        input_file_id: str,
        output_file_id: str = "",
        error_file_id: str = "",
        config_json: str,
        metadata_json: str,
        request_counts_total: int = 0,
        request_counts_completed: int = 0,
        request_counts_failed: int = 0,
        reserved_cost_usd: float = 0.0,
        items: list[dict[str, Any]],
    ) -> None:
        now = time.time()
        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO batch_job (
                    batch_job_id,
                    run_id,
                    provider_key,
                    status,
                    endpoint,
                    completion_window,
                    model_name,
                    repeat_count,
                    request_count,
                    input_file_id,
                    output_file_id,
                    error_file_id,
                    config_json,
                    metadata_json,
                    created_at,
                    updated_at,
                    submitted_at,
                    reserved_cost_usd,
                    request_counts_total,
                    request_counts_completed,
                    request_counts_failed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_job_id,
                    run_id,
                    provider_key,
                    status,
                    endpoint,
                    completion_window,
                    model_name,
                    repeat_count,
                    request_count,
                    input_file_id,
                    output_file_id,
                    error_file_id,
                    config_json,
                    metadata_json,
                    now,
                    now,
                    now,
                    float(reserved_cost_usd or 0.0),
                    request_counts_total,
                    request_counts_completed,
                    request_counts_failed,
                ),
            )
            for item in items:
                con.execute(
                    """
                    INSERT INTO batch_job_item (
                        item_id,
                        batch_job_id,
                        custom_id,
                        keyword_raw,
                        keyword_norm,
                        iteration_index,
                        query_plan_id,
                        user_query_raw,
                        executed_query,
                        executed_query_index,
                        request_body_json,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"bji_{uuid.uuid4().hex}",
                        batch_job_id,
                        item["custom_id"],
                        item["keyword_raw"],
                        item["keyword_norm"],
                        int(item["iteration_index"]),
                        str(item.get("query_plan_id") or ""),
                        str(item.get("user_query_raw") or item["keyword_raw"]),
                        str(item.get("executed_query") or item["keyword_raw"]),
                        int(item.get("executed_query_index") or 1),
                        item["request_body_json"],
                        "queued",
                        now,
                        now,
                    ),
                )

    def update_batch_job_status(
        self,
        batch_job_id: str,
        *,
        status: str,
        output_file_id: str = "",
        error_file_id: str = "",
        request_counts_total: int = 0,
        request_counts_completed: int = 0,
        request_counts_failed: int = 0,
        last_error: str = "",
    ) -> None:
        now = time.time()
        with self._connect() as con:
            con.execute(
                """
                UPDATE batch_job
                SET
                    status = ?,
                    output_file_id = ?,
                    error_file_id = ?,
                    request_counts_total = ?,
                    request_counts_completed = ?,
                    request_counts_failed = ?,
                    last_error = ?,
                    updated_at = ?,
                    last_checked_at = ?
                WHERE batch_job_id = ?
                """,
                (
                    status,
                    output_file_id,
                    error_file_id,
                    int(request_counts_total or 0),
                    int(request_counts_completed or 0),
                    int(request_counts_failed or 0),
                    last_error,
                    now,
                    now,
                    batch_job_id,
                ),
            )

    def mark_batch_job_item_processed(
        self,
        batch_job_id: str,
        custom_id: str,
        *,
        status: str,
        response_status_code: int | None = None,
        remote_request_id: str = "",
        imported_result_id: str = "",
        error_text: str = "",
    ) -> None:
        with self._connect() as con:
            con.execute(
                """
                UPDATE batch_job_item
                SET
                    status = ?,
                    response_status_code = ?,
                    remote_request_id = ?,
                    imported_result_id = ?,
                    error_text = ?,
                    updated_at = ?
                WHERE batch_job_id = ? AND custom_id = ?
                """,
                (
                    status,
                    response_status_code,
                    remote_request_id,
                    imported_result_id,
                    error_text,
                    time.time(),
                    batch_job_id,
                    custom_id,
                ),
            )

    def mark_batch_job_imported(
        self,
        batch_job_id: str,
        *,
        imported_result_count: int,
        imported_error_count: int,
    ) -> None:
        with self._connect() as con:
            con.execute(
                """
                UPDATE batch_job
                SET
                    imported_at = ?,
                    imported_result_count = ?,
                    imported_error_count = ?,
                    updated_at = ?
                WHERE batch_job_id = ?
                """,
                (
                    time.time(),
                    int(imported_result_count or 0),
                    int(imported_error_count or 0),
                    time.time(),
                    batch_job_id,
                ),
            )

    def get_batch_job(self, batch_job_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT b.*, COALESCE(r.run_mode, 'manual') AS run_mode, r.question_set_name, r.schedule_id
                FROM batch_job b
                LEFT JOIN run_session r ON r.run_id = b.run_id
                WHERE b.batch_job_id = ?
                """,
                (batch_job_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_batch_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    b.batch_job_id,
                    b.run_id,
                    b.provider_key,
                    b.status,
                    b.endpoint,
                    b.completion_window,
                    b.model_name,
                    b.repeat_count,
                    b.request_count,
                    b.input_file_id,
                    b.output_file_id,
                    b.error_file_id,
                    b.submitted_at,
                    b.created_at,
                    b.updated_at,
                    b.last_checked_at,
                    b.imported_at,
                    b.imported_result_count,
                    b.imported_error_count,
                    b.reserved_cost_usd,
                    b.request_counts_total,
                    b.request_counts_completed,
                    b.request_counts_failed,
                    b.last_error,
                    COALESCE(r.run_mode, 'manual') AS run_mode,
                    r.question_set_name,
                    r.schedule_id
                FROM batch_job b
                LEFT JOIN run_session r ON r.run_id = b.run_id
                ORDER BY b.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_runs_for_scope(self, *, scope_kind: str, scope_id: str, limit: int = 30) -> list[dict[str, Any]]:
        if not scope_id:
            return []
        if scope_kind == "question_set":
            where_clause = "WHERE r.question_set_id = ?"
        elif scope_kind == "schedule":
            where_clause = "WHERE r.schedule_id = ?"
        else:
            return []
        with self._connect() as con:
            cur = con.execute(
                f"""
                SELECT
                    r.run_id,
                    r.started_at,
                    r.finished_at,
                    r.repeat_count,
                    r.model_name,
                    COALESCE(r.run_mode, 'manual') AS run_mode,
                    r.question_set_id,
                    r.question_set_name,
                    r.schedule_id,
                    r.scheduled_for,
                    r.batch_submitted_at,
                    COUNT(k.result_id) AS result_count
                FROM run_session r
                LEFT JOIN keyword_result k ON k.run_id = r.run_id
                {where_clause}
                GROUP BY r.run_id
                ORDER BY r.started_at DESC
                LIMIT ?
                """,
                (scope_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_batch_job_items(self, batch_job_id: str) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    batch_job_id,
                    custom_id,
                    keyword_raw,
                    keyword_norm,
                    iteration_index,
                    query_plan_id,
                    user_query_raw,
                    executed_query,
                    executed_query_index,
                    request_body_json,
                    status,
                    response_status_code,
                    remote_request_id,
                    imported_result_id,
                    error_text,
                    created_at,
                    updated_at
                FROM batch_job_item
                WHERE batch_job_id = ?
                ORDER BY iteration_index ASC, rowid ASC
                """,
                (batch_job_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_active_batch_job_reservations(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    b.batch_job_id,
                    b.run_id,
                    b.status,
                    b.submitted_at,
                    b.created_at,
                    b.updated_at,
                    b.request_count,
                    b.imported_result_count,
                    b.imported_error_count,
                    b.request_counts_total,
                    b.request_counts_completed,
                    b.request_counts_failed,
                    b.output_file_id,
                    b.error_file_id,
                    b.config_json,
                    b.reserved_cost_usd,
                    COALESCE(r.run_mode, 'manual') AS run_mode
                FROM batch_job b
                LEFT JOIN run_session r ON r.run_id = b.run_id
                WHERE COALESCE(b.request_count, 0) > COALESCE(b.imported_result_count, 0) + COALESCE(b.imported_error_count, 0)
                ORDER BY COALESCE(b.submitted_at, b.created_at, b.updated_at) DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_scheduled_batch_jobs_for_poll(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    b.*,
                    r.run_mode,
                    r.question_set_id,
                    r.question_set_name,
                    r.schedule_id
                FROM batch_job b
                INNER JOIN run_session r ON r.run_id = b.run_id
                WHERE r.run_mode = 'scheduled'
                  AND (b.imported_result_count + b.imported_error_count) < b.request_count
                ORDER BY COALESCE(b.last_checked_at, 0) ASC, b.updated_at ASC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_recent_results(self, limit: int = 120) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    k.result_id,
                    k.run_id,
                    k.analyzed_at,
                    k.iteration_index,
                    k.keyword_raw,
                    k.keyword_norm,
                    k.answer_snapshot,
                    k.answer_text,
                    k.citations_json,
                    k.mentioned_brands_json,
                    k.citation_domains_json,
                    k.owned_mention_hit,
                    k.competitor_mention_hit,
                    k.answer_type_key,
                    k.answer_type_label,
                    k.output_json,
                    k.visibility_score,
                    k.raw_llm_score,
                    k.deterministic_score,
                    k.estimated_cost_usd,
                    k.input_tokens,
                    k.cached_tokens,
                    k.output_tokens,
                    k.web_search_calls,
                    k.target_domain_hit,
                    k.brand_mention_hit,
                    k.owned_citation_count,
                    k.owned_citation_share,
                    k.external_only_result,
                    k.source_count,
                    k.error_text,
                    k.query_plan_id,
                    k.executed_query,
                    k.executed_query_norm,
                    k.executed_query_index,
                    COALESCE(r.run_mode, 'manual') AS run_mode,
                    r.question_set_id,
                    r.question_set_name,
                    r.schedule_id,
                    r.finished_at AS run_finished_at,
                    r.model_name AS run_model_name,
                    r.config_json AS run_config_json,
                    r.started_at AS run_started_at,
                    r.scheduled_for,
                    r.batch_submitted_at,
                    qp.user_query_short,
                    qp.query_was_shortened,
                    qp.shortening_note,
                    qp.expanded_queries_json,
                    qp.prompt_taxonomy_json,
                    qp.expansion_mode,
                    qp.expansion_signature,
                    qp.scheduler_mode,
                    qp.scheduled_dispatch_at,
                    qp.provider_batch_mode,
                    qp.provider_batch_id,
                    qp.provider_cache_policy
                FROM keyword_result k
                LEFT JOIN run_session r ON r.run_id = k.run_id
                LEFT JOIN query_plan qp ON qp.query_plan_id = k.query_plan_id
                ORDER BY k.analyzed_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_results_for_runs(self, run_ids: list[str]) -> list[dict[str, Any]]:
        resolved_ids = [str(run_id or "") for run_id in run_ids if str(run_id or "")]
        if not resolved_ids:
            return []
        placeholders = ",".join("?" for _ in resolved_ids)
        with self._connect() as con:
            cur = con.execute(
                f"""
                SELECT
                    k.result_id,
                    k.run_id,
                    k.analyzed_at,
                    k.iteration_index,
                    k.keyword_raw,
                    k.keyword_norm,
                    k.answer_snapshot,
                    k.answer_text,
                    k.citations_json,
                    k.mentioned_brands_json,
                    k.citation_domains_json,
                    k.owned_mention_hit,
                    k.competitor_mention_hit,
                    k.answer_type_key,
                    k.answer_type_label,
                    k.output_json,
                    k.visibility_score,
                    k.raw_llm_score,
                    k.deterministic_score,
                    k.estimated_cost_usd,
                    k.input_tokens,
                    k.cached_tokens,
                    k.output_tokens,
                    k.web_search_calls,
                    k.target_domain_hit,
                    k.brand_mention_hit,
                    k.owned_citation_count,
                    k.owned_citation_share,
                    k.external_only_result,
                    k.source_count,
                    k.error_text,
                    k.query_plan_id,
                    k.executed_query,
                    k.executed_query_norm,
                    k.executed_query_index,
                    COALESCE(r.run_mode, 'manual') AS run_mode,
                    r.question_set_id,
                    r.question_set_name,
                    r.schedule_id,
                    r.started_at AS run_started_at,
                    r.scheduled_for,
                    r.batch_submitted_at,
                    qp.user_query_short,
                    qp.query_was_shortened,
                    qp.shortening_note,
                    qp.expanded_queries_json,
                    qp.prompt_taxonomy_json,
                    qp.expansion_mode,
                    qp.expansion_signature,
                    qp.scheduler_mode,
                    qp.scheduled_dispatch_at,
                    qp.provider_batch_mode,
                    qp.provider_batch_id,
                    qp.provider_cache_policy
                FROM keyword_result k
                LEFT JOIN run_session r ON r.run_id = k.run_id
                LEFT JOIN query_plan qp ON qp.query_plan_id = k.query_plan_id
                WHERE k.run_id IN ({placeholders})
                ORDER BY k.analyzed_at DESC
                """,
                resolved_ids,
            )
            return [dict(row) for row in cur.fetchall()]

    def list_sources(self, result_id: str) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT url, title, kind
                FROM source_url
                WHERE result_id = ?
                ORDER BY rowid ASC
                """,
                (result_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_run_history(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                """
                SELECT
                    r.run_id,
                    r.started_at,
                    r.finished_at,
                    r.repeat_count,
                    r.model_name,
                    COALESCE(r.run_mode, 'manual') AS run_mode,
                    r.question_set_id,
                    r.question_set_name,
                    r.schedule_id,
                    r.scheduled_for,
                    r.batch_submitted_at,
                    COUNT(k.result_id) AS result_count,
                    COALESCE(SUM(k.estimated_cost_usd), 0) AS total_cost_usd
                FROM run_session r
                LEFT JOIN keyword_result k ON k.run_id = r.run_id
                GROUP BY r.run_id
                ORDER BY r.started_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
