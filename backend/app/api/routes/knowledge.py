from fastapi import APIRouter, HTTPException, status, Depends
from app.modules.knowledge.main import Ingestion
from app.modules.knowledge.document import ALLOWED_EXTENSIONS
from pathlib import Path
from app.core.models import FileExt
from pydantic import BaseModel
from app.modules.knowledge.ollama import (
    ollama_embed,
    OllamaMetadataExtractor,
    answer_question,
)
from app.api.deps import SessionDep
from app.modules.knowledge.db import search_candidates, find_all
import json
import asyncio
from fastapi.responses import StreamingResponse
from app.core.models import Document


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest/")
async def ingest(ingestion: Ingestion = Depends(Ingestion)) -> dict:
    ext = ingestion.get_file_ext()

    if not ingestion.allowed_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext.value}' not allowed. Allowed are: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    await ingestion.create_file()

    if ext == FileExt.MD:
        ingestion.ingest_md()
    else:
        content = await ingestion.ingest_pdf()

    return {"msg": content}


class Question(BaseModel):
    text: str


async def message_generator(text: str):
    for i in range((len(text))):
        # Simulate some asynchronous work or delay
        await asyncio.sleep(0.05)
        # Yield the message chunk, formatted as JSON with a newline for clarity
        yield text[i]


@router.post("/asking/")
async def asking(
    session: SessionDep,
    q: str,
    extractor: OllamaMetadataExtractor = Depends(OllamaMetadataExtractor),
) -> dict:
    metadata = await extractor.extract(q)
    print("extracted meta = ", metadata)
    if metadata.intent == "search":
        documents = find_all(session, metadata)

        return {
            "msg": "".join(
                [
                    f"เลขที่สัญญา:{d.contact_number} ชื่อ:{d.doc_metadata['title']} หน่วยงาน:{d.doc_metadata['agency']}"
                    for d in documents
                ]
            )
        }
        # return StreamingResponse(message_generator(msg), media_type="application/json")

    # emb = await ollama_embed(q.text)
    # candidates = search_candidates(session, emb, metadata)

    # print("\n--- Retrieved Chunks ---")
    # for c in candidates:
    #     print(c["score"])
    #     print(c["text"][:200], "\n")

    # ans = await answer_question(q.text, candidates)
    # print(ans)
    return {"msg": metadata}
