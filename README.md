# Horizon Tune Lab

A deterministic tuning-advice service for a racing game, built with FastAPI and React.

It turns handling symptoms into a short, ordered tuning plan using a read-only SQLite index of car and tuning knowledge. The service does not call an LLM or require API keys at runtime, so the same request against the same database produces the same advice. This makes answers easier to inspect, cheaper to operate, and suitable for a public tool with a narrow purpose.

## Architecture

The React and TypeScript frontend collects a handling question and optional build details, then calls the FastAPI API. The API validates and rate-limits requests, extracts symptom and drivetrain keywords, and queries a read-only SQLite database for recommendations, tuning effects, interactions, baselines, and car matches. A deterministic answer engine formats those records into a consistent response. The Docker image builds the frontend and serves its static files from the API process.

## Notable engineering decisions

- The advice engine uses fixed symptom maps, database retrieval, and templates instead of generative output. There is no model dependency or runtime secret.
- SQLite is opened with `mode=ro` and `immutable=1`. Query helpers only issue reads, which enforces the database contract at the connection layer.
- Each answer keeps the same practical shape: likely cause, relevant interactions as evidence, ordered steps, and watch-fors. The UI presents the ordered plan first and keeps supporting evidence available on demand.
- The API rejects common prompt-injection and off-topic requests, limits request sizes and fields, and applies an in-memory per-address limiter to tuning endpoints.
- The container runs as a non-root user with a read-only filesystem. The supplied compose file mounts the database read-only.

## Stack

- Python 3.11, FastAPI, Pydantic, and SQLite FTS5
- React 18, TypeScript, Vite, and Tailwind CSS
- Docker multi-stage build and Docker Compose
- pytest and HTTPX test tooling

## Running locally

The repository does not include game-derived data. Generate the included synthetic demonstration database first. It has obviously fictional rows and is ignored by Git.

```bash
python3 scripts/create_sample_db.py
cd api
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
FORZA_DB_PATH=../sample-data/forza_tuning_sample.db uvicorn app.main:app --reload
```

In a second terminal, run the frontend:

```bash
cd web
npm ci
npm run dev
```

For the containerized demonstration, generate the sample database and then run `docker compose up --build`. To use a real index, set `FORZA_DB_PATH` to an approved local database file. It remains a read-only mount and must not be committed.

## Public deployment posture

The service has no accounts, no write APIs, and no runtime API keys. A public deployment should terminate HTTPS at a reverse proxy, enforce an edge rate limit in addition to the app-level limiter, and mount only the approved read-only database. See [SECURITY.md](SECURITY.md) for the deployment checks.
