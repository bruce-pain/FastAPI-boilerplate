import uvicorn
import slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
import uvicorn, os
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware  # required by google oauth
from slowapi import Limiter
from slowapi.util import get_remote_address
from api.utils.logger import logger
from api.utils.success_response import success_response
from api.v1.routes import api_version_one
from api.core.settings import settings
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.middleware import SlowAPIMiddleware
from collections import defaultdict
from slowapi.errors import RateLimitExceeded
from scripts.presets import (
    load_avatars_in_db,
    load_audio_in_db,
    load_billing_plans_in_db,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_avatars_in_db()
    load_audio_in_db()
    load_billing_plans_in_db()
    yield


app = FastAPI(lifespan=lifespan, title="Convey API")

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


# Endpoint to get request stats
@app.get("/request-stats", response_class=JSONResponse)
async def get_request_stats():
    return success_response(
        status_code=status.HTTP_200_OK,
        message="endpoints request retreived successfully",
        data={
            "request_counts": {
                endpoint: dict(ips) for endpoint, ips in request_counter.items()
            }
        },
    )


# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

# Register the rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        {"detail": "Rate limit exceeded"}, status_code=429
    ),
)
app.add_middleware(SlowAPIMiddleware)

# Set up email templates and css static files
email_templates = Jinja2Templates(directory="api/core/dependencies/email/templates")

MEDIA_DIR = "./media"
os.makedirs(MEDIA_DIR, exist_ok=True)

TEMP_DIR = "./tmp/media"
os.makedirs(TEMP_DIR, exist_ok=True)

# Load up media static files
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
app.mount("/tmp/media", StaticFiles(directory=TEMP_DIR), name="tmp-media")
app.mount("/presets", StaticFiles(directory="./presets"), name="presets")

origins = ["http://localhost:3000", "http://localhost:3001", "https://staging.tifi.tv"]


app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_version_one)


@app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return success_response(
        message="Welcome to API", status_code=status.HTTP_200_OK, data={"URL": ""}
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
