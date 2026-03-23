from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class JobSubmit(BaseModel):
    # For Phase 1 smoke test; Phase 3 will accept natural language prompts instead
    r_script: str


class JobStatus(BaseModel):
    id: UUID
    status: str
    stage: str
    result_stdout: Optional[str] = None
    result_stderr: Optional[str] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class JobCreated(BaseModel):
    id: UUID
    status: str
