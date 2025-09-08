import os

from typing import Any, ClassVar

from memos.configs.mem_user import UserManagerConfigFactory
from memos.mem_user.mysql_user_manager import MySQLUserManager
from memos.mem_user.postgres_user_manager import PostgresUserManager
from memos.mem_user.user_manager import UserManager


class UserManagerFactory:
    """Factory class for creating user manager instances."""

    backend_to_class: ClassVar[dict[str, Any]] = {
        "sqlite": UserManager,
        "mysql": MySQLUserManager,
        "postgres": PostgresUserManager,
        "postgresql": PostgresUserManager,
    }

    @classmethod
    def from_config(
        cls, config_factory: UserManagerConfigFactory
    ) -> UserManager | MySQLUserManager | PostgresUserManager:
        """Create a user manager instance from configuration.

        Args:
            config_factory: Configuration factory containing backend and config

        Returns:
            User manager instance

        Raises:
            ValueError: If backend is not supported
        """
        backend = config_factory.backend
        if backend not in cls.backend_to_class:
            raise ValueError(f"Invalid user manager backend: {backend}")

        user_manager_class = cls.backend_to_class[backend]
        config = config_factory.config

        # Use model_dump() to convert Pydantic model to dict and unpack as kwargs
        return user_manager_class(**config.model_dump())

    @classmethod
    def from_env(cls) -> UserManager | MySQLUserManager | PostgresUserManager:
        """Create a user manager instance from environment variables.

        Environment variables:
            MEMOS_USER_MANAGER: one of [sqlite, mysql, postgres] (default: sqlite)

        SQLite:
            MEMOS_SQLITE_DB_PATH: optional path to sqlite db file

        MySQL:
            MEMOS_MYSQL_HOST, MEMOS_MYSQL_PORT, MEMOS_MYSQL_USERNAME,
            MEMOS_MYSQL_PASSWORD, MEMOS_MYSQL_DATABASE, MEMOS_MYSQL_CHARSET

        Postgres:
            MEMOS_POSTGRES_HOST, MEMOS_POSTGRES_PORT, MEMOS_POSTGRES_USERNAME,
            MEMOS_POSTGRES_PASSWORD, MEMOS_POSTGRES_DATABASE, MEMOS_POSTGRES_SSLMODE
        """
        backend = os.getenv("MEMOS_USER_MANAGER", "sqlite").lower()

        if backend in {"postgres", "postgresql"}:
            return PostgresUserManager(
                user_id=os.getenv("MEMOS_USER_ID", "root"),
                host=os.getenv("MEMOS_POSTGRES_HOST", "localhost"),
                port=int(os.getenv("MEMOS_POSTGRES_PORT", "5432")),
                username=os.getenv("MEMOS_POSTGRES_USERNAME", "postgres"),
                password=os.getenv("MEMOS_POSTGRES_PASSWORD", ""),
                database=os.getenv("MEMOS_POSTGRES_DATABASE", "memos_users"),
                sslmode=os.getenv("MEMOS_POSTGRES_SSLMODE", None),
            )

        if backend == "mysql":
            return MySQLUserManager(
                user_id=os.getenv("MEMOS_USER_ID", "root"),
                host=os.getenv("MEMOS_MYSQL_HOST", "localhost"),
                port=int(os.getenv("MEMOS_MYSQL_PORT", "3306")),
                username=os.getenv("MEMOS_MYSQL_USERNAME", "root"),
                password=os.getenv("MEMOS_MYSQL_PASSWORD", ""),
                database=os.getenv("MEMOS_MYSQL_DATABASE", "memos_users"),
                charset=os.getenv("MEMOS_MYSQL_CHARSET", "utf8mb4"),
            )

        # default sqlite
        return UserManager(
            db_path=os.getenv("MEMOS_SQLITE_DB_PATH", None),
            user_id=os.getenv("MEMOS_USER_ID", "root"),
        )

    @classmethod
    def create_sqlite(cls, db_path: str | None = None, user_id: str = "root") -> UserManager:
        """Create SQLite user manager with default configuration.

        Args:
            db_path: Path to SQLite database file
            user_id: Default user ID for initialization

        Returns:
            SQLite user manager instance
        """
        config_factory = UserManagerConfigFactory(
            backend="sqlite", config={"db_path": db_path, "user_id": user_id}
        )
        return cls.from_config(config_factory)

    @classmethod
    def create_mysql(
        cls,
        user_id: str = "root",
        host: str = "localhost",
        port: int = 3306,
        username: str = "root",
        password: str = "",
        database: str = "memos_users",
        charset: str = "utf8mb4",
    ) -> MySQLUserManager:
        """Create MySQL user manager with specified configuration.

        Args:
            user_id: Default user ID for initialization
            host: MySQL server host
            port: MySQL server port
            username: MySQL username
            password: MySQL password
            database: MySQL database name
            charset: MySQL charset

        Returns:
            MySQL user manager instance
        """
        config_factory = UserManagerConfigFactory(
            backend="mysql",
            config={
                "user_id": user_id,
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "database": database,
                "charset": charset,
            },
        )
        return cls.from_config(config_factory)
