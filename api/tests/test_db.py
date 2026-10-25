"""Tests for DB query helpers."""
from __future__ import annotations

import os
import pytest


def test_search_cars_returns_results(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    from app import db
    results = db.search_cars("Ferrari", limit=5)
    assert isinstance(results, list)


def test_get_recommendations_returns_list(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    from app import db
    results = db.get_recommendations(["understeer"], "AWD")
    assert isinstance(results, list)


def test_get_recommendations_drivetrain_filter(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    from app import db
    results = db.get_recommendations(["understeer"], "RWD")
    assert isinstance(results, list)


def test_search_documents_returns_list(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    from app import db
    results = db.search_documents("understeer", limit=3)
    assert isinstance(results, list)


def test_db_health_ok(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    from app import db
    status = db.check_db_health()
    assert status == "ok"


def test_db_health_bad_path(db_path):
    import importlib
    saved = os.environ.get("FORZA_DB_PATH")
    os.environ["FORZA_DB_PATH"] = "/nonexistent/path.db"
    from app import db as db_mod
    importlib.reload(db_mod)
    status = db_mod.check_db_health()
    assert "error" in status
    # Restore
    if saved:
        os.environ["FORZA_DB_PATH"] = saved
    else:
        os.environ.pop("FORZA_DB_PATH", None)


def test_no_write_sql(db_path):
    """Verify that write SQL against a mode=ro connection raises OperationalError."""
    os.environ["FORZA_DB_PATH"] = db_path
    import importlib
    import sqlite3
    from app import db as db_mod
    importlib.reload(db_mod)
    with db_mod.get_db() as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO cars(id) VALUES(9999)")
