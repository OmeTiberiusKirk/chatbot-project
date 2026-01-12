import hashlib
from fastapi import UploadFile
from pypdf import PdfReader


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def hashReader(file: UploadFile) -> str:
    reader = PdfReader(file.file)
    pages = [page.extract_text() for _, page in enumerate(reader.pages)]
    doc_hash = sha256("".join(pages))
    return doc_hash
