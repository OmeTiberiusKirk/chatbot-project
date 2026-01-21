from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from enum import Enum
from sqlalchemy import (
    String,
    Text,
    Integer,
    ForeignKey,
    TIMESTAMP,
    JSON,
    func,
)
from pgvector.sqlalchemy import Vector
from typing import Literal


class FileExt(Enum):
    PDF = 'pdf'
    MD = 'md'


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(50))
    checksum: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False)
    doc_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # relationships
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __init__(
        self,
        source: str,
        source_type: Literal["pdf", "md"],
        checksum: str,
        chunks: Mapped[list["Chunk"]]
    ):
        self.source = source
        self.source_type = source_type
        self.checksum = checksum
        self.chunks = chunks


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # relationships
    document: Mapped["Document"] = relationship(back_populates="chunks")
    embedding: Mapped["Embedding"] = relationship(
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __init__(
        self,
        content: str,
        content_hash: str,
        token_count: int | None
    ):
        self.content = content
        self.content_hash = content_hash
        self.token_count = token_count


class Embedding(Base):
    __tablename__ = "embeddings"

    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(1536)  # ปรับตาม model embedding
    )

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # relationships
    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")
