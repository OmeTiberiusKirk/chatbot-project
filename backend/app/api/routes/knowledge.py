from fastapi import APIRouter, UploadFile, HTTPException, status
from app.api.deps import SessionDep
from app.services.knowledge import Knowledge, ALLOWED_EXTENSIONS
from pathlib import Path
import os
from app.core.models import FileExt

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest/")
async def ingest(session: SessionDep, file: UploadFile):
    print(file.headers)
    knl = Knowledge(session, file)
    extension = knl.get_file_ext()

    try:
        if not knl.allowed_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{extension}' not allowed. Allowed are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        await knl.create_file()

        if (extension[1:] == FileExt.MD.value):
            knl.ingest_md()
        else:
            content = knl.ingest_pdf()
        return {"content": content}
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
