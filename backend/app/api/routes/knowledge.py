from fastapi import APIRouter

router = APIRouter(prefix="/knowledges", tags=["knowledges"])


@router.get("/")
def root():
    return {"Hello": "knowledges"}
