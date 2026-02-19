from concurrent.futures import ThreadPoolExecutor
import asyncio
import ollama
from app.modules.knowledge.schemas import DocumentMetadata
from app.modules.knowledge.config import (
    EMBED_MODEL,
    LLM_MODEL,
    NOT_FOUND_THRESHOLD,
    METADATA_PROMPT,
    QUESTION_PROMPT,
)
import json
from fastapi import HTTPException, status


# -----------------------------
# Async Ollama
# -----------------------------
_executor = ThreadPoolExecutor()


async def ollama_embed(text: str, model=EMBED_MODEL) -> list[float]:
    def _run():
        try:
            return ollama.embed(model=model, input=text)
        except ConnectionError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=e.__str__(),
            )

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(_executor, _run)

    vec = resp.get("embeddings") or resp.get("embedding")
    if isinstance(vec, list) and isinstance(vec[0], list):
        return vec[0]
    return vec


async def ollama_generate(prompt: str, model=LLM_MODEL):
    def _run():
        r = ollama.generate(model=model, prompt=prompt)
        return r.response

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(_executor, _run)
    # return resp.get("content") or ""
    return resp


class OllamaMetadataExtractor:
    def __init__(self):
        pass

    async def extract(self, question: str) -> DocumentMetadata:
        try:
            prompt = METADATA_PROMPT.format(question=question)
            raw = await ollama_generate(prompt)
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            return DocumentMetadata(**data)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Ollama: {raw}")
        except ollama.ResponseError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.__str__()
            )


async def answer_question(question, top_chunks):
    if not top_chunks or top_chunks[0]["score"] < NOT_FOUND_THRESHOLD:
        return "Not found in document."

    context = "\n\n---\n\n".join([f"{c['text']}" for c in top_chunks])
    prompt = QUESTION_PROMPT.format(context, question)
    return (await ollama_generate(prompt)).strip()
