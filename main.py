import uvicorn
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware  # required by google oauth
from starlette.middleware.base import BaseHTTPMiddleware

from api.core.config import settings
from api.utils.logger import logger
from api.v1.routes.main import main_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan, title="Boilerplate")

# In-memory request counter by endpoint and IP address
request_counter = defaultdict(lambda: defaultdict(int))


# Middleware to track request counts and IP addresses
class RequestCountMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        endpoint = request.url.path
        ip_address = request.client.host
        request_counter[endpoint][ip_address] += 1
        response = await call_next(request)
        return response


app.add_middleware(RequestCountMiddleware)
app.include_router(main_router)


# Endpoint to get request stats
@app.get("/request-stats", response_class=JSONResponse)
async def get_request_stats():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "request_counts": {
                endpoint: dict(ips) for endpoint, ips in request_counter.items()
            },
            "message": "endpoints request retreived successfully",
        },
    )


app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"URL": "", "message": "Welcome to the boilerplate API"},
    )


@app.get("/probe", tags=["Home"])
async def probe():
    return {"message": "I am the Python FastAPI API responding"}


# REGISTER EXCEPTION HANDLERS
@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    """HTTP exception handler"""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    """Validation exception handler"""

    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": errors,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception(request: Request, exc: IntegrityError):
    """Integrity error exception handlers"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=400,
        content={
            "status": False,
            "status_code": 400,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


@app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    """Other exception handlers"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=7001,
        reload=True,
        workers=4,
    )
