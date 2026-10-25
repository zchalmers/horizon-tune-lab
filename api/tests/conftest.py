from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def db_path():
    # Create a minimal synthetic fixture DB.
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.executescript("""
        CREATE TABLE cars(
            id INTEGER PRIMARY KEY, make TEXT, car_name TEXT,
            full_name TEXT UNIQUE, year INTEGER, car_type TEXT,
            car_class TEXT, pi INTEGER, class_letter TEXT,
            country TEXT, collection TEXT, add_ons TEXT, source_id INTEGER
        );
        INSERT INTO cars VALUES(1,'Ferrari','512 S','Ferrari 512 S',1970,'Sports GT',NULL,900,'S2',NULL,NULL,NULL,NULL);
        CREATE VIRTUAL TABLE cars_fts USING fts5(make, car_name, full_name, content='cars', content_rowid='id');
        INSERT INTO cars_fts(rowid, make, car_name, full_name) VALUES(1,'Ferrari','512 S','Ferrari 512 S');
        CREATE TABLE documents(id INTEGER PRIMARY KEY, source_id INTEGER, title TEXT, section TEXT, content TEXT, path TEXT);
        CREATE VIRTUAL TABLE doc_fts USING fts5(title, section, content, content='documents', content_rowid='id');
        CREATE TABLE sources(id INTEGER PRIMARY KEY, name TEXT, url TEXT, source_type TEXT);
        CREATE TABLE recommendations(
            id INTEGER PRIMARY KEY, symptom TEXT, phase TEXT, balance TEXT,
            drivetrain TEXT, priority INTEGER, setting TEXT, direction TEXT,
            target_end TEXT, rationale TEXT, source_id INTEGER
        );
        INSERT INTO recommendations VALUES(1,'exit understeer on throttle','exit','understeer','AWD/FWD',1,
            'Front ARB','Soften','front','Reduces front lateral stiffness to improve exit grip',NULL);
        INSERT INTO recommendations VALUES(2,'exit understeer on throttle','exit','understeer','AWD/FWD',2,
            'Front Springs','Soften','front','Allows more front suspension travel on exit',NULL);
        CREATE TABLE tuning_controls(
            id INTEGER PRIMARY KEY, control_type TEXT, key TEXT UNIQUE,
            display_name TEXT, category TEXT, axle TEXT, unit TEXT,
            forzafire_category TEXT, forzafire_setting TEXT,
            forzafire_part_category TEXT, forzafire_part_name TEXT,
            entity_name TEXT, aliases TEXT DEFAULT '[]', notes TEXT
        );
        INSERT INTO tuning_controls VALUES(1,'setting','front_arb','Front ARB','suspension','front',NULL,NULL,NULL,NULL,NULL,NULL,'[]',NULL);
        INSERT INTO tuning_controls VALUES(2,'setting','front_springs','Front Springs','suspension','front',NULL,NULL,NULL,NULL,NULL,NULL,'[]',NULL);
        CREATE TABLE tuning_effects(
            id INTEGER PRIMARY KEY, control_id INTEGER, action TEXT,
            effect_control_id INTEGER, effect_key TEXT, effect_direction TEXT,
            phase TEXT, drivetrain TEXT, surface TEXT, discipline TEXT,
            magnitude TEXT, condition_json TEXT DEFAULT '{}', strength INTEGER,
            recommendation_id INTEGER, source_id INTEGER, document_id INTEGER,
            evidence TEXT, confidence TEXT DEFAULT 'medium'
        );
        INSERT INTO tuning_effects VALUES(1,1,'soften',NULL,'understeer','reduces',
            'exit','AWD','tarmac',NULL,'high','{}',3,1,NULL,NULL,
            'Softer front ARB reduces lateral stiffness aiding exit traction','high');
        CREATE TABLE tuning_interactions(
            id INTEGER PRIMARY KEY, from_control_id INTEGER, from_action TEXT,
            to_control_id INTEGER, to_action TEXT, interaction_type TEXT,
            effect_key TEXT, phase TEXT, drivetrain TEXT, surface TEXT,
            discipline TEXT, condition_json TEXT DEFAULT '{}', priority INTEGER,
            rationale TEXT, source_id INTEGER, document_id INTEGER,
            evidence TEXT, confidence TEXT DEFAULT 'medium'
        );
        CREATE TABLE tuning_baselines(
            id INTEGER PRIMARY KEY, control_id INTEGER, baseline_type TEXT,
            value_min REAL, value_max REAL, value_text TEXT, unit TEXT,
            formula TEXT, phase TEXT, drivetrain TEXT, surface TEXT, discipline TEXT,
            car_type TEXT, class_letter TEXT, condition_json TEXT DEFAULT '{}',
            source_id INTEGER, document_id INTEGER, evidence TEXT, confidence TEXT DEFAULT 'medium'
        );
        CREATE TABLE builds(
            id INTEGER PRIMARY KEY, car_id INTEGER, car_name TEXT, car_class TEXT,
            drivetrain TEXT, pi_class TEXT, build_title TEXT, author TEXT, share_code TEXT
        );
        CREATE TABLE build_parts(id INTEGER PRIMARY KEY, build_id INTEGER, part_category TEXT, part_name TEXT);
        CREATE TABLE build_tuning(id INTEGER PRIMARY KEY, build_id INTEGER, category TEXT, setting TEXT, value_front REAL, value_rear REAL);
        CREATE TABLE entities(id INTEGER PRIMARY KEY, name TEXT, entity_type TEXT);
        CREATE TABLE relations(id INTEGER PRIMARY KEY, from_id INTEGER, to_id INTEGER, relation_type TEXT);
        CREATE TABLE kudosprime_car_cards(id INTEGER PRIMARY KEY, car_id INTEGER);
        CREATE VIRTUAL TABLE kudosprime_cars_fts USING fts5(content='kudosprime_car_cards', content_rowid='id');
        CREATE VIRTUAL TABLE builds_fts USING fts5(car_name, build_title, content='builds', content_rowid='id');
    """)
    conn.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture(autouse=True)
def reset_limits():
    """Clear rate-limit buckets before each test so tests don't bleed into each other."""
    try:
        from app.safety import reset_rate_limits
        reset_rate_limits()
    except ImportError:
        pass


@pytest.fixture(scope="session")
def client(db_path):
    os.environ["FORZA_DB_PATH"] = db_path
    os.environ["STATIC_DIR"] = "/nonexistent"  # disable static mount in tests

    # Import app after env is set
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
