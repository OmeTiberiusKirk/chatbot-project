from fastapi import APIRouter, HTTPException, status, Depends
from app.services.knowledge import Ingestion, ALLOWED_EXTENSIONS
from pathlib import Path
from app.core.models import FileExt


router = APIRouter(prefix="/knowledge", tags=["knowledge"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest/")
async def ingest(ingestion: Ingestion = Depends(Ingestion)) -> dict:
    extension = ingestion.get_file_ext()

    try:
        if not ingestion.allowed_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{extension}' not allowed. Allowed are: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        await ingestion.create_file()

        if extension[1:] == FileExt.MD.value:
            ingestion.ingest_md()
        else:
            content = ingestion.ingest_pdf()
        return {"msg": content}
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.__str__()
        )
    finally:
        await ingestion.upload_file.close()
