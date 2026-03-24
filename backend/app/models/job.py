import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    # status: queued, running_r, success, error, cancelled
    status: Mapped[str] = mapped_column(String(50), default="queued")
    # stage: queued, fetching_data, running_r, generating_interpretation, done
    stage: Mapped[str] = mapped_column(String(50), default="queued")
    r_script: Mapped[str] = mapped_column(Text, nullable=True)
    # Phase 2: Data pipeline columns
    prompt: Mapped[str] = mapped_column(Text, nullable=True)
    data_sources: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of {source, series_id, display_name}
    date_range: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: {start: str, end: str}
    resolution_method: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., "mean", "last", "sum", "ffill"
    analysis_mode: Mapped[str] = mapped_column(String(20), nullable=True)  # "quick" or "detailed"
    assumptions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of assumption strings
    cached_data_keys: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of Redis cache keys used
    result_stdout: Mapped[str] = mapped_column(Text, nullable=True)
    result_stderr: Mapped[str] = mapped_column(Text, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
