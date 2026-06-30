# Phase 2A API Contract

This document outlines the API contracts for the 8 workflow endpoints introduced in Phase 2A.

## 1. Create Prompt Draft
**Endpoint:** `POST /prompts/drafts`
**Description:** Creates a new prompt draft.
**Transactionality:** Single database insert.

**Request Body (`PromptDraftCreate`):**
```json
{
  "title": "string",
  "content": "string",
  "system_message": "string (optional)",
  "parameters_json": "object (optional)",
  "prompt_id": "integer (optional)"
}
```

**Response (`PromptDraftResponse`, 200 OK):**
```json
{
  "id": "integer",
  "prompt_id": "integer (optional)",
  "title": "string",
  "content": "string",
  "system_message": "string (optional)",
  "parameters_json": "object (optional)",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 2. Update Prompt Draft
**Endpoint:** `PATCH /prompts/drafts/{draft_id}`
**Description:** Updates an existing prompt draft.
**Transactionality:** Single database update.

**Request Body (`PromptDraftUpdate`):**
```json
{
  "title": "string (optional)",
  "content": "string (optional)",
  "system_message": "string (optional)",
  "parameters_json": "object (optional)"
}
```

**Response (`PromptDraftResponse`, 200 OK):** Same as above. (404 if not found).

## 3. Publish Prompt Draft
**Endpoint:** `POST /prompts/drafts/{draft_id}/publish`
**Description:** Publishes a draft to a new prompt version.
**Transactionality:** Requires a transaction across updating the draft status, potentially creating a `Prompt` entity, creating a `PromptVersion`, and updating the `content_hash`.

**Request Body (`PublishDraftRequest`):**
```json
{
  "change_note": "string (optional)",
  "created_by": "string (optional)"
}
```

**Response (`PromptVersionResponse`, 200 OK):**
```json
{
  "id": "integer",
  "prompt_id": "integer",
  "version": "integer",
  "content": "string",
  "system_message": "string (optional)",
  "parameters_json": "object (optional)",
  "change_note": "string (optional)",
  "created_at": "datetime",
  "is_active": "boolean",
  "content_hash": "string"
}
```

## 4. Discard Prompt Draft
**Endpoint:** `POST /prompts/drafts/{draft_id}/discard`
**Description:** Discards a prompt draft.
**Transactionality:** Single database update.

**Request Body:** Empty

**Response (`PromptDraftResponse`, 200 OK):** Returns updated draft with 'discarded' status.

## 5. Get Prompt Draft
**Endpoint:** `GET /prompts/drafts/{draft_id}`
**Description:** Retrieves a draft by ID.

**Response (`PromptDraftResponse`, 200 OK):** Same as above.

## 6. Submit Task
**Endpoint:** `POST /tasks/`
**Description:** Submits a new workflow task.
**Transactionality:** Single database insert (optionally creates TaskChain if not provided).

**Request Body (`TaskSubmit`):**
```json
{
  "title": "string",
  "task_type": "string",
  "input_json": "object (optional)",
  "prompt_version_id": "integer (optional)",
  "parent_task_id": "integer (optional)",
  "chain_id": "integer (optional)"
}
```

**Response (`TaskResponse`, 200 OK):**
```json
{
  "id": "integer",
  "title": "string",
  "task_type": "string",
  "status": "string",
  "input_json": "object (optional)",
  "output_json": "object (optional)",
  "error_message": "string (optional)",
  "prompt_version_id": "integer (optional)",
  "parent_task_id": "integer (optional)",
  "chain_id": "integer (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 7. Get Task
**Endpoint:** `GET /tasks/{task_id}`
**Description:** Retrieves a task by ID.

**Response (`TaskResponse`, 200 OK):** Same as above.

## 8. Get Task Chain Graph
**Endpoint:** `GET /tasks/chain/{chain_id}`
**Description:** Retrieves the execution graph for a task chain.

**Response (200 OK):**
```json
{
  "chain": {
    "id": "integer",
    "name": "string",
    "status": "string"
  },
  "tasks": [
    {
      "id": "integer",
      "title": "string",
      "status": "string",
      "task_type": "string"
    }
  ],
  "edges": [
    {
      "id": "integer",
      "from_task_id": "integer",
      "to_task_id": "integer",
      "edge_type": "string"
    }
  ]
}
```
