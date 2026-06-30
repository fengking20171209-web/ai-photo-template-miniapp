-- Migration for Phase 2A: Prompt Drafts

CREATE TABLE IF NOT EXISTS prompt_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER,
    title VARCHAR(255),
    content TEXT,
    system_message TEXT,
    parameters_json JSON,
    status VARCHAR(50) DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(prompt_id) REFERENCES prompts(id)
);

CREATE INDEX idx_prompt_drafts_prompt_id ON prompt_drafts(prompt_id);
CREATE INDEX idx_prompt_drafts_status ON prompt_drafts(status);
