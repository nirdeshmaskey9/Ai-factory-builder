from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from datetime import datetime, timezone
from uuid import uuid4

TaskType = Literal["general", "coding", "research", "planning"]


class PlanStep(BaseModel):
    index: int = Field(ge=0, description="0-based step order")
    action: str = Field(..., description="What to do")
    rationale: str = Field(..., description="Why this step exists")


class DispatchRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User instruction or goal")
    task_type: TaskType = Field("general", description="Type of task for routing")

    @field_validator("prompt")
    @classmethod
    def no_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt cannot be empty or whitespace")
        return v


class DispatchResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    request_id: str
    created_at: datetime
    task_type: TaskType
    steps: List[PlanStep]
    estimated_tokens: int
    model_name: str = "stub/planner-v0"
    notes: Optional[str] = None

    @classmethod
    def make(
        cls,
        task_type: TaskType,
        steps: List[PlanStep],
        estimated_tokens: int,
        notes: Optional[str] = None,
    ) -> "DispatchResponse":
        return cls(
            request_id=str(uuid4()),
            created_at=datetime.now(timezone.utc),
            task_type=task_type,
            steps=steps,
            estimated_tokens=estimated_tokens,
            notes=notes,
        )


class ErrorResponse(BaseModel):
    detail: str
