import os

from typing import Any, ClassVar

from memos.configs.mem_user import UserManagerConfigFactory
from memos.mem_user.mysql_persistent_user_manager import MySQLPersistentUserManager
from memos.mem_user.persistent_user_manager import PersistentUserManager


def _load_mysql_env_config(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "username": os.getenv("MYSQL_USERNAME", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "memos_users"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    }


def _load_postgres_env_config(user_id: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "host": os.getenv("MOS_POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost")),
        "port": int(os.getenv("MOS_POSTGRES_PORT", os.getenv("POSTGRES_PORT", "5432"))),
        "username": os.getenv("MOS_POSTGRES_USERNAME", os.getenv("POSTGRES_USERNAME", "postgres")),
        "password": os.getenv("MOS_POSTGRES_PASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
        "database": os.getenv(
            "MOS_POSTGRES_DATABASE", os.getenv("POSTGRES_DATABASE", "memos_users")
        ),
        "schema": os.getenv("MOS_POSTGRES_SCHEMA", os.getenv("POSTGRES_SCHEMA", "memos")),
        "sslmode": (os.getenv("MOS_POSTGRES_SSLMODE", os.getenv("POSTGRES_SSLMODE", "")) or None),
    }


class PersistentUserManagerFactory:
    """Factory class for creating persistent user manager instances."""

    backend_to_class: ClassVar[dict[str, Any]] = {
        "sqlite": PersistentUserManager,
        "mysql": MySQLPersistentUserManager,
    }

    @classmethod
    def from_config(
        cls, config_factory: UserManagerConfigFactory
    ) -> PersistentUserManager | MySQLPersistentUserManager:
        """Create a persistent user manager instance from configuration.

        Args:
            config_factory: Configuration factory containing backend and config

        Returns:
            Persistent user manager instance

        Raises:
            ValueError: If backend is not supported
        """
        backend = config_factory.backend
        if backend not in cls.backend_to_class:
            raise ValueError(f"Invalid persistent user manager backend: {backend}")

        config = config_factory.config
        user_id = getattr(config, "user_id", "root")

        env_backend = (
            os.getenv("MOS_PERSISTENT_USER_MANAGER")
            or os.getenv("MOS_USER_MANAGER")
            or os.getenv("MOS_USER_MANAGER_BACKEND")
            or ""
        ).lower()

        if env_backend and env_backend in cls.backend_to_class:
            backend = env_backend
            if backend == "mysql":
                env_kwargs = _load_mysql_env_config(user_id)
            elif backend == "postgres":
                env_kwargs = _load_postgres_env_config(user_id)
            else:
                env_kwargs = {"user_id": user_id}

            config_cls = config_factory.backend_to_class[backend]
            config = config_cls(**env_kwargs)

        user_manager_class = cls.backend_to_class[backend]

        # Use model_dump() to convert Pydantic model to dict and unpack as kwargs
        return user_manager_class(**config.model_dump(by_alias=True))

    @classmethod
    def create_sqlite(
        cls, db_path: str | None = None, user_id: str = "root"
    ) -> PersistentUserManager:
        """Create SQLite persistent user manager with default configuration.

        Args:
            db_path: Path to SQLite database file
            user_id: Default user ID for initialization

        Returns:
            SQLite persistent user manager instance
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
    ) -> MySQLPersistentUserManager:
        """Create MySQL persistent user manager with specified configuration.

        Args:
            user_id: Default user ID for initialization
            host: MySQL server host
            port: MySQL server port
            username: MySQL username
            password: MySQL password
            database: MySQL database name
            charset: MySQL charset

        Returns:
            MySQL persistent user manager instance
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
