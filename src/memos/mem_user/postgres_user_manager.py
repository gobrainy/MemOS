"""Postgres-backed user manager for MemOS."""

from __future__ import annotations

import string

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import quoted_name

from memos.log import get_logger
from memos.mem_user.mysql_user_manager import Base, MySQLUserManager

logger = get_logger(__name__)

_ALLOWED_SCHEMA_CHARS = set(string.ascii_letters + string.digits + "_")


def _validate_schema(schema: str) -> str:
    if not schema:
        raise ValueError("Postgres schema name cannot be empty")
    if schema[0] not in string.ascii_letters + "_":
        raise ValueError("Postgres schema name must start with a letter or underscore")
    if any(char not in _ALLOWED_SCHEMA_CHARS for char in schema):
        raise ValueError("Postgres schema name may only contain letters, numbers, and underscores")
    return schema


class PostgresUserManager(MySQLUserManager):
    """User management system for MemOS using Postgres."""

    def __init__(
        self,
        user_id: str = "root",
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "",
        database: str = "memos_users",
        schema: str = "memos",
        sslmode: str | None = None,
    ) -> None:
        schema = _validate_schema(schema)
        query: dict[str, str] = {"options": f"-csearch_path={schema}"}
        if sslmode:
            query["sslmode"] = sslmode

        connection_url = URL.create(
            "postgresql+psycopg2",
            username=username or None,
            password=password or None,
            host=host,
            port=port,
            database=database,
            query=query,
        )

        self.schema = schema
        self.connection_url = str(connection_url)
        self.engine = create_engine(connection_url, echo=False, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        print(
            "[PostgresUserManager.__init__] connection params: "
            f"host={host}, port={port}, database={database}, schema={schema}"
        )

        def _set_search_path(dbapi_connection, _):
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema}"')

        event.listen(self.engine, "connect", _set_search_path)

        with self.engine.begin() as connection:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {quoted_name(schema, True)}"))

        # Create tables inside the configured schema
        Base.metadata.create_all(bind=self.engine)

        # Initialize with root user if no users exist
        self._init_root_user(user_id)

        logger.info(
            "PostgresUserManager initialized with database at %s:%s/%s (schema '%s')",
            host,
            port,
            database,
            schema,
        )

    def close(self) -> None:
        if hasattr(self, "engine"):
            self.engine.dispose()
            logger.info("PostgresUserManager database connections closed")
