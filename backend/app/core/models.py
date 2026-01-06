from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey, SmallInteger
from pgvector.sqlalchemy import Vector
from typing import List


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100), nullable=True)
    checksum: Mapped[str] = mapped_column(String, unique=True)

    chunk_document: Mapped["ChunkDocument"] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(Text, unique=True)
    token_count: Mapped[int] = mapped_column(Integer)

    embedding: Mapped["Embedding"] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )
    chunk_document: Mapped["ChunkDocument"] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )


class Embedding(Base):
    __tablename__ = "embedding"

    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("chunk.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[List[float]] = mapped_column(Vector(1024))
    model: Mapped[str] = mapped_column(Text)

    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")


class ChunkDocument(Base):
    __tablename__ = "chunk_document"

    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("chunk.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), primary_key=True
    )
    page: Mapped[int] = mapped_column(SmallInteger)
    section: Mapped[str] = mapped_column(Text)

    chunk: Mapped["Chunk"] = relationship(back_populates="chunk_document")
    document: Mapped["Document"] = relationship(back_populates="chunk_document")
