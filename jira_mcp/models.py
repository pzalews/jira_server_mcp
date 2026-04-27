from __future__ import annotations
import os
from typing import Annotated, Any, Optional
from pydantic import BaseModel, Field, field_validator

IssueKey = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]+-\d+$")]
ProjectKey = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]*$")]


class CreateIssueInput(BaseModel):
    project_key: ProjectKey
    summary: str = Field(..., min_length=1, max_length=255)
    issue_type: str = Field("Task")
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)


class UpdateIssueInput(BaseModel):
    issue_key: IssueKey
    summary: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[list[str]] = None
    components: Optional[list[str]] = None


class AddAttachmentInput(BaseModel):
    issue_key: IssueKey
    filename: str = Field(..., min_length=1)
    content_base64: str
    mime_type: str = Field("application/octet-stream")

    @field_validator("filename")
    @classmethod
    def no_path_traversal(cls, v: str) -> str:
        safe = os.path.basename(v)
        if not safe or safe != v or ".." in v:
            raise ValueError(f"Invalid filename: {v!r}")
        return safe


class CreateSprintInput(BaseModel):
    board_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    goal: Optional[str] = None
