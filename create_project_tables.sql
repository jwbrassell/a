-- Project Status table
CREATE TABLE IF NOT EXISTS project_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project Priority table
CREATE TABLE IF NOT EXISTS project_priority (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project table
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    summary VARCHAR(500),
    icon VARCHAR(50),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    priority VARCHAR(50) DEFAULT 'medium',
    percent_complete INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_private BOOLEAN DEFAULT 0,
    notify_task_created BOOLEAN DEFAULT 1,
    notify_task_completed BOOLEAN DEFAULT 1,
    notify_comments BOOLEAN DEFAULT 1,
    lead_id INTEGER,
    FOREIGN KEY (lead_id) REFERENCES user(id)
);

-- Project association tables
CREATE TABLE IF NOT EXISTS project_watchers (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS project_stakeholders (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS project_shareholders (
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS project_roles (
    project_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (project_id, role_id),
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (role_id) REFERENCES role(id)
);

-- Task table
CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    parent_id INTEGER,
    name VARCHAR(200) NOT NULL,
    summary VARCHAR(500),
    description TEXT,
    status_id INTEGER,
    priority_id INTEGER,
    due_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    position INTEGER DEFAULT 0,
    list_position VARCHAR(50) DEFAULT 'todo',
    assigned_to_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (parent_id) REFERENCES task(id),
    FOREIGN KEY (status_id) REFERENCES project_status(id),
    FOREIGN KEY (priority_id) REFERENCES project_priority(id),
    FOREIGN KEY (assigned_to_id) REFERENCES user(id)
);

-- Task dependencies table
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id INTEGER NOT NULL,
    dependency_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, dependency_id),
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (dependency_id) REFERENCES task(id)
);

-- Todo table
CREATE TABLE IF NOT EXISTS todo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    task_id INTEGER,
    description VARCHAR(500) NOT NULL,
    completed BOOLEAN DEFAULT 0,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    sort_order INTEGER DEFAULT 0,
    assigned_to_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (assigned_to_id) REFERENCES user(id)
);

-- Comment table
CREATE TABLE IF NOT EXISTS comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    task_id INTEGER,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- History table
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(50) NOT NULL,
    project_id INTEGER,
    task_id INTEGER,
    action VARCHAR(50) NOT NULL,
    details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS ix_project_status ON project(status);
CREATE INDEX IF NOT EXISTS ix_project_priority ON project(priority);
CREATE INDEX IF NOT EXISTS ix_task_project_id ON task(project_id);
CREATE INDEX IF NOT EXISTS ix_task_status_id ON task(status_id);
CREATE INDEX IF NOT EXISTS ix_task_priority_id ON task(priority_id);
CREATE INDEX IF NOT EXISTS ix_todo_project_id ON todo(project_id);
CREATE INDEX IF NOT EXISTS ix_todo_task_id ON todo(task_id);
CREATE INDEX IF NOT EXISTS ix_comment_project_id ON comment(project_id);
CREATE INDEX IF NOT EXISTS ix_comment_task_id ON comment(task_id);
CREATE INDEX IF NOT EXISTS ix_history_project_id ON history(project_id);
CREATE INDEX IF NOT EXISTS ix_history_task_id ON history(task_id);

-- Insert default statuses
INSERT OR IGNORE INTO project_status (name, color) VALUES
    ('planning', 'info'),
    ('active', 'success'),
    ('on_hold', 'warning'),
    ('completed', 'secondary'),
    ('archived', 'dark');

-- Insert default priorities
INSERT OR IGNORE INTO project_priority (name, color) VALUES
    ('low', 'success'),
    ('medium', 'warning'),
    ('high', 'danger');
