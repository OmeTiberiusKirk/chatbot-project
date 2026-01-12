from fastapi import APIRouter, UploadFile, HTTPException, status
from pathlib import Path
import shutil
from app.services.knowledge import hashReader


router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Create an upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/")
def root():
    return {"Hello": "knowledge"}


@router.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    doc_hash = hashReader(file)
    print(doc_hash)

    # for pageno, page in enumerate(reader.pages):
    #     t = page.extract_text() or ""
    #     print(t)

    # Define the destination path
    file_path = UPLOAD_DIR / file.filename

    # Stream the file to disk in chunks
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}",
        )
    finally:
        await file.close()
    return {"filename": file.filename}
