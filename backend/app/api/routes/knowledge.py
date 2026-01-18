from fastapi import APIRouter, UploadFile, HTTPException, status
from app.api.deps import SessionDep
from app.services.knowledge import Knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest/")
async def ingest(session: SessionDep, file: UploadFile):
    # Stream the file to disk in chunks
    try:
        knl = Knowledge(file, session)
        knl.create_file()
        content = knl.read_pdf_with_ocr()
        # knl.insert_document()
        return {"content": content}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.__str__()
        )
    finally:
        await file.close()
