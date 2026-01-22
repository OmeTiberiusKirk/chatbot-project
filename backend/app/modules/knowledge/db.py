from app.core.models import Document, ChunkModel
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.modules.knowledge.main import Ingestion


def insert_document(
    self: Ingestion,
    checksum: str,
    chunks: list[tuple[int, str]],
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
                    token_count=1,
                )
                for chunk in chunks
            ],
        )
        self.session.add(doc)
        self.session.commit()
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.args[0])
