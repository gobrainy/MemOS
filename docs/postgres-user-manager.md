# Postgres User Manager

The Postgres-backed user manager is available when the application runs with the
`MOS_USER_MANAGER=postgres` environment variable. When enabled, MemOS uses the
`memos` schema inside the configured Postgres database (created automatically if
missing) and shares the same schema definition as the SQLite and MySQL user
manager implementations.

## Environment variables

Set the following variables to control the Postgres connection:

- `MOS_USER_MANAGER=postgres` – switch the backend from the default SQLite
- `MOS_POSTGRES_HOST` (default: `localhost`)
- `MOS_POSTGRES_PORT` (default: `5432`)
- `MOS_POSTGRES_USERNAME` (default: `postgres`)
- `MOS_POSTGRES_PASSWORD` (default: empty)
- `MOS_POSTGRES_DATABASE` (default: `memos_users`)
- `MOS_POSTGRES_SCHEMA` (default: `memos`)
- `MOS_POSTGRES_SSLMODE` (optional; e.g. `require`)

Optional: use `MOS_USER_MANAGER_BACKEND=postgres` for backward compatibility with
existing deployment scripts. The legacy `POSTGRES_*` variables are still read as
fallbacks but the `MOS_`-prefixed variables take precedence.

## Database bootstrap

Run the SQL script whenever you provision a new Postgres instance to ensure the
schema exists:

```bash
psql "postgresql://${MOS_POSTGRES_USERNAME}:${MOS_POSTGRES_PASSWORD}@${MOS_POSTGRES_HOST}:${MOS_POSTGRES_PORT}/${MOS_POSTGRES_DATABASE}" \
  -f sql/postgres-user.sql
```

The script contains idempotent `IF NOT EXISTS` statements so it can be executed
multiple times without side effects.
