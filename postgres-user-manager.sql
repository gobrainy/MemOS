-- SQL schema for PostgresUserManager
-- Execute this on your PostgreSQL database before running MemOS with MEMOS_USER_MANAGER=postgres

CREATE TABLE IF NOT EXISTS users (
    user_id   VARCHAR(255) PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    role      VARCHAR(20)  NOT NULL DEFAULT 'USER',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active  BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS cubes (
    cube_id    VARCHAR(255) PRIMARY KEY,
    cube_name  VARCHAR(255) NOT NULL,
    cube_path  VARCHAR(500),
    owner_id   VARCHAR(255) NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active  BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS user_cube_association (
    user_id   VARCHAR(255) NOT NULL REFERENCES users(user_id),
    cube_id   VARCHAR(255) NOT NULL REFERENCES cubes(cube_id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY(user_id, cube_id)
);

-- Optional index to speed up lookups
CREATE INDEX IF NOT EXISTS idx_user_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_cube_active ON cubes(is_active);
