from fastapi import UploadFile, Form
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from types import MethodType
from typing import Annotated
from app.modules.knowledge.ollama import ollama_embed


POPPLER_PATH = "C:/Users/stron/Downloads/poppler-25.12.0/Library/bin"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class Ingestion:
    upload_file: UploadFile
    file_path: Path
    file: BinaryIO
    doc_meta: dict

    def __init__(
        self,
        session: SessionDep,
        upload_file: UploadFile,
        contact_number: Annotated[str, Form()],
        title: Annotated[str, Form()],
        agency: Annotated[str, Form()],
        year: Annotated[int, Form()],
    ):
        self.session = session
        self.upload_file = upload_file
        self.file_path = UPLOAD_DIR / (upload_file.filename or "")
        self.file = upload_file.file
        self.contact_number = contact_number
        self.doc_meta = {"title": title, "agency": agency, "year": year}

        # bind related functions
        from app.modules.knowledge.image_processing import read_pdf_with_ocr
        from app.modules.knowledge.db import insert_document
        from app.modules.knowledge.document import (
            get_file_ext,
            create_file,
            allowed_file,
            extract_text_from_pdf,
        )

        self.extract_text_from_pdf = MethodType(extract_text_from_pdf, self)
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

    async def ingest_pdf(self):
        from app.modules.knowledge.document import chunk_texts

        pages, checksum = self.extract_text_from_pdf()
        # await extract_metadata_from_text("".join([page for _, page in pages]))
        chunks = chunk_texts(pages)

        # embed chunks
        embeddings: list[list[float]] = []
        for _, chunk in chunks:
            emb = await ollama_embed(chunk)
            embeddings.append(emb)

        self.insert_document(checksum, chunks, embeddings)
        return chunks
