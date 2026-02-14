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


class QuestionMetadata(BaseModel):
    agency: str
    year: int


class OllamaMetadataExtractor:
    def __init__(self):
        pass

    async def extract(self, question: str) -> QuestionMetadata:
        try:
            prompt = METADATA_PROMPT.format(question=question)
            raw = await ollama_generate(prompt)
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            print(data["year"] + 543)
            return QuestionMetadata(year=data["year"], agency=data["agency"])
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Ollama: {raw}")
        except ollama.ResponseError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=e.__str__()
            )


async def answer_question(question, top_chunks):
    if not top_chunks or top_chunks[0]["score"] < NOT_FOUND_THRESHOLD:
        return "Not found in document."

    context = "\n\n---\n\n".join([f"{c['text']}" for c in top_chunks])

    prompt = f"""
    คุณเป็นผู้ช่วยที่ตอบคำถามโดยอ้างอิงจากข้อมูลที่ให้มาเท่านั้น

    ข้อบังคับ:
    - ตอบเป็นภาษาไทยทั้งหมด
    - ใช้ภาษาสุภาพ ชัดเจน และเป็นทางการ
    - ห้ามเดา หรือแต่งข้อมูลเพิ่มจากความรู้ภายนอก
    - หากข้อมูลใน Context ไม่เพียงพอ ให้ตอบว่า "ไม่พบข้อมูลในเอกสาร"
    - อนุญาตให้ใช้ศัพท์เทคนิคภาษาอังกฤษได้เฉพาะกรณีจำเป็น และต้องอธิบายเป็นภาษาไทย

    รูปแบบคำตอบ:
    - ตอบให้ตรงคำถาม
    - หากมีหลายประเด็น ให้ตอบเป็นข้อ ๆ
    
    ### Context
    {context}

    ### Question
    {question}

    ### Answer (ตอบเป็นภาษาไทย):
    """
    print(prompt)
    return (await ollama_generate(prompt)).strip()
