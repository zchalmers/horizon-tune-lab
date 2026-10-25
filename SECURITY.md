# Security Contract

This service accepts public tuning questions and treats requests as untrusted.

## Boundaries

- The SQLite database is mounted read-only and opened with SQLite read-only mode.
- The API has no write endpoints and does not require runtime API keys.
- The container runs as a non-root user with a read-only filesystem. Its temporary directory can be a tmpfs mount.
- Errors returned to clients are generic. Internal details are logged only by the running service.

## Request handling

- Questions and context fields have length limits.
- Requests that ask for secrets, configuration, files, commands, or unrelated tasks receive a short refusal.
- The API uses an in-memory per-address limiter for the tuning endpoints. A public deployment should also apply an edge rate limit.
- Response headers disable framing and content sniffing, restrict browser connections to the same origin, and discourage indexing.

## Deployment checks

- Mount only an approved game-data database at `FORZA_DB_PATH` and make that mount read-only.
- Keep the database out of images, source control, browser bundles, and logs.
- Put the service behind an HTTPS reverse proxy with a public rate limit.
- Run the included tests and inspect `/api/health` after deployment.
