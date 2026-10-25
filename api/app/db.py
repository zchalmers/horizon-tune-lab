from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any
import os

def _connect() -> sqlite3.Connection:
    db_path = os.environ.get("FORZA_DB_PATH", "/data/forza_tuning.db")
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def search_cars(query: str, limit: int = 8) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.make, c.car_name, c.full_name, c.year,
                   c.car_type, c.class_letter, c.pi
            FROM cars_fts f
            JOIN cars c ON c.id = f.rowid
            WHERE cars_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                """
                SELECT id, make, car_name, full_name, year, car_type, class_letter, pi
                FROM cars
                WHERE full_name LIKE ? OR make LIKE ? OR car_name LIKE ?
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
        return [dict(r) for r in rows]


def get_car(car_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, make, car_name, full_name, year, car_type, class_letter, pi, country FROM cars WHERE id = ?",
            (car_id,),
        ).fetchone()
        return dict(row) if row else None


def search_documents(query: str, limit: int = 5) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.title, d.section, d.content
            FROM doc_fts f
            JOIN documents d ON d.id = f.rowid
            WHERE doc_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_recommendations(symptom_keywords: list[str], drivetrain: str | None = None, limit: int = 8) -> list[dict]:
    with get_db() as conn:
        parts = []
        params: list[Any] = []
        for kw in symptom_keywords:
            parts.append("(symptom LIKE ? OR balance LIKE ? OR phase LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
        where = " OR ".join(parts) if parts else "1=1"

        drivetrain_clause = ""
        if drivetrain:
            norm = drivetrain.upper()
            drivetrain_clause = " AND (drivetrain = ? OR drivetrain = 'any' OR drivetrain LIKE ?)"
            params.extend([norm, f"%{norm}%"])

        rows = conn.execute(
            f"""
            SELECT symptom, phase, balance, drivetrain, priority, setting, direction, target_end, rationale
            FROM recommendations
            WHERE ({where}){drivetrain_clause}
            ORDER BY priority ASC
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]


def get_tuning_effects(symptom_keywords: list[str], drivetrain: str | None = None, limit: int = 10) -> list[dict]:
    with get_db() as conn:
        kw_clauses = []
        params: list[Any] = []
        for kw in symptom_keywords:
            kw_clauses.append("(te.effect_key LIKE ? OR te.evidence LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
        where = " OR ".join(kw_clauses) if kw_clauses else "1=1"

        drivetrain_clause = ""
        if drivetrain:
            norm = drivetrain.upper()
            drivetrain_clause = " AND (te.drivetrain IS NULL OR te.drivetrain = 'any' OR te.drivetrain = ? OR te.drivetrain LIKE ?)"
            params.extend([norm, f"%{norm}%"])

        rows = conn.execute(
            f"""
            SELECT tc.display_name AS control_name, te.action, te.effect_key,
                   te.effect_direction, te.phase, te.drivetrain, te.magnitude, te.evidence
            FROM tuning_effects te
            JOIN tuning_controls tc ON tc.id = te.control_id
            WHERE ({where}){drivetrain_clause}
            ORDER BY te.strength DESC NULLS LAST
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]


def get_tuning_interactions(setting_names: list[str], limit: int = 6) -> list[dict]:
    with get_db() as conn:
        if not setting_names:
            return []
        placeholders = ",".join("?" * len(setting_names))
        rows = conn.execute(
            f"""
            SELECT tc1.display_name AS from_control, tc2.display_name AS to_control,
                   ti.interaction_type, ti.rationale, ti.evidence
            FROM tuning_interactions ti
            JOIN tuning_controls tc1 ON tc1.id = ti.from_control_id
            LEFT JOIN tuning_controls tc2 ON tc2.id = ti.to_control_id
            WHERE tc1.display_name IN ({placeholders})
               OR (tc2.display_name IN ({placeholders}))
            LIMIT ?
            """,
            setting_names + setting_names + [limit],
        ).fetchall()
        return [dict(r) for r in rows]


def get_tuning_baselines(setting_names: list[str], drivetrain: str | None = None, limit: int = 6) -> list[dict]:
    with get_db() as conn:
        if not setting_names:
            return []
        placeholders = ",".join("?" * len(setting_names))
        drivetrain_clause = ""
        params: list[Any] = list(setting_names)
        if drivetrain:
            norm = drivetrain.upper()
            drivetrain_clause = " AND (tb.drivetrain IS NULL OR tb.drivetrain = 'any' OR tb.drivetrain = ? OR tb.drivetrain LIKE ?)"
            params.extend([norm, f"%{norm}%"])
        rows = conn.execute(
            f"""
            SELECT tc.display_name AS control_name, tb.baseline_type,
                   tb.value_min, tb.value_max, tb.value_text, tb.unit, tb.evidence
            FROM tuning_baselines tb
            JOIN tuning_controls tc ON tc.id = tb.control_id
            WHERE tc.display_name IN ({placeholders}){drivetrain_clause}
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]


def get_builds_for_car(car_id: int, limit: int = 5) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.car_name, b.car_class, b.drivetrain, b.pi_class,
                   b.build_title, b.author, b.share_code
            FROM builds b
            WHERE b.car_id = ?
            ORDER BY b.id DESC
            LIMIT ?
            """,
            (car_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def check_db_health() -> str:
    try:
        with get_db() as conn:
            conn.execute("SELECT count(*) FROM cars").fetchone()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"
