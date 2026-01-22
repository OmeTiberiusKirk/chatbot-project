from fastapi import UploadFile, Form
from pypdf import PdfReader
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from types import MethodType
from app.api.deps import SessionDep
from typing import Annotated

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

        # bind related functions
        from app.modules.knowledge.image_processing import read_pdf_with_ocr
        from app.modules.knowledge.document import (
            get_file_ext,
            create_file,
            allowed_file,
        )
        from app.modules.knowledge.db import insert_document

        self.read_pdf_with_ocr = MethodType(read_pdf_with_ocr, self)
        self.get_file_ext = MethodType(get_file_ext, self)
        self.create_file = MethodType(create_file, self)
        self.allowed_file = MethodType(allowed_file, self)
        self.insert_document = MethodType(insert_document, self)

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
