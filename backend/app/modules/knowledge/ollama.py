from concurrent.futures import ThreadPoolExecutor
import asyncio
import ollama
from pydantic import BaseModel
from app.modules.knowledge.config import (
    EMBED_MODEL,
    LLM_MODEL,
    METADATA_PROMPT,
    NOT_FOUND_THRESHOLD,
)
import json


# -----------------------------
# Async Ollama
# -----------------------------
_executor = ThreadPoolExecutor()


async def ollama_embed(text: str, model=EMBED_MODEL) -> list[float]:
    def _run():
        return ollama.embed(model=model, input=text)

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(_executor, _run)

    vec = resp.get("embeddings") or resp.get("embedding")
    if isinstance(vec, list) and isinstance(vec[0], list):
        return vec[0]
    return vec


async def ollama_generate(prompt: str, model=LLM_MODEL):
    def _run():
        messages = [
            {"role": "system", "content": "คุณเป็นผู้ช่วยที่ตอบเป็นภาษาไทยเท่านั้น"},
            {"role": "user", "content": prompt},
        ]
        resp = ollama.chat(model=model, messages=messages)
        return resp.message
        # return ollama.generate(model=model, prompt=prompt)

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(_executor, _run)
    return resp.get("content") or ""


class QuestionMetadata(BaseModel):
    agency: str
    year: int


class OllamaMetadataExtractor:
    def __init__(self):
        pass

    async def extract(self, question: str) -> QuestionMetadata:
        prompt = METADATA_PROMPT.format(question=question)
        raw = await ollama_generate(prompt)
        clean = raw.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(clean)
            return QuestionMetadata(**data)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Ollama: {raw}")


async def answer_question(question, top_chunks):
    if not top_chunks or top_chunks[0]["score"] < NOT_FOUND_THRESHOLD:
        return "Not found in document."

    context = "\n\n---\n\n".join([f"{c['text']}" for c in top_chunks])

    prompt = f"""
    - ตอบจากข้อมูลที่ให้เท่านั้น
    - ถ้าไม่มีข้อมูล ให้ตอบว่า "ไม่พบข้อมูลในเอกสาร"
    - ห้ามเดา ห้ามสรุปเกินข้อมูล

    CONTEXT:
    {context}

    QUESTION:
    {question}
    """
    return (await ollama_generate(prompt)).strip()
