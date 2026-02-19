from fastapi import APIRouter, HTTPException, status, Depends
from pathlib import Path
import json
import asyncio
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.models import Document, FileExt
from app.api.deps import SessionDep
from app.modules.knowledge.main import Ingestion
from app.modules.knowledge.db import search_candidates, find_all
from app.modules.knowledge.document import ALLOWED_EXTENSIONS
from app.modules.knowledge.config import SEARCH_PROMPT
from app.modules.knowledge.ollama import (
    ollama_embed,
    OllamaMetadataExtractor,
    answer_question,
    ollama_generate,
)


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
        context = "\n".join(
            [
                f"{i+1}. เลขที่สัญญา:{d.contact_number}, ปี:{d.doc_metadata["year"]}, หน่วยงาน:{d.doc_metadata['agency']}, ชื่อ:{d.doc_metadata['title']}"
                for i, d in enumerate(documents)
            ]
        )
        context = f"รายชื่อโครงการ TOR(Terms of Reference)\n{context}"
        prompt = SEARCH_PROMPT.format(context=context, question=q)
        answer = (await ollama_generate(prompt)).strip()
        print(answer)
        return {"msg": answer}
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
