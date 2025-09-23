from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from memos.configs.base import BaseConfig


class BaseUserManagerConfig(BaseConfig):
    """Base configuration class for user managers."""

    user_id: str = Field(default="root", description="Default user ID for initialization")


class SQLiteUserManagerConfig(BaseUserManagerConfig):
    """SQLite user manager configuration."""

    db_path: str | None = Field(
        default=None,
        description="Path to SQLite database file. If None, uses default path in MEMOS_DIR",
    )


class MySQLUserManagerConfig(BaseUserManagerConfig):
    """MySQL user manager configuration."""

    host: str = Field(default="localhost", description="MySQL server host")
    port: int = Field(default=3306, description="MySQL server port")
    username: str = Field(default="root", description="MySQL username")
    password: str = Field(default="", description="MySQL password")
    database: str = Field(default="memos_users", description="MySQL database name")
    charset: str = Field(default="utf8mb4", description="MySQL charset")


class PostgresUserManagerConfig(BaseUserManagerConfig):
    """Postgres user manager configuration."""

    model_config = ConfigDict(populate_by_name=True)

    host: str = Field(default="localhost", description="Postgres server host")
    port: int = Field(default=5432, description="Postgres server port")
    username: str = Field(default="postgres", description="Postgres username")
    password: str = Field(default="", description="Postgres password")
    database: str = Field(default="memos_users", description="Postgres database name")
    schema_: str = Field(
        default="memos",
        alias="schema",
        description="Postgres schema for the user manager",
    )
    sslmode: str | None = Field(default=None, description="Postgres SSL mode")

    @property
    def schema(self) -> str:
        return self.schema_

    @schema.setter
    def schema(self, value: str) -> None:
        self.schema_ = value


class UserManagerConfigFactory(BaseModel):
    """Factory for user manager configurations."""

    backend: str = Field(default="sqlite", description="Backend for user manager")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Configuration for the user manager backend"
    )

    backend_to_class: ClassVar[dict[str, Any]] = {
        "sqlite": SQLiteUserManagerConfig,
        "mysql": MySQLUserManagerConfig,
        "postgres": PostgresUserManagerConfig,
    }

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, backend: str) -> str:
        if backend not in cls.backend_to_class:
            raise ValueError(f"Unsupported user manager backend: {backend}")
        return backend

    @model_validator(mode="after")
    def instantiate_config(self):
        config_class = self.backend_to_class[self.backend]
        self.config = config_class(**self.config)
        return self
