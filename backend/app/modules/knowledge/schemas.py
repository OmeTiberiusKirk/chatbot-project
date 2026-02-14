from pydantic import BaseModel, field_validator
from typing import Optional


class DocumentMetadata(BaseModel):
    agency: Optional[str] = None
    year: Optional[int] = None
    document_type: Optional[str] = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        if v is not None and (v < 1900 or v > 2100):
            return None
        return v
