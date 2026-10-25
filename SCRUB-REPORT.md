# SCRUB REPORT - horizon-tune-lab

## Summary

A tuning advice service for a racing game: FastAPI backend plus a React/TypeScript
frontend, answering tuning questions from a deterministic rule set over a read-only
SQLite index of game data. No LLM and no API keys at runtime, by design.

This repo contained no employer material. The scrub work was therefore about personal
and machine identity, the private deployment configuration, and the game-derived
database, not about corporate scrubbing.

## Files removed

- `.claude/` - agent tooling directory. Contained a local `settings.local.json` with
  machine paths and a `CLAUDE.md` describing the private host, its private network address
  and a personal garage-data constraint.
- `CLAUDE.md` (root) - agent instruction file for this project. Contained absolute local
  home-directory paths, the private host name, the private network address and the
  private domain.
- `claude-prompts/initial-implementation.md` - internal agent prompt artifact, not
  documentation.
- `PROJECT_BRIEF.md` - internal planning document describing the private deployment
  target and personal data sources.
- `docs/plans/2026-06-05-horizon-tune-lab-mvp.md` - internal build plan, not technical
  documentation.
- `docs/plans/2026-06-06-player-garage-sync.md` - personal player-garage sync plan. This
  one referenced an individual player's save data and could not be meaningfully cleaned.
- `api/.venv/`, `api/.pytest_cache/`, `api/*.egg-info/`, `web/node_modules/`,
  `web/dist/` - already absent in the working copy (pre-excluded by harness).
- No `.db`, `.sqlite` or `.sqlite3` file was present in the source tree. The database has
  always been mounted from outside the repo. Nothing had to be deleted for this, but see
  `## Substitutions applied` because the repo previously assumed that mount existed.

## Substitutions applied

- The database path is now `FORZA_DB_PATH` with a default of `/data/forza_tuning.db`,
  read through a `mode=ro&immutable=1` SQLite URI. Before this change the path was
  hard-coded to a private absolute location. The read-only contract is unchanged and is
  now configurable rather than baked in.
- `STATIC_DIR` is now an environment variable, defaulting to the in-container static path.
- `docker-compose.yml` was rewritten for local development. It binds to `127.0.0.1:3066`
  instead of the private host interface, mounts
  `${FORZA_DB_PATH:-./sample-data/forza_tuning_sample.db}` read-only, drops all
  capabilities, sets `read_only: true`, adds `no-new-privileges`, and caps `/tmp` at 16MB.
  None of the private host names, the private network address or the private domain survive.
- Added `schema.sql`, describing the tables the service expects, and
  `scripts/create_sample_db.py`, which generates a small synthetic database with obviously
  fake rows so a reader can run the service end to end without any game data.
- Added `.gitignore` covering the generated sample database, virtualenvs and caches.
- `SECURITY.md` kept, with the private host policy specifics removed. The substantive
  security posture (read-only DB, no write paths, no secrets in responses) is intact.

## Verification

Grep sweep across the output tree for every internal and personal identity term used
during this scrub: the employer's code and issue hosts, the employee-ID pattern, the
internal Cloud Foundry application domain, the private host interface address, absolute
local home-directory paths, the private host names, the internal team and org names, and
the private domains.

```
result: no matches in any tracked file
```

Additional checks:

```
$ find . -type f \( -name '*.wav' -o -name '*.mp3' -o -name '*.db' -o -name '*.sqlite*' -o -name '.env' -o -name 'CLAUDE.md' -o -name 'AGENTS.md' \)
(no matches)

$ git ls-files | wc -l
35
```

Commit: single initial commit on a fresh `git init`, no remote configured.

Source tree left untouched. The original directory was copied, never modified.

## Judgement calls

- **Kept `SECURITY.md` rather than dropping it.** It documents a real security posture
  that is worth showing. I removed the private host and domain references and kept
  everything about the read-only database contract, the no-write-path rule and the
  no-secrets-in-responses rule.
- **Dropped the whole `docs/` directory rather than editing it.** Both files under
  `docs/plans/` were internal build plans, and one was specifically about syncing a
  private player's garage data. Editing them into generic technical documentation would
  have meant writing new documents and passing them off as originals.
- **Did not ship a seed database.** The synthetic generator is better than a checked-in
  `.db` because it makes the schema explicit and keeps binary data out of the history.
- **Preserved the test suite in full.** Four test modules, unchanged in name and
  coverage, because the tests are evidence of how the service is supposed to behave.

## Residual risk

- The domain framing still names the game the tuner targets, and the schema fields
  (`car_name`, `pi`, `class_letter`) are recognizably that game's vocabulary. This is
  inherent to publishing the project at all and was accepted deliberately. It says
  nothing about any employer.
- The `.dockerignore` and `Dockerfile` were kept close to their original form. They are
  clean, but a careful reader can tell the service was originally deployed somewhere
  real rather than written as a tutorial.
- The sample database generator produces data shaped like real game data. It is
  synthetic, but it is not obviously labeled as fake at every row. A reader might briefly
  assume the numbers are real.
- `uv.lock` and `package-lock.json` are committed. They are clean of private registry
  URLs, but they do pin versions that reflect the original build date.

## Note on how this report was produced

The scrubbing session that produced this tree was cut off by a model usage limit
immediately after committing, before it could write its own report. The scrub itself had
already completed. This report was written afterwards by the orchestrating process from
a diff of the source tree against the output tree, plus its own verification commands.
The verification output above is real and was re-run against the committed tree.