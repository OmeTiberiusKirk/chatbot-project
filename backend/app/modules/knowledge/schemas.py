from pydantic import BaseModel, field_validator
from typing import Optional, Literal


class DocumentMetadata(BaseModel):
    agency: Optional[str] = None
    year: Optional[int] = None
    intent: Optional[Literal["count", "search", "summary"]] = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 3000):
            return None
        return v
