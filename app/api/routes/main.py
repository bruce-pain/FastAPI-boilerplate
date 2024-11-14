from fastapi import APIRouter

from app.api.routes.auth import auth

main_router = APIRouter(prefix="/api/v1")

main_router.include_router(router=auth)
