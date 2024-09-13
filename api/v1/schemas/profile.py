from pydantic import BaseModel, Field, EmailStr, validator
from fastapi import UploadFile
from typing import Optional
import re
from datetime import datetime
from api.v1.schemas.user import UserBase


class ProfileBase(BaseModel):
    '''Base profile schema'''
    id: str
    created_at: datetime
    user: UserBase
    username: Optional[str] = Field(None, max_length=50)  
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    
    class Config:
        extra = 'allow'

class UserData(BaseModel):
    id: str
    email: str
    avatar_url: str

class ProfileData(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    username: str
    pronouns: str
    job_title: str
    social: str
    bio: str
    phone_number: str
    user: UserData

class CurrentProfileResponse(BaseModel):
    status: str = "success"
    message: str
    data: ProfileData
    status_code: int = 200


class ProfileCreateUpdate(BaseModel):
    '''Schema to create or update a profile'''
    username: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    social: Optional[str] = None
    bio: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    avatar: Optional[UploadFile] = None
    
    
    @validator('phone_number', always=True)
    def phone_number_validator(cls, value):
        if value is None:
            return value
        
        if not isinstance(value, str):
            raise ValueError("Phone number must be a string.")
        
        if not re.fullmatch(r"^\+?[0-9]+$", value):
            raise ValueError("Phone number must contain only digits and may start with '+'.")
        
        number_length = len(re.sub(r"\D", "", value))  
        if number_length < 10 or number_length > 15:
            raise ValueError("Phone number must be between 10 and 15 digits long.")

        return value        

    @validator('job_title', pre=True, always=True)
    def job_title_validator(cls, value):
        if value is None:
            return value 
        
        if not isinstance(value, str):
            raise ValueError("Job title must be a string.")
        
        if not value.replace(" ", "").isalpha():
            raise ValueError("Job title must contain only alphabetic characters.")
        
        return value        
    
    class Config:
        extra = 'allow'

