from concurrent.futures import ThreadPoolExecutor
import asyncio
import ollama

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5"

# -----------------------------
# Async Ollama
# -----------------------------
_executor = ThreadPoolExecutor()


async def ollama_embed(text: str, model=EMBED_MODEL) -> list[float]:
    def _run():
        print("embbeding.......")
        return ollama.embed(model=model, input=text)

    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(_executor, _run)

    vec = resp.get("embeddings") or resp.get("embedding")
    if isinstance(vec, list) and isinstance(vec[0], list):
        return vec[0]
    return vec
