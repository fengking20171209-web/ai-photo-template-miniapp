"""SQLAlchemy ORM models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, func, Index, JSON
from backend.database import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    prompt = Column(Text)
    revised_prompt = Column(Text)
    image_url = Column(String(1024), nullable=False)
    thumbnail_url = Column(String(1024))
    tags = Column(JSON, default=list)
    description = Column(Text)
    source = Column(String(50))
    source_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_created_at", created_at),
    )


class UserEvent(Base):
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    template_id = Column(String(255), nullable=True, index=True)
    query = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_event_created", event_type, created_at),
    )

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    category = Column(String(100), index=True)
    description = Column(Text)
    current_version_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    content = Column(Text)
    model_hint = Column(String(255))
    system_message = Column(Text)
    parameters_json = Column(JSON)
    change_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    is_active = Column(Boolean, default=True)
    content_hash = Column(String(64))

    __table_args__ = (
        UniqueConstraint("prompt_id", "version", name="uq_prompt_version"),
        UniqueConstraint("prompt_id", "content_hash", name="uq_prompt_content_hash"),
    )

class PromptDraft(Base):
    __tablename__ = "prompt_drafts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    system_message = Column(Text)
    parameters_json = Column(JSON)
    status = Column(String(50), default="draft", index=True)  # draft, published, discarded
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class TaskChain(Base):
    __tablename__ = "task_chains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    status = Column(String(50), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    task_type = Column(String(50))
    status = Column(String(50), index=True)
    input_json = Column(JSON)
    output_json = Column(JSON)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True, index=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    chain_id = Column(Integer, ForeignKey("task_chains.id"), nullable=True, index=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class TaskChainEdge(Base):
    __tablename__ = "task_chain_edges"

    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(Integer, ForeignKey("task_chains.id"), nullable=False, index=True)
    from_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    to_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    edge_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("chain_id", "from_task_id", "to_task_id", name="uq_chain_edge"),
    )


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    task_chain_id = Column(Integer, ForeignKey("task_chains.id"), nullable=True, index=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    mime_type = Column(String(100))
    title = Column(String(255))
    description = Column(Text)
    file_path = Column(String(1024), nullable=False)
    file_url = Column(String(1024))
    thumbnail_path = Column(String(1024))
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    metadata_json = Column(JSON)
    source = Column(String(50), index=True)
    is_favorite = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_assets_task_is_deleted", task_id, is_deleted),
    )


class PromptEvolutionRun(Base):
    __tablename__ = "prompt_evolution_runs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False, index=True)
    base_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=False, index=True)
    status = Column(String(50), default="running")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromptEvolutionCandidate(Base):
    __tablename__ = "prompt_evolution_candidates"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_evolution_runs.id"), nullable=False, index=True)
    variant_text = Column(Text)
    strategy = Column(String(100))
    status = Column(String(50), default="pending")  # pending, promoted, rejected
    promoted_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PromptEvaluationRecord(Base):
    __tablename__ = "prompt_evaluation_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    feedback = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelPersona(Base):
    """A reusable character/model for identity-consistent generation.

    No LoRA/training: consistency is achieved via a bound reference face image
    (reused as img2img input) plus auto-injected identity/negative prompts.
    """
    __tablename__ = "model_personas"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    reference_image = Column(Text)        # base64 data URI of the bound face
    identity_prompt = Column(Text)
    negative_prompt = Column(Text)
    tags = Column(JSON, default=list)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

