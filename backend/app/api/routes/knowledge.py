from fastapi import APIRouter, UploadFile, HTTPException, status
from app.api.deps import SessionDep
from app.services.knowledge import Knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest/")
async def ingest(session: SessionDep, file: UploadFile):

    # for pageno, page in enumerate(reader.pages):
    #     t = page.extract_text() or ""
    #     print(t)

    # Define the destination path

    # Stream the file to disk in chunks
    # try:
    #     knl = Knowledge(file, session)
    #     knl.read_pdf_with_ocr()
    #     knl.create_file()
    #     knl.insert_document()
    # except Exception as e:
    #     print(e)
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=e.__str__()
    #     )
    # finally:
    #     await file.close()

    knl = Knowledge(file, session)
    content = knl.read_pdf_with_ocr()

    return {"content": content}
