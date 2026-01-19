from fastapi import APIRouter, UploadFile, HTTPException, status
from app.api.deps import SessionDep
from app.services.knowledge import create_file, read_pdf_with_ocr
from multiprocessing import cpu_count
from pathlib import Path

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest/")
async def ingest(session: SessionDep, file: UploadFile):
    file_path = UPLOAD_DIR / file.filename

    try:
        await create_file(file_path, file)
        read_pdf_with_ocr(file_path)

        return {"content": "content"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.__str__()
        )
    finally:
        await file.close()
