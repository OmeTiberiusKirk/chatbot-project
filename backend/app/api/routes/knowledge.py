from fastapi import APIRouter, UploadFile, HTTPException, status
from app.api.deps import SessionDep
from app.services.knowledge import (
    create_file,
    allowed_file,
    ALLOWED_EXTENSIONS,
    FileExt,
    ingest_md,
    ingest_pdf
)
from pathlib import Path
import os

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest/")
async def ingest(session: SessionDep, file: UploadFile):
    file_path = UPLOAD_DIR / file.filename
    _, extension = os.path.splitext(file.filename)

    try:
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{extension}' not allowed. Allowed are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        await create_file(file_path, file)

        if (extension[1:] == FileExt.MD.value):
            ingest_md()
        else:
            ingest_pdf(file_path)
        return {"content": "content"}
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.__str__()
        )
    finally:
        await file.close()
