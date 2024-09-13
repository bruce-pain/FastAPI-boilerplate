from datetime import datetime
from typing import Optional, Union, List
from pydantic import BaseModel


class CreateResource(BaseModel):
    """Schema for creating Resource"""

    title: str
    content: str
    image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class ResourceBase(CreateResource):
    """Base schema for Resource"""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceData(ResourceBase):
    """Data schema for resources"""

    is_deleted: bool
    is_published: bool


class UpdateResource(BaseModel):
    """Schema for updating Resource"""

    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class SuccessResponse(BaseModel):
    message: str
    status_code: int
    status: str = "success"


class AllResourcesResponse(SuccessResponse):
    """
    Schema for all resources
    """

    page: int
    per_page: int
    total_pages: int
    total: int
    data: Union[List[ResourceData], List[None]]

class CreateResourceResponse(SuccessResponse):
    """
    Response schema for successfull creation of resources
    """

    data: ResourceData
