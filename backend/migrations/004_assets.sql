CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    task_chain_id INTEGER REFERENCES task_chains(id),
    prompt_version_id INTEGER REFERENCES prompt_versions(id),
    asset_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,
    file_path VARCHAR(1024) NOT NULL,
    file_url VARCHAR(1024),
    thumbnail_path VARCHAR(1024),
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    metadata_json JSON,
    source VARCHAR(50),
    is_favorite BOOLEAN DEFAULT 0,
    is_deleted BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);

CREATE INDEX idx_assets_task_id ON assets(task_id);
CREATE INDEX idx_assets_task_chain_id ON assets(task_chain_id);
CREATE INDEX idx_assets_prompt_version_id ON assets(prompt_version_id);
CREATE INDEX idx_assets_asset_type ON assets(asset_type);
CREATE INDEX idx_assets_source ON assets(source);
CREATE INDEX idx_assets_is_deleted ON assets(is_deleted);
CREATE INDEX idx_assets_created_at ON assets(created_at);
CREATE INDEX idx_assets_task_is_deleted ON assets(task_id, is_deleted);
