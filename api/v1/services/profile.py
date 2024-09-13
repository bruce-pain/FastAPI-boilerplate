from fastapi import HTTPException
from pydantic import ValidationError
from datetime import datetime
import json
from typing import Any, Optional
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.utils.db_validators import check_model_existence
from api.v1.models.user import User
from api.v1.models.profile import Profile
from api.v1.schemas.profile import ProfileCreateUpdate


class ProfileService(Service):
    '''Profile service functionality'''
    def create():
        pass
    
    def update(self, db: Session, schema: ProfileCreateUpdate, user_id: str):
        '''Updates a Profile, creates one if it doesn't exist'''
        try:
            # Fetch the existing profile and user
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # If profile doesn't exist, create one
            if not profile:
                profile_data = schema.dict(exclude={"email", "avatar_url", "avatar"})
                profile_data["social"] = schema.social
                profile = Profile(**profile_data, user_id=user_id)
                db.add(profile)
            else:
                update_data = schema.dict(exclude={"email", "avatar_url", "avatar"})
                update_data["social"] = schema.social

                for key, value in update_data.items():
                    setattr(profile, key, value)

            # Update user's email and avatar URL if provided
            if schema.email:
                user.email = schema.email
            if schema.avatar_url:
                user.avatar_url = schema.avatar_url

            db.commit()
            db.refresh(profile)
            db.refresh(user)
            
            # Response data
            response_data = {
                "id": profile.id,
                "username": profile.username,
                "pronouns": profile.pronouns,
                "job_title": profile.job_title,
                "social": profile.social,
                "bio": profile.bio,
                "phone_number": profile.phone_number,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "avatar_url": user.avatar_url
                }
            }
            
            return response_data
        
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=409, detail="Email address already in use")
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))

    
    
    def fetch_by_user_id(
    self, 
    db: Session, 
    user_id: str
    ):
        '''Fetches a profile by user_id, returns user information if profile is missing'''
        try:
            # Fetch the profile and user
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # If profile is missing, create a placeholder
            if not profile:
                profile = Profile(
                    id=None, 
                    user_id=user_id, 
                    username=None, 
                    pronouns=None, 
                    job_title=None,
                    social=None, 
                    bio=None, 
                    phone_number=None, 
                    created_at=datetime.utcnow(), 
                    updated_at=datetime.utcnow()
                    )

            response_data = {
                "id": profile.id,
                "username": profile.username,
                "pronouns": profile.pronouns,
                "job_title": profile.job_title,
                "social": profile.social,
                "bio": profile.bio,
                "phone_number": profile.phone_number,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "avatar_url": user.avatar_url,
                    "is_active": user.is_active
                }
            }

            return response_data
        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))
          



    def fetch_all(
        self, db: Session, 
        **query_params: Optional[Any]
    ):
        '''Fetch all Profiles with optional search parameters'''
        
        try:

            query = db.query(Profile)

            # Enable filter by query parameters
            if query_params:
                for column, value in query_params.items():
                    if hasattr(Profile, column) and value:
                        query = query.filter(getattr(Profile, column).ilike(f'%{value}%'))

            return query.all()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))
        
        
        

    def fetch(
        self, db: Session, 
        id: str
    ):
        '''Fetches a profile by its id'''
        try:
            profile = check_model_existence(db, Profile, id)
            return profile
        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))



    def delete(
        self, db: Session, 
        id: str
    ):
        '''Deletes a profile'''
        
        try:

            profile = self.fetch(id=id)
            db.delete(profile)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error: " + str(e))

profile_service = ProfileService()