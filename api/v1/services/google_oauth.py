from fastapi import BackgroundTasks, Depends, HTTPException
from api.core.dependencies.email_sender import send_email
from api.db.database import get_db
from api.v1.models.user import User
from api.v1.models.user import User
from api.v1.models.profile import Profile
from api.core.base.services import Service
from sqlalchemy.orm import Session
from typing import Annotated
from api.v1.schemas.google_oauth import Tokens
from api.v1.services.user import user_service


class GoogleOauthServices(Service):
    """Handles database operations for google oauth"""

    def create(
        self, background_tasks: BackgroundTasks, google_response: dict, db: Session
    ):
        """
        Creates a user using information from google.

        Args:
            google_response: Raw data from google oauth2
            db: database session to manage database operation

        Returns:
            user: The user object if user already exists or if newly created
            False: for when Authentication fails
        """

        try:
            new_user = self.create_new_user(google_response, db)
            background_tasks.add_task(
                send_email,
                recipient=new_user.email,
                template_name="welcome.html",
                subject="Welcome to HNG Boilerplate",
                context={
                    "first_name": new_user.first_name,
                    "last_name": new_user.last_name,
                },
            )
            return new_user
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error {e}")

    def fetch(self):
        return super().fetch()

    def fetch_all(self, db: Annotated[Session, Depends(get_db)]):
        return super().fetch_all()

    def delete(self):
        """
        Delete method
        """
        pass

    def update(self):
        return super().update()

    def generate_tokens(self, user: object):
        """
        Creates a resnpose for the end user

        Args:
            user: the user object
        Returns:
            tokens: the object containing access and refresh tokens for the user
        """
        try:
            # create access token
            access_token = user_service.create_access_token(user.id)
            # create refresh token
            refresh_token = user_service.create_access_token(user.id)
            # create a token data for response
            tokens = Tokens(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )
            return tokens
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error {e}")

    def create_new_user(
        self, 
        google_response: dict, 
        db: Annotated[Session, Depends(get_db)]
        ):
        """
        Creates a new user and their associated profile and OAuth data.

        Args:
            user_info: User information from Google OAuth.
            google_response: The response from Google OAuth.
            db: The database session object for connection.

        Returns:
            new user: The newly created user object.
            False: If an error occurred.
        """
        try:
            # Create a new user object
            new_user = User(
                first_name=google_response.get("given_name"),
                last_name=google_response.get("family_name"),
                email=google_response.get("email"),
                avatar_url=google_response.get("picture"),
            )
            
            # Add the new user to the session and commit to get the user ID
            db.add(new_user)
            db.commit()
            db.refresh(new_user)  # Refresh to get the newly assigned user ID

            # Now create the associated profile
            profile = Profile(user_id=new_user.id)
            db.add(profile)
            db.commit()

            return new_user
        except Exception as e:
            db.rollback()  # Rollback the transaction in case of error
            raise HTTPException(status_code=500, detail=f"Error {e}")

