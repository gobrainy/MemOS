"""Persistent user management system for MemOS with configuration storage (PostgreSQL).

This module extends the Postgres UserManager to provide persistent storage
for user configurations and MOS instances.
"""

import json

from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text

from memos.configs.mem_os import MOSConfig
from memos.log import get_logger
from memos.mem_user.postgres_user_manager import Base, PostgresUserManager


logger = get_logger(__name__)


class UserConfig(Base):
    """User configuration model for the database."""

    __tablename__ = "user_configs"

    user_id = Column(String(255), primary_key=True)
    config_data = Column(Text, nullable=False)  # JSON string of MOSConfig
    created_at = Column(String(50), nullable=False)  # ISO format timestamp
    updated_at = Column(String(50), nullable=False)  # ISO format timestamp

    def __repr__(self):
        return f"<UserConfig(user_id='{self.user_id}')>"


class PostgresPersistentUserManager(PostgresUserManager):
    """Extended PostgresUserManager with configuration persistence."""

    def __init__(
        self,
        user_id: str = "root",
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "",
        database: str = "memos_users",
        sslmode: str | None = None,
    ):
        """Initialize the persistent user manager."""
        super().__init__(
            user_id=user_id,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            sslmode=sslmode,
        )

        # Create user_configs table
        Base.metadata.create_all(bind=self.engine)
        logger.info("PostgresPersistentUserManager initialized with configuration storage")

    def _convert_datetime_strings(self, obj: Any) -> Any:
        """Recursively convert datetime strings back to datetime objects in config dict."""
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == "created_at" and isinstance(value, str):
                    try:
                        result[key] = datetime.fromisoformat(value)
                    except ValueError:
                        # If parsing fails, keep the original string
                        result[key] = value
                else:
                    result[key] = self._convert_datetime_strings(value)
            return result
        elif isinstance(obj, list):
            return [self._convert_datetime_strings(item) for item in obj]
        else:
            return obj

    def save_user_config(self, user_id: str, config: MOSConfig) -> bool:
        """Save user configuration to database."""
        session = self._get_session()
        try:
            # Convert config to JSON string with proper datetime handling
            config_dict = config.model_dump(mode="json")
            config_json = json.dumps(config_dict, indent=2)

            now = datetime.now().isoformat()

            # Check if config already exists
            existing_config = (
                session.query(UserConfig).filter(UserConfig.user_id == user_id).first()
            )

            if existing_config:
                # Update existing config
                existing_config.config_data = config_json
                existing_config.updated_at = now
                logger.info(f"Updated configuration for user {user_id}")
            else:
                # Create new config
                user_config = UserConfig(
                    user_id=user_id, config_data=config_json, created_at=now, updated_at=now
                )
                session.add(user_config)
                logger.info(f"Saved new configuration for user {user_id}")

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving user config for {user_id}: {e}")
            return False
        finally:
            session.close()

    def get_user_config(self, user_id: str) -> MOSConfig | None:
        """Get user configuration from database."""
        session = self._get_session()
        try:
            user_config = session.query(UserConfig).filter(UserConfig.user_id == user_id).first()

            if user_config:
                config_dict = json.loads(user_config.config_data)
                # Convert datetime strings back to datetime objects
                config_dict = self._convert_datetime_strings(config_dict)
                return MOSConfig(**config_dict)
            return None

        except Exception as e:
            logger.error(f"Error loading user config for {user_id}: {e}")
            return None
        finally:
            session.close()

    def delete_user_config(self, user_id: str) -> bool:
        """Delete user configuration from database."""
        session = self._get_session()
        try:
            user_config = session.query(UserConfig).filter(UserConfig.user_id == user_id).first()

            if user_config:
                session.delete(user_config)
                session.commit()
                logger.info(f"Deleted configuration for user {user_id}")
                return True
            return False

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting user config for {user_id}: {e}")
            return False
        finally:
            session.close()

    def list_user_configs(self) -> dict[str, MOSConfig]:
        """List all user configurations."""
        session = self._get_session()
        try:
            user_configs = session.query(UserConfig).all()
            result = {}

            for user_config in user_configs:
                try:
                    config_dict = json.loads(user_config.config_data)
                    # Convert datetime strings back to datetime objects
                    config_dict = self._convert_datetime_strings(config_dict)
                    result[user_config.user_id] = MOSConfig(**config_dict)
                except Exception as e:
                    logger.error(f"Error parsing config for user {user_config.user_id}: {e}")
                    continue

            return result

        except Exception as e:
            logger.error(f"Error listing user configs: {e}")
            return {}
        finally:
            session.close()

    def create_user_with_config(
        self, user_name: str, config: MOSConfig, role=None, user_id: str | None = None
    ) -> str:
        """Create a new user with configuration."""
        # Create user using parent method
        created_user_id = self.create_user(user_name, role, user_id)

        # Save configuration
        if not self.save_user_config(created_user_id, config):
            logger.error(f"Failed to save configuration for user {created_user_id}")

        return created_user_id

    def delete_user(self, user_id: str) -> bool:
        """Delete a user and their configuration."""
        # Delete configuration first
        self.delete_user_config(user_id)

        # Delete user using parent method
        return super().delete_user(user_id)

    def get_user_cube_access(self, user_id: str) -> list[str]:
        """Get list of cube IDs that a user has access to."""
        cubes = self.get_user_cubes(user_id)
        return [cube.cube_id for cube in cubes]

