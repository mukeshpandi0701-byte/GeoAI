from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """The small set of details needed to create a Phase 2 project record."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    location: str = Field(default="", max_length=160)
