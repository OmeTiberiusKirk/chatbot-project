import hashlib
from fastapi import UploadFile
from pypdf import PdfReader
import shutil
from app.core.models import Document, Chunk
from app.api.deps import SessionDep
from pathlib import Path
from typing import BinaryIO
from app.api.deps import SessionDep

# Create an upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class Knowledge:
    file_path: str
    file: BinaryIO
    session: SessionDep

    def __init__(self, file: UploadFile, session: SessionDep):
        self.file_path = UPLOAD_DIR / file.filename
        self.file = file.file
        self.session = session

    def __get_hashed_doc(self) -> str:
        reader = PdfReader(self.file)
        pages = [page.extract_text() for _, page in enumerate(reader.pages)]
        doc_hash = self.__sha256("".join(pages))
        return doc_hash

    def __sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def create_file(self) -> None:
        with open(self.file_path, "wb") as buffer:
            shutil.copyfileobj(self.file, buffer)

    def insert_document(self) -> None:
        doc = Document(
            source=f"{self.file_path}",
            source_type="pdf",
            checksum=self.__get_hashed_doc(),
            chunks=[
                Chunk(
                    content="content....",
                    content_hash="2f2fj2fjlfjljwelf",
                    token_count=2
                )
            ]
        )

        self.session.add(doc)
        self.session.commit()
