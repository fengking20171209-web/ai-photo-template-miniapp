# Gemini / AI Assistant Instructions

This project enforces strict AI Agent workflows to maintain high architectural standards.

## 1. Superpowers Framework
All agents MUST follow the internal `superpowers` SOPs located in `.kimi-code/skills/superpowers/`. Before executing any task, check for an applicable skill.

## 2. Mandatory External Architectural Review (GPT-5.4-mini)
When designing a new feature, proposing a refactoring, or finalizing a Design Specification (typically during the `brainstorming` phase):
- The Agent **MUST NOT** proceed directly to `writing-plans` or implementation.
- The Agent **MUST** submit the drafted Design Spec to the external architectural review model (`codex gpt-5.4-mini` or the user's configured OpenAI model).
- **Execution:** Use the project's internal script (e.g., `test_openai_api.py`) passing the `.env.openai` credentials, or request the user to provide authorization if missing.
- **Integration:** The feedback from the external Senior Architect MUST be summarized, presented to the user, and integrated into the revised design before generating the atomic tasks.

## 3. Tech Stack Constraints
- **Frontend:** Next.js, Tailwind CSS, Shadcn UI, React Query (for server state), Zustand (for local UI state only), Masonry.
- **Backend:** Python FastAPI, Celery + Redis (Queue), PostgreSQL (target DB), WebSockets/SSE (Real-time).
- **Asset Storage:** OSS/R2 (Originals + Thumbnails + Previews).
