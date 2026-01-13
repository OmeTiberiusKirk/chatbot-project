import hashlib
from fastapi import UploadFile
from pypdf import PdfReader
import shutil
from app.core.models import Document
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

    def sha256(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def getHashedDoc(self) -> str:
        reader = PdfReader(self.file)
        pages = [page.extract_text() for _, page in enumerate(reader.pages)]
        doc_hash = self.sha256("".join(pages))
        return doc_hash

    def createFile(self) -> None:
        with open(self.file_path, "wb") as buffer:
            shutil.copyfileobj(self.file, buffer)

    def insertDocument(self) -> None:
        doc = Document(source=f"{self.file_path}", source_type="pdf",
                       checksum=self.getHashedDoc())
        self.session.add(doc)
        self.session.commit()
