from app.core.models import Document, ChunkModel, EmbeddingModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from fastapi import HTTPException, status
from app.modules.knowledge.main import Ingestion
from app.modules.knowledge.document import count_tokens
from app.api.deps import SessionDep
from app.modules.knowledge.config import TOP_K
from app.modules.knowledge.ollama import QuestionMetadata
import json


def insert_document(
    self: Ingestion,
    checksum: str,
    chunks: list[tuple[int, str]],
    embeddings: list[list[float]],
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
                    embedding=EmbeddingModel(embedding=emb),
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


# def search_candidate(session: SessionDep, emb: list[float]):
#     assert isinstance(emb, list)
#     assert all(isinstance(x, float) for x in emb)
#     assert len(emb) == 768
#     stmt = (
#         select(
#             (1 - EmbeddingModel.embedding.op("<=>")(
#                 cast(bindparam("emb"), Vector(len(emb)))
#             )).label("score")
#         )
#         .select_from(EmbeddingModel)
#         .limit(10)
#     )

#     session.scalars(stmt, {"emb": emb})


def search_candidates(
    session: SessionDep,
    emb: list[float],
    meta: QuestionMetadata,
):
    stmt = text(
        """
        select ch.content, d.doc_metadata, 1 - (emb.embedding <=> cast(:emb AS vector)) AS score
        from embeddings as emb
        join chunks as ch on ch.chunk_id = emb.chunk_id
        join documents as d on d.document_id = ch.document_id
        where d.doc_metadata @> :meta
        order by score desc
        limit :top_k
    """
    )

    rows = session.exec(
        statement=stmt,
        params={
            "emb": emb,
            "top_k": TOP_K,
            "meta": json.dumps({k: v for k, v in meta if v is not None}),
        },
    )

    candidates: list[dict] = []
    for t, m, s in rows:
        candidates.append({"text": t, "meta": m, "score": s})

    return candidates


def to_pgvector(vec):
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
