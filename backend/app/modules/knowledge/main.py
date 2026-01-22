from fastapi import UploadFile, Form, HTTPException, status
from pypdf import PdfReader
from app.core.models import Document, ChunkModel
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from types import MethodType
from app.api.deps import SessionDep
from typing import Annotated
from sqlalchemy.exc import IntegrityError

POPPLER_PATH = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class KnowledgeService:
    session: SessionDep

    def __init__(self, session: SessionDep):
        self.session = session


class Ingestion(KnowledgeService):
    upload_file = UploadFile
    file_path: Path
    file: BinaryIO
    doc_meta: dict

    def __init__(
        self,
        session: SessionDep,
        upload_file: UploadFile,
        agency: Annotated[str, Form()],
        year: Annotated[int, Form()],
    ):

        super().__init__(session)
        self.upload_file = upload_file
        self.file_path = UPLOAD_DIR / (upload_file.filename or "")
        self.file = upload_file.file
        self.doc_meta = {"agency": agency, "year": year}

        from app.modules.knowledge.image_processing import read_pdf_with_ocr
        from app.modules.knowledge.document import (
            get_file_ext,
            create_file,
            allowed_file,
        )

        # bind related functions
        self.read_pdf_with_ocr = MethodType(read_pdf_with_ocr, self)
        self.get_file_ext = MethodType(get_file_ext, self)
        self.create_file = MethodType(create_file, self)
        self.allowed_file = MethodType(allowed_file, self)

    def insert_document(
        self,
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

    def ingest_md(self) -> None:
        print("ingest markdown")
        with open(self.file_path, "r") as file:
            content = self.file.read()
            print(content)

    def ingest_pdf(self):
        from app.modules.knowledge.document import sha256_bytes, chunk_texts
        from app.modules.knowledge.text_normalization import clean_thai_text

        with open(self.file_path, "rb") as b:
            checksum = sha256_bytes(b.read())
            reader = PdfReader(b)
            pages: list[tuple[int, str]] = []

            for pageno, page in enumerate(reader.pages):
                t = page.extract_text() or ""
                t = clean_thai_text(t)
                pages.append((pageno, t))

            chunks = chunk_texts(pages)
            self.insert_document(checksum, chunks)
            return chunks
