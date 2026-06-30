-- Migration: 005_prompt_evolution
-- Description: Create tables for Prompt Evolution Engine

CREATE TABLE IF NOT EXISTS prompt_evolution_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    base_version_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id),
    FOREIGN KEY(base_version_id) REFERENCES prompt_versions(id)
);

CREATE TABLE IF NOT EXISTS prompt_evolution_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    variant_text TEXT,
    strategy VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    promoted_version_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES prompt_evolution_runs(id),
    FOREIGN KEY(promoted_version_id) REFERENCES prompt_versions(id)
);

CREATE TABLE IF NOT EXISTS prompt_evaluation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    prompt_version_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(asset_id) REFERENCES assets(id),
    FOREIGN KEY(prompt_version_id) REFERENCES prompt_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_prompt_evolution_runs_prompt_id ON prompt_evolution_runs(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_evolution_candidates_run_id ON prompt_evolution_candidates(run_id);
CREATE INDEX IF NOT EXISTS idx_prompt_evaluation_records_asset_id ON prompt_evaluation_records(asset_id);
CREATE INDEX IF NOT EXISTS idx_prompt_evaluation_records_prompt_version_id ON prompt_evaluation_records(prompt_version_id);
