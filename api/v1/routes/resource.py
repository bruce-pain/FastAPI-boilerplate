from fastapi import APIRouter, Depends, status, Query, Form, File, UploadFile
from fastapi.encoders import jsonable_encoder
from typing import Annotated, Optional
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.pagination import paginated_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.resource import resource_service
from api.v1.schemas.resource import (
    CreateResource,
    ResourceBase,
    AllResourcesResponse,
    UpdateResource,
    CreateResourceResponse,
    SuccessResponse,
)
import logging
import json


resource = APIRouter(prefix="/resources", tags=["Resources"])


@resource.post(
    "",
    response_model=CreateResourceResponse,
    status_code=201,
    summary="Create new Resource",
    description="Admin endpoint to create a resource",
)
async def create_resource(
    # schema: CreateResource,
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    tags: Optional[str] = Form(None),
    cover_image: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    publish: bool = Query(True),
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to create a new Resource. Only accessible to superadmins

    Args:
        schema (CreateResource): Request Body for creating resource
        publish (bool): query parameter to decide whether or not to publish after creating
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_admin (User, optional): Admin User. Defaults to Depends(user_service.get_current_super_admin).

    Returns:
        success_response
    """

    schema = CreateResource(title=title, content=content)

    if tags:
        schema.tags = json.loads(tags)

    resource = resource_service.create(
        db, schema=schema, publish=publish, cover_image=cover_image, image=image
    )

    logging.info(f"Creating new Resource. ID: {resource.id}.")
    return success_response(
        data=jsonable_encoder(ResourceBase.model_validate(resource)),
        message="Successfully created Resource",
        status_code=status.HTTP_201_CREATED,
    )


@resource.get("", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse)
async def get_resources(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    is_deleted: Optional[bool] = Query(None),
):
    """
    Retrieves all resources.
    Args:
        current_user: The current user(admin) making the request
        db: database Session object
        page: the page number
        per_page: the maximum size of resources for each page
        is_published: boolean to filter published resources
        is_deleted: boolean to filter deleted resources
    Returns:
        ResourceData
    """
    query_params = {
        "is_published": is_published,
        "is_deleted": is_deleted,
    }
    return resource_service.fetch_all(db, page, per_page, search, **query_params)


@resource.get(
    "/public", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse
)
async def get_public_resources(
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = Query(None),
):
    """
    Retrieves all public resources.
    Args:
        db: database Session object
        page: the page number
        per_page: the maximum size of resources for each page
    Returns:
        ResourceData
    """

    return resource_service.fetch_all(
        db=db,
        page=page,
        per_page=per_page,
        search=search,
        is_published=True,
        is_deleted=False,
    )


@resource.patch(
    "/{resource_id}", response_model=success_response, status_code=status.HTTP_200_OK
)
async def update_resources(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    resource_id: str,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    cover_image: Optional[UploadFile] = File(None),
):
    """
    Route to Update resources

    Args:
        schema (UpdateResource): Schema for the resource model
        resource_id (str): id for the resource about to be updated
        db (Annotated[Session, Depends): database dependency
        current_user: dependency to verify whether the supposed user is an admin. Defaults to Annotated[User, Depends(user_service.get_current_super_admin)].

    Returns:
        dict: {"status":200,
               "message":Resource Updated Successfully,
               "data" : {}
               }
    """

    schema = UpdateResource()

    if title:
        schema.title = title
    if content:
        schema.content = content
    if tags:
        schema.tags = json.loads(tags)

    resource = resource_service.update(
        db=db,
        resource_id=resource_id,
        schema=schema,
        cover_image=cover_image,
        image=image,
    )
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Resource updated Succesfully",
        data=jsonable_encoder(ResourceBase.model_validate(resource)),
    )


@resource.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resources(
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    """
    Route to soft  delete Resources

    Args:
        resource_id (str): used as an identifier for the resource
        db (Annotated[Session, Depends): database dependency
        current_user (Annotated[User, Depends): Admin User dependency
    """
    return resource_service.delete(db=db, Resource_id=resource_id)


@resource.get(
    "/{resource_id}", status_code=status.HTTP_200_OK, response_model=success_response
)
async def get_resource_by_id(resource_id: str, db: Annotated[Session, Depends(get_db)]):
    """
    Route to get resource by its id

    Args:
        resource_id (str):the identifier of the resource to query
        db (Annotated[Session, Depends): database dependency
    """

    resource = resource_service.fetch(db=db, id=resource_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Resource fetched successfully",
        data=jsonable_encoder(resource),
    )


@resource.put(
    "/{resource_id}/publish",
    status_code=status.HTTP_200_OK,
    summary="Publish a resource",
    response_model=SuccessResponse,
)
async def publish_resource(
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    resource_service.publish(db=db, Resource_id=resource_id)

    return success_response(
        status_code=status.HTTP_200_OK, message="Resource successfully published!"
    )


@resource.put(
    "/{resource_id}/unpublish",
    status_code=status.HTTP_200_OK,
    summary="Unpublish a resource",
    response_model=SuccessResponse,
)
async def unpublish_resource(
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    resource_service.unpublish(db=db, Resource_id=resource_id)

    return success_response(
        status_code=status.HTTP_200_OK, message="Resource successfully unpublished!"
    )
