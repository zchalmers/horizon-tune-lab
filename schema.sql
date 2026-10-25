-- Expected read-only SQLite schema. This file contains no game-derived rows.
CREATE TABLE cars (id INTEGER PRIMARY KEY, make TEXT, car_name TEXT, full_name TEXT UNIQUE, year INTEGER, car_type TEXT, class_letter TEXT, pi INTEGER, country TEXT);
CREATE VIRTUAL TABLE cars_fts USING fts5(make, car_name, full_name, content='cars', content_rowid='id');
CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT, section TEXT, content TEXT);
CREATE VIRTUAL TABLE doc_fts USING fts5(title, section, content, content_rowid='id');
CREATE TABLE recommendations (id INTEGER PRIMARY KEY, symptom TEXT, phase TEXT, balance TEXT, drivetrain TEXT, priority INTEGER, setting TEXT, direction TEXT, target_end TEXT, rationale TEXT);
CREATE TABLE tuning_controls (id INTEGER PRIMARY KEY, display_name TEXT);
CREATE TABLE tuning_effects (id INTEGER PRIMARY KEY, control_id INTEGER, action TEXT, effect_key TEXT, effect_direction TEXT, phase TEXT, drivetrain TEXT, magnitude TEXT, strength INTEGER, evidence TEXT);
CREATE TABLE tuning_interactions (id INTEGER PRIMARY KEY, from_control_id INTEGER, to_control_id INTEGER, interaction_type TEXT, rationale TEXT, evidence TEXT);
CREATE TABLE tuning_baselines (id INTEGER PRIMARY KEY, control_id INTEGER, baseline_type TEXT, value_min REAL, value_max REAL, value_text TEXT, unit TEXT, drivetrain TEXT, evidence TEXT);
CREATE TABLE builds (id INTEGER PRIMARY KEY, car_id INTEGER, car_name TEXT, car_class TEXT, drivetrain TEXT, pi_class TEXT, build_title TEXT, author TEXT, share_code TEXT);
