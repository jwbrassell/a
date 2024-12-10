-- Create role table
CREATE TABLE role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(80) UNIQUE NOT NULL,
    description VARCHAR(255)
);

-- Create user table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    name VARCHAR(120),
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create user_roles junction table
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (role_id) REFERENCES role (id)
);

-- Insert default roles
INSERT INTO role (name, description) VALUES 
    ('admin', 'Administrator role'),
    ('user', 'Default user role');

-- Insert admin user (password will be 'test123')
INSERT INTO user (username, email, password_hash, name) VALUES 
    ('admin', 'admin@example.com', 'pbkdf2:sha256:600000$g3Gh2Mm6lGzKGHEm$a2178ce1fa841e901be3d81e2d9516e19f89c121960fee89160f936080de4b1b', 'Admin User');

-- Assign both roles to admin user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM user u, role r
WHERE u.username = 'admin';

-- Create alembic_version table
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
