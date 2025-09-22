CREATE SCHEMA IF NOT EXISTS memos;

CREATE TABLE IF NOT EXISTS memos.users (
    user_id VARCHAR(255) PRIMARY KEY,
    user_name VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS memos.cubes (
    cube_id VARCHAR(255) PRIMARY KEY,
    cube_name VARCHAR(255) NOT NULL,
    cube_path VARCHAR(500),
    owner_id VARCHAR(255) NOT NULL REFERENCES memos.users(user_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS memos.user_cube_association (
    user_id VARCHAR(255) NOT NULL REFERENCES memos.users(user_id),
    cube_id VARCHAR(255) NOT NULL REFERENCES memos.cubes(cube_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, cube_id)
);

CREATE INDEX IF NOT EXISTS idx_users_user_name ON memos.users (user_name);
CREATE INDEX IF NOT EXISTS idx_cubes_owner_id ON memos.cubes (owner_id);
