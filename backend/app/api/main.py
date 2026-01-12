from fastapi import APIRouter
from app.api.routes import knowledge

api_router = APIRouter()
api_router.include_router(knowledge.router)
