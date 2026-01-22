from fastapi import APIRouter, HTTPException, status, Depends
from app.modules.knowledge.main import Ingestion
from app.modules.knowledge.document import ALLOWED_EXTENSIONS
from pathlib import Path
from app.core.models import FileExt


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
        content = ingestion.ingest_pdf()

    return {"msg": content}
