### PostgreSQL setup for MemOS

This project can use PostgreSQL for the user manager. A ready‑to‑run Docker service is provided and the schema is auto‑initialized on first start.

### Quick start (Docker Compose)

1) Create/update your `.env` in the repository root with at least:

```env
# Select backend
MEMOS_USER_MANAGER=postgres

# Connection info used by MemOS
MEMOS_POSTGRES_HOST=postgres
MEMOS_POSTGRES_PORT=5432
MEMOS_POSTGRES_USERNAME=postgres
MEMOS_POSTGRES_PASSWORD=postgres
MEMOS_POSTGRES_DATABASE=memos_users
# Optional: sslmode values like require, verify-full, etc.
# MEMOS_POSTGRES_SSLMODE=
```

2) Start services:

```bash
docker compose -f docker/docker-compose.yml up -d postgres
docker compose -f docker/docker-compose.yml up -d memos
```

The `postgres` service automatically runs `postgres-user-manager.sql` on first initialization (via `/docker-entrypoint-initdb.d/`). If the data volume already exists, the script will not re-run.

### How it works

- The `docker/docker-compose.yml` defines a `postgres` service (image `postgres:16-alpine`).
- The SQL schema file `postgres-user-manager.sql` is mounted into `/docker-entrypoint-initdb.d/01-schema.sql`, so it runs automatically on first start.
- A named volume `postgres_data` persists the database between restarts.
- The app should reach Postgres at host `postgres` (Docker network alias).

### Manual apply (only if needed)

If you ever need to re-apply the schema manually (e.g., after recreating the DB):

```bash
docker exec -i postgres-docker psql -U "$MEMOS_POSTGRES_USERNAME" -d "$MEMOS_POSTGRES_DATABASE" \
  -c "\i /docker-entrypoint-initdb.d/01-schema.sql"
```

### Environment variables

- **MEMOS_USER_MANAGER**: `postgres` to enable PostgreSQL backend.
- **MEMOS_POSTGRES_HOST**: Hostname of Postgres (in Compose: `postgres`).
- **MEMOS_POSTGRES_PORT**: Port (default `5432`).
- **MEMOS_POSTGRES_USERNAME**: Database user (default `postgres`).
- **MEMOS_POSTGRES_PASSWORD**: Database password.
- **MEMOS_POSTGRES_DATABASE**: Database name (default `memos_users`).
- **MEMOS_POSTGRES_SSLMODE**: Optional SSL mode (`require`, `verify-full`, etc.).

Set these in your root `.env`. The `memos` service already loads `../.env` in Compose.

