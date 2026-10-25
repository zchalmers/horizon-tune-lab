"""Create a synthetic database for local demonstrations.

The rows are invented examples and are not game data.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema.sql"
DEFAULT_OUTPUT = ROOT / "sample-data" / "forza_tuning_sample.db"


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with sqlite3.connect(output) as conn:
        conn.executescript(SCHEMA.read_text())
        conn.execute("INSERT INTO cars VALUES (1, 'Example', 'Comet 400', 'Example Comet 400', 2088, 'Coupe', 'S1', 825, 'Fictional')")
        conn.execute("INSERT INTO cars_fts(rowid, make, car_name, full_name) VALUES (1, 'Example', 'Comet 400', 'Example Comet 400')")
        conn.execute("INSERT INTO documents VALUES (1, 'Exit balance', 'Differential', 'Synthetic note about reducing front axle pull when an AWD car pushes on exit.')")
        conn.execute("INSERT INTO doc_fts(rowid, title, section, content) VALUES (1, 'Exit balance', 'Differential', 'Synthetic note about reducing front axle pull when an AWD car pushes on exit.')")
        conn.execute("INSERT INTO recommendations VALUES (1, 'understeer', 'exit', 'understeer', 'AWD', 1, 'Front differential acceleration', 'reduce slightly', 'lower', 'Synthetic example: reducing front pull can help the car rotate on throttle.')")
        conn.execute("INSERT INTO tuning_controls VALUES (1, 'Front differential acceleration')")
        conn.execute("INSERT INTO tuning_effects VALUES (1, 1, 'reduce', 'understeer', 'reduces', 'exit', 'AWD', 'medium', 3, 'Synthetic example evidence.')")
        conn.execute("INSERT INTO tuning_baselines VALUES (1, 1, 'range', 10, 30, NULL, 'percent', 'AWD', 'Synthetic baseline only.')")
    print(output)


if __name__ == '__main__':
    main()
