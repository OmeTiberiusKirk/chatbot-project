import hashlib
from app.core.models import FileExt
import os
from app.modules.knowledge.text_normalization import thai_sentence_split
from fastapi import UploadFile
from typing import cast
from app.modules.knowledge.main import Ingestion
import tiktoken
from pypdf import PdfReader
from app.modules.knowledge.text_normalization import clean_thai_text


ALLOWED_EXTENSIONS = {"md", "pdf"}
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60


def extract_text_from_pdf(self: Ingestion) -> tuple[list[tuple[int, str]], str]:
    with open(self.file_path, "rb") as b:
        checksum = sha256_bytes(b.read())
        reader = PdfReader(b)
        pages: list[tuple[int, str]] = []

        for pageno, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            t = clean_thai_text(t)
            pages.append((pageno, t))

        return pages, checksum


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_text(text: str) -> str:
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_file_ext(self: Ingestion) -> FileExt:
    _, extension = os.path.splitext(self.file_path)
    if extension[1:] == FileExt.PDF.value:
        return FileExt.PDF
    else:
        return FileExt.MD


async def create_file(self: Ingestion) -> None:
    content = await cast(UploadFile, self.upload_file).read()
    with open(self.file_path, "wb") as buffer:
        buffer.write(content)


def allowed_file(self: Ingestion) -> bool:
    # Split the filename into name and extension
    ext = get_file_ext(self)
    # Check if the extension (in lowercase) is in the allowed set
    return ext.value in ALLOWED_EXTENSIONS


def chunk_texts(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    chunks = []
    chunk_id = 0
    for pageno, text in pages:
        sentences = thai_sentence_split(text)
        # join sentences into windows of approx chunk_size words (word ~ token)
        words = " ".join(sentences).split()
        i = 0
        while i < len(words):
            chunk_words = words[i: i + CHUNK_SIZE]
            chunk_text = " ".join(chunk_words).strip()

            if chunk_text:
                chunks.append(
                    (
                        pageno,
                        # "metadata": METADATA,
                        chunk_text,
                    )
                )
                chunk_id += 1

            i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(enc.encode(text))
