"""Integration tests for the Postgres user manager."""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy.exc import SQLAlchemyError

from memos.mem_user.postgres_user_manager import PostgresUserManager
from memos.mem_user.user_manager import UserRole


@pytest.fixture(scope="module")
def postgres_manager():
    """Provide a Postgres-backed user manager if the database is reachable."""

    config = {
        "user_id": os.getenv("MOS_POSTGRES_ROOT_USER", "root"),
        "host": os.getenv("MOS_POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("MOS_POSTGRES_PORT", "5432")),
        "username": os.getenv("MOS_POSTGRES_USERNAME", "postgres"),
        "password": os.getenv("MOS_POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("MOS_POSTGRES_DATABASE", "memos_users"),
        "schema": os.getenv("MOS_POSTGRES_SCHEMA", "memos"),
        "sslmode": os.getenv("MOS_POSTGRES_SSLMODE"),
    }

    try:
        manager = PostgresUserManager(**config)
    except (SQLAlchemyError, OSError) as exc:
        pytest.skip(f"Postgres server is not available: {exc}")
    else:
        yield manager
        manager.close()


@pytest.mark.integration
def test_postgres_root_user_created(postgres_manager):
    """Ensure the root user exists when the manager initializes."""

    root = postgres_manager.get_user("root")
    assert root is not None
    assert root.user_name == "root"
    assert root.role == UserRole.ROOT.value or root.role == UserRole.ROOT


@pytest.mark.integration
def test_postgres_create_user_and_cube(postgres_manager):
    """Verify user and cube lifecycle operations work on Postgres."""

    user_name = f"pg_user_{uuid.uuid4().hex[:8]}"
    user_id = postgres_manager.create_user(user_name, UserRole.ADMIN)

    user = postgres_manager.get_user(user_id)
    assert user is not None
    assert user.user_name == user_name
    assert user.role == UserRole.ADMIN.value

    cube_name = f"pg_cube_{uuid.uuid4().hex[:8]}"
    cube_id = postgres_manager.create_cube(cube_name, owner_id=user_id)

    cube = postgres_manager.get_cube(cube_id)
    assert cube is not None
    assert cube.cube_name == cube_name
    assert cube.owner_id == user_id

    assert postgres_manager.validate_user_cube_access(user_id, cube_id) is True
