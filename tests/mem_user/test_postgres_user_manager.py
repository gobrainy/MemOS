"""Integration tests for the Postgres user manager."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid

import pytest
from sqlalchemy.exc import SQLAlchemyError

from memos.mem_user.postgres_user_manager import PostgresUserManager
from memos.mem_user.user_manager import UserRole


def _explicit_postgres_configured() -> bool:
    keys = [
        "MOS_POSTGRES_HOST",
        "MOS_POSTGRES_PORT",
        "MOS_POSTGRES_USERNAME",
        "MOS_POSTGRES_PASSWORD",
        "MOS_POSTGRES_DATABASE",
        "MOS_POSTGRES_SCHEMA",
    ]
    return any(os.getenv(key) for key in keys)


def _start_temporary_postgres(config: dict[str, str | int | None]) -> tuple[dict[str, str | int | None], str]:
    """Start a temporary Postgres container using Docker and update config."""

    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not available to start a Postgres container")

    container_name = f"memos-postgres-test-{uuid.uuid4().hex[:8]}"
    port = int(os.getenv("MOS_POSTGRES_TEST_PORT", "55432"))
    password = config.get("password") or "postgres"

    updated_config = dict(config)
    updated_config.update(
        {
            "host": "127.0.0.1",
            "port": port,
            "password": password,
        }
    )

    cmd = [
        "docker",
        "run",
        "--rm",
        "-d",
        "--name",
        container_name,
        "-e",
        f"POSTGRES_USER={updated_config['username']}",
        "-e",
        f"POSTGRES_PASSWORD={password}",
        "-e",
        f"POSTGRES_DB={updated_config['database']}",
        "-p",
        f"{port}:5432",
        "postgres:15",
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return updated_config, container_name


def _stop_container(container_name: str) -> None:
    subprocess.run(
        ["docker", "stop", container_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(scope="module")
def postgres_manager():
    """Provide a Postgres-backed user manager, starting Docker if needed."""

    config: dict[str, str | int | None] = {
        "user_id": os.getenv("MOS_POSTGRES_ROOT_USER", "root"),
        "host": os.getenv("MOS_POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("MOS_POSTGRES_PORT", "5432")),
        "username": os.getenv("MOS_POSTGRES_USERNAME", "postgres"),
        "password": os.getenv("MOS_POSTGRES_PASSWORD", "postgres"),
        "database": os.getenv("MOS_POSTGRES_DATABASE", "memos_users"),
        "schema": os.getenv("MOS_POSTGRES_SCHEMA", "memos"),
        "sslmode": os.getenv("MOS_POSTGRES_SSLMODE"),
    }

    container_name = None
    manager = None

    try:
        manager = PostgresUserManager(**config)
    except (SQLAlchemyError, OSError) as exc:
        if _explicit_postgres_configured():
            pytest.skip(f"Postgres server is not available: {exc}")

        try:
            config, container_name = _start_temporary_postgres(config)
        except RuntimeError as start_err:
            pytest.skip(f"Postgres server is not available and Docker could not start it: {start_err}")

        deadline = time.time() + 30
        last_error: Exception | None = exc
        while time.time() < deadline:
            try:
                manager = PostgresUserManager(**config)
                break
            except (SQLAlchemyError, OSError) as inner_exc:
                last_error = inner_exc
                time.sleep(1)

        if manager is None:
            if container_name:
                _stop_container(container_name)
            pytest.skip(f"Postgres container failed to become ready: {last_error}")

    try:
        yield manager
    finally:
        if manager is not None:
            manager.close()
        if container_name is not None:
            _stop_container(container_name)


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
