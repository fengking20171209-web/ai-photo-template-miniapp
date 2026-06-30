-- Migration: 002_prompt_versions_task_chains
-- Description: Schema refactoring for prompt versioning and task chains.

CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    category VARCHAR(100),
    description TEXT,
    current_version_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name);
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    content TEXT,
    model_hint VARCHAR(255),
    system_message TEXT,
    parameters_json TEXT,
    change_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    content_hash VARCHAR(64),
    CONSTRAINT uq_prompt_version UNIQUE(prompt_id, version),
    CONSTRAINT uq_prompt_content_hash UNIQUE(prompt_id, content_hash),
    FOREIGN KEY(prompt_id) REFERENCES prompts(id)
);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);

CREATE TABLE IF NOT EXISTS task_chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_task_chains_status ON task_chains(status);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255),
    task_type VARCHAR(50),
    status VARCHAR(50),
    input_json TEXT,
    output_json TEXT,
    prompt_version_id INTEGER,
    parent_task_id INTEGER,
    chain_id INTEGER,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY(prompt_version_id) REFERENCES prompt_versions(id),
    FOREIGN KEY(parent_task_id) REFERENCES tasks(id),
    FOREIGN KEY(chain_id) REFERENCES task_chains(id)
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_prompt_version_id ON tasks(prompt_version_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_chain_id ON tasks(chain_id);

CREATE TABLE IF NOT EXISTS task_chain_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    from_task_id INTEGER NOT NULL,
    to_task_id INTEGER NOT NULL,
    edge_type VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_chain_edge UNIQUE(chain_id, from_task_id, to_task_id),
    FOREIGN KEY(chain_id) REFERENCES task_chains(id),
    FOREIGN KEY(from_task_id) REFERENCES tasks(id),
    FOREIGN KEY(to_task_id) REFERENCES tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_task_chain_edges_chain_id ON task_chain_edges(chain_id);
CREATE INDEX IF NOT EXISTS idx_task_chain_edges_from_task_id ON task_chain_edges(from_task_id);
CREATE INDEX IF NOT EXISTS idx_task_chain_edges_to_task_id ON task_chain_edges(to_task_id);
