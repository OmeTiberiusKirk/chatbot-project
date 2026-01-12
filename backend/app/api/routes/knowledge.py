from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    status
)
from pathlib import Path
import hashlib
import shutil


router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Create an upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/")
def root():
    return {"Hello": "knowledge"}


@router.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    # doc_hash = sha256(doc.decode("utf-8"))
    # Define the destination path
    file_path = UPLOAD_DIR / file.filename

    # Stream the file to disk in chunks
    try:
        with open(file_path, "wb") as buffer:
            # use shutil.copyfileobj to efficiently copy file-like objects in chunks
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )
    finally:
        await file.close()
    return {"filename": file.filename}


# def sha256(text: str) -> str:
#     return hashlib.sha256(text.encode("utf-8")).hexdigest()
