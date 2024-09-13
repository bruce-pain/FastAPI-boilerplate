from fastapi import Depends, APIRouter, status, Form
from sqlalchemy.orm import Session
import os
import shutil
from typing import Optional, Dict
from api.utils.minio_service import minio_service
from uuid import uuid4
from api.v1.models.user import User
from api.v1.schemas.profile import ProfileBase, ProfileCreateUpdate, CurrentProfileResponse
from api.db.database import get_db
from api.v1.services.user import user_service
from api.v1.services.profile import profile_service
from fastapi import UploadFile, File
from api.utils.success_response import success_response
import tempfile



profile = APIRouter(prefix='/profile', tags=['Profiles'])


UPLOAD_DIR = "media/uploads/user_avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)



@profile.get("/me", response_model=CurrentProfileResponse)
def get_current_user_profile(
    db: Session = Depends(get_db), 
    current_user: User = Depends(user_service.get_current_user)
    ):
    """
    Get the profile of the currently authenticated user
    """
    profile = profile_service.fetch_by_user_id(db, user_id=current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Profile retrieved Successfully!!!",
        data=profile
    )



@profile.put('', status_code=status.HTTP_200_OK, response_model=ProfileBase)
def update_user_profile(
    username: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    pronouns: Optional[str] = Form(None),
    social: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),    
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    '''Endpoint to update user profile'''
    
    # Construct the schema manually using the validated data
    schema = ProfileCreateUpdate(
        username=username,
        job_title=job_title,
        pronouns=pronouns,
        social=social,
        phone_number=phone_number,
        email=email,
        bio=bio,
    )
    
    
    if avatar:
        # Replace spaces in the filename with underscores or hyphens
        cleaned_filename = avatar.filename.replace(" ", "_")
        
        # Check if the cleaned filename is not empty or None
        if cleaned_filename:
            # Upload the avatar to Minio
            minio_save_file = f"avatar-{str(uuid4())}.{avatar.filename.split('.')[-1]}"
            minio_bucket_name = 'user-avatars'
            minio_content_type = avatar.content_type

            # Create a temporary file to save the avatar
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                shutil.copyfileobj(avatar.file, temp_file)
                temp_file_path = temp_file.name

            save_url, download_url = minio_service.upload_to_minio(
                bucket_name=minio_bucket_name,
                source_file=temp_file_path,
                destination_file=minio_save_file,
                content_type=minio_content_type
            )
            
            # Clean up the temporary file after uploading
            os.remove(temp_file_path)

            # Update the user's avatar URL
            current_user.avatar_url = save_url
        else:
            pass
    else:
        pass

    # Update the user profile and related user data
    updated_profile = profile_service.update(db, schema=schema, user_id=current_user.id)
    
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User Profile Updated Successfully!!!",
        data=updated_profile
    )
