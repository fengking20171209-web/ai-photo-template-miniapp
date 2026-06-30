# AI Gallery Search Backend

This folder contains the Kimi Agents delivery for the gallery search API.

Status:

- FastAPI app scaffolded.
- PostgreSQL `images` ORM model included.
- `GET /images/` supports keyword search, tag filtering, date range filtering, and pagination.
- Tests are included under `backend/tests/`.

This is a second-stage module. The current website MVP still uses the Node.js API in `src/server/`.

## Run Locally

Install dependencies in a Python environment:

```powershell
uv pip install -r backend\requirements.txt
```

Run the API:

```powershell
uv run --with-requirements backend\requirements.txt uvicorn backend.main:app --reload
```

Run tests:

```powershell
uv run --with-requirements backend\requirements.txt pytest backend\tests
```

## Environment

Set `DATABASE_URL` for PostgreSQL:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aigallery
```
