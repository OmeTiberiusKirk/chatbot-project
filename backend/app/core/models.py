from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, TIMESTAMP, Integer, ForeignKey
from pgvector.sqlalchemy import Vector
from typing import List
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100), nullable=True)
    checksum: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)


class Chunk(Base):
    __tablename__ = "chunk"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(Text, unique=True)
    token_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)

    embedding: Mapped["Embedding"] = relationship(back_populates="chunk")


class Embedding(Base):
    __tablename__ = "embedding"
    id: Mapped[int] = mapped_column(primary_key=True)
    embedding: Mapped[List[float]] = mapped_column(Vector(1024))
    model: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)

    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunk.id"))
    chunk: Mapped["Chunk"] = relationship(back_populates="embedding")


class ChunkDocument(Base):
    __tablename__ = "chunk_document"
    id: Mapped[int] = mapped_column(primary_key=True)
