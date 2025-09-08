import os

import pytest

from memos.mem_user.postgres_user_manager import PostgresUserManager, UserRole


requires_pg = pytest.mark.skipif(
    os.getenv("MEMOS_USER_MANAGER", "sqlite").lower() not in {"postgres", "postgresql"},
    reason="Postgres tests skipped: MEMOS_USER_MANAGER is not set to postgres",
)


@requires_pg
def test_postgres_user_lifecycle():
    manager = PostgresUserManager(
        user_id=os.getenv("MEMOS_USER_ID", "root"),
        host=os.getenv("MEMOS_POSTGRES_HOST", "localhost"),
        port=int(os.getenv("MEMOS_POSTGRES_PORT", "5432")),
        username=os.getenv("MEMOS_POSTGRES_USERNAME", "postgres"),
        password=os.getenv("MEMOS_POSTGRES_PASSWORD", ""),
        database=os.getenv("MEMOS_POSTGRES_DATABASE", "memos_users"),
        sslmode=os.getenv("MEMOS_POSTGRES_SSLMODE", None),
    )
    try:
        user_id = manager.create_user("pg_test_user", UserRole.USER)
        assert user_id is not None
        assert manager.validate_user(user_id) is True

        # create cube
        cube_id = manager.create_cube("pg_test_cube", user_id)
        assert cube_id is not None

        # access checks
        assert manager.validate_user_cube_access(user_id, cube_id) is True

        # soft delete
        assert manager.delete_cube(cube_id) is True
        assert manager.validate_user_cube_access(user_id, cube_id) is False

        assert manager.delete_user(user_id) is True
        assert manager.validate_user(user_id) is False
    finally:
        manager.close()

