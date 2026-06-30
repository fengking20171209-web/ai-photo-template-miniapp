# Database Migration Sequence

This document outlines the database migrations introduced in Phase 2A, including their purpose, idempotency, and dependencies.

## 001 - Initial Schema & SQLite WAL Configuration
**File:** Implemented via `backend/database.py` and SQLAlchemy `Base.metadata.create_all`.
**Purpose:** Sets up the foundational database schema (e.g. initial `Image`, `Template` models) and configures SQLite to use Write-Ahead Logging (WAL) for improved concurrency and reliability, preventing "database is locked" errors under concurrent loads.
**Idempotency:** Yes, `create_all` checks for existing tables and PRAGMA statements are safe to execute multiple times.
**Dependencies:** None.

## 002 - Prompt Versions and Task Chains
**File:** `backend/migrations/002_prompt_versions_task_chains.sql`
**Purpose:** Introduces the schema for the prompt versioning system (`prompts`, `prompt_versions`) and task execution graph (`tasks`, `task_chains`, `task_edges`). This allows the system to version control system prompts and define Directed Acyclic Graphs (DAGs) for business workflow execution.
**Idempotency:** Requires manual or ORM checking if run via raw SQL, but in an automated migration tool (like Alembic, or `CREATE TABLE IF NOT EXISTS`), it is idempotent.
**Dependencies:** Depends on 001 (Foundational Schema).

## 003 - Prompt Drafts
**File:** `backend/migrations/003_prompt_drafts.sql`
**Purpose:** Extends the prompt system by adding the `prompt_drafts` table. This allows drafts to be created, updated, and reviewed before they are published to a permanent `prompt_version`.
**Idempotency:** Requires `IF NOT EXISTS` for raw SQL to be fully idempotent. 
**Dependencies:** Depends on 002 (requires the prompt system to be established).
