from fastapi import BackgroundTasks, Depends, APIRouter, status, HTTPException, Request
from starlette.responses import RedirectResponse
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from decouple import config
from api.v1.schemas.user import UserCreate
import os
from fastapi.security import OAuth2PasswordBearer
from api.db.database import get_db
from api.v1.services.google_oauth import GoogleOauthServices
from api.utils.success_response import success_response
from api.v1.schemas.google_oauth import OAuthToken
from api.v1.services.user import user_service
from fastapi.encoders import jsonable_encoder
import requests
from datetime import timedelta

google_auth = APIRouter(prefix="/auth", tags=["Authentication"])
FRONTEND_URL = os.environ.get("FRONTEND_URL")


@google_auth.post("/google", status_code=200)
async def google_login(background_tasks: BackgroundTasks, token_request: OAuthToken, db: Session = Depends(get_db)):
    """
    Handles Google OAuth login.

    Args:
    - background_tasks (BackgroundTasks): Background tasks to be executed.
    - token_request (OAuthToken): OAuth token request.
    - db (Session): Database session.

    Returns:
    - JSONResponse: JSON response with user details and access token.

    Example:
    ```
    POST /google HTTP/1.1
    Content-Type: application/json

    {
        "id_token": "your_id_token_here"
    }
    ```
    """
    try:

        id_token = token_request.id_token
        profile_endpoint = f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}'
        profile_response = requests.get(profile_endpoint)
        
        if profile_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token or failed to fetch user info")
        
        profile_data = profile_response.json()

        
        email = profile_data.get('email')
        user = user_service.get_user_by_email(db=db, email=email)

        # Check if the user exists
        if user:
            # User already exists, return their details
            access_token = user_service.create_access_token(user_id=user.id)
            refresh_token = user_service.create_refresh_token(user_id=user.id)
            response = JSONResponse(
                status_code=200,
                content={
                    "status_code": 200,
                    "message": "Login successful",
                    "access_token": access_token,
                    "data": {
                        "user": jsonable_encoder(
                            user, exclude=["password", "is_deleted", "updated_at"]
                        )
                    },
                },
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                expires=timedelta(days=30),
                httponly=True,
                secure=True,
                samesite="none",
            )
            return response
        else:

            google_oauth_service = GoogleOauthServices()
            # User does not exist, create a new user
            user = google_oauth_service.create(background_tasks=background_tasks, db=db, google_response=profile_data)
            access_token = user_service.create_access_token(user_id=user.id)
            refresh_token = user_service.create_refresh_token(user_id=user.id)
            response = JSONResponse(
                status_code=200,
                content={
                    "status_code": 200,
                    "message": "Login successful",
                    "access_token": access_token,
                    "data": {
                        "user": jsonable_encoder(
                            user, exclude=["password", "is_deleted", "updated_at"]
                        )
                    },
                },
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                expires=timedelta(days=30),
                httponly=True,
                secure=True,
                samesite="none",
            )
            return response
    except ValueError:
        # Invalid ID token
        return JSONResponse(status_code=401, content={"error": "Invalid ID token"})


@google_auth.get("/google/initiate")
async def initiate_google_auth():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    scope = "openid email profile"
    response_type = "code"
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}"
    return RedirectResponse(url=auth_url, status_code=302)


@google_auth.get("/google/callback")
async def google_callback(background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code is missing")
    
    # Exchange the authorization code for an access token
    token_url = "https://oauth2.googleapis.com/token"
    token_response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI"),
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        },
    )

    if token_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange authorization code")
    
    token_data = token_response.json()
    id_token = token_data.get("id_token")
    
    # Validate the ID token
    profile_endpoint = f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}"
    profile_response = requests.get(profile_endpoint)

    if profile_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token")
    
    profile_data = profile_response.json()
    
    # Check if the user exists or create a new user
    google_oauth_service = GoogleOauthServices()
    email = profile_data.get('email')
    user = user_service.get_user_by_email(db=db, email=email)
    if not user:
        # Create a new user if they don't exist

        user = google_oauth_service.create(background_tasks=background_tasks, google_response=profile_data, db=db)
    
    # Generate tokens
    access_token = user_service.create_access_token(user_id=user.id)
    refresh_token = user_service.create_refresh_token(user_id=user.id)

    response = JSONResponse(
        status_code=200,
        content={
            "status_code": 200,
            "message": "Authenticated successfully",
            "access_token": access_token,
            "id_token": id_token,
            "data": {
                "user": jsonable_encoder(
                    user,
                    exclude=['password', 'is_superadmin', 'is_deleted', 'is_verified', 'updated_at']
                )
            }
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        expires=timedelta(days=60),
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response
