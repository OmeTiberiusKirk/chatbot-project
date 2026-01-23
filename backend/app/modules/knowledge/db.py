from app.core.models import Document, ChunkModel, EmbeddingModel
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.modules.knowledge.main import Ingestion
from app.modules.knowledge.document import count_tokens


def insert_document(
    self: Ingestion,
    checksum: str,
    chunks: list[tuple[int, str]],
    embeddings: list[list[float]]
) -> None:
    from app.modules.knowledge.document import hash_text

    try:
        doc = Document(
            source=f"{self.file_path}",
            source_type=self.get_file_ext(),
            checksum=checksum,
            doc_metadata=self.doc_meta,
            chunks=[
                ChunkModel(
                    content=chunk[1],
                    content_hash=hash_text(chunk[1]),
                    token_count=count_tokens(chunk[1]),
                    chunk_index=chunk[0],
                    embedding=EmbeddingModel(
                        embedding=emb
                    )
                )
                for chunk, emb in zip(chunks, embeddings)
            ],
        )
        self.session.add(doc)
        self.session.commit()
    except IntegrityError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document already exists.",
        )


def to_pgvector(vec):
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
