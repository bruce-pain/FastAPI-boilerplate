from fastapi import APIRouter

from app.features.auth.routes import auth_router

main_router = APIRouter(prefix="/api/v1")
main_router.include_router(auth_router)
