from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
import enum
from sqlalchemy import (
    String,
    Text,
    Integer,
    ForeignKey,
    TIMESTAMP,
    func,
    Enum,
)
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional


class FileExt(enum.Enum):
    PDF = "pdf"
    MD = "md"


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    # document_id: Mapped[str] = mapped_column(
    #     UUID(as_uuid=True), primary_key=True, default=uuid4
    # )
    contact_number: Mapped[str] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[FileExt] = mapped_column(Enum(FileExt))
    checksum: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    doc_metadata: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # relationships
    chunks: Mapped[list["ChunkModel"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ChunkModel(Base):
    __tablename__ = "chunks"

    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    contact_number: Mapped[str] = mapped_column(
        ForeignKey("documents.contact_number", ondelete="CASCADE"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # relationships
    document: Mapped["Document"] = relationship(back_populates="chunks")
    embedding: Mapped["EmbeddingModel"] = relationship(
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan",
    )


class EmbeddingModel(Base):
    __tablename__ = "embeddings"

    chunk_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(768)  # ปรับตาม model embedding
    )

    # relationships
    chunk: Mapped["ChunkModel"] = relationship(back_populates="embedding")
