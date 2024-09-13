from typing import Any, Optional, List
from sqlalchemy import desc, or_
from fastapi import status, UploadFile
from uuid_extensions import uuid7
import os
import shutil

from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.utils import mime_types
from api.utils.minio_service import minio_service
from api.v1.models.resource import Resource
from api.v1.schemas.resource import (
    CreateResource,
    UpdateResource,
    AllResourcesResponse,
    ResourceData,
)
from api.utils.db_validators import check_model_existence
from fastapi import HTTPException

UPLOAD_DIR = "media/uploads/resources"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ResourceService(Service):
    """Resource service functionality"""

    def get_image_url(self, image: UploadFile, resource_id: str) -> str:
        """Upload image to minio bucket and return it's URL

        Args:
            image (UploadFile): Image file to upload
            resource_id (str): Resource UUID string

        Raises:
            HTTPException: 400 (Bad Request) - If wrong file format is passed

        Returns:
            str: The live image url for the uploaded image
        """
        extension = image.filename.split(".")[-1]
        mime_map = {
            "jpg": mime_types.IMAGE_JPEG,
            "jpeg": mime_types.IMAGE_JPEG,
            "png": mime_types.IMAGE_PNG,
        }

        if extension not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format, please upload png or jpeg",
            )

        mime = mime_map[extension]

        cleaned_filename = image.filename.replace(" ", "_")

        if not cleaned_filename:
            return None

        filename = f"tmp_{cleaned_filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save the new avatar file to the server
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        minio_save_file = f"resource-{resource_id}-{str(uuid7())}.{extension}"
        minio_response = minio_service.upload_to_minio(
            bucket_name="resources",
            source_file=file_path,
            destination_file=minio_save_file,
            content_type=mime,
        )

        os.remove(file_path)

        image_url = minio_response[0]

        return image_url

    def create(
        self,
        db: Session,
        schema: CreateResource,
        publish: bool,
        image: UploadFile,
        cover_image: UploadFile,
    ) -> Resource:
        """Create a new Resource

        Returns:
            (Resource): Resource object.
        """

        if schema.title.strip() == "" or schema.content.strip() == "":
            raise HTTPException(status_code=400, detail="Invalid request body")

        new_resource = Resource(**schema.model_dump())
        new_resource.is_published = publish
        db.add(new_resource)
        db.commit()
        db.refresh(new_resource)

        if cover_image:
            new_resource.cover_image_url = self.get_image_url(
                image=cover_image, resource_id=new_resource.id
            )
        if image:
            new_resource.image_url = self.get_image_url(
                image=image, resource_id=new_resource.id
            )

        db.commit()
        db.refresh(new_resource)

        return new_resource

    def fetch_all(
        self,
        db: Session,
        page: int,
        per_page: int,
        search: str,
        **query_params: Optional[Any],
    ):
        """
        Fetch all resources
        Args:
            db: database Session object
            page: page number
            per_page: max number of resources in a page
            search: search query
            query_params: params to filter by
        """
        per_page = min(per_page, 10)

        if not isinstance(search, str) and search is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid value for search parameter. Must be a non empty string.",
            )

        # Enable filter by query parameter
        filters = []
        if all(query_params):
            # Validate boolean query parameters
            for param, value in query_params.items():
                if value is not None and not isinstance(value, bool):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid value for '{param}'. Must be a boolean.",
                    )
                if value is None:
                    continue
                if hasattr(Resource, param):
                    filters.append(getattr(Resource, param) == value)

        query = db.query(Resource)

        if search:
            query = self.search_resources(db=db, search_query=search)

        total_resources = query.count()
        if filters:
            query = query.filter(*filters)
            total_resources = query.count()

        total_pages = int(total_resources / per_page) + (total_resources % per_page > 0)

        all_resources: list = (
            query.order_by(desc(Resource.created_at))
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )

        return self.all_resources_response(
            resources=all_resources,
            total_resources=total_resources,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    def fetch_all_public(self, db: Session, page: int, per_page: int):
        """fetch all public resources"""
        per_page = min(per_page, 10)
        query = (
            db.query(Resource)
            .filter(Resource.is_published == True)
            .filter(Resource.is_deleted == False)
        )
        total_resources = query.count()

        total_pages = int(total_resources / per_page) + (total_resources % per_page > 0)

        all_resources: list = (
            query.order_by(desc(Resource.created_at))
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )

        return self.all_resources_response(
            resources=all_resources,
            total_resources=total_resources,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    def all_resources_response(
        self,
        resources: list,
        total_resources: int,
        page: int,
        per_page: int,
        total_pages: int,
    ):
        """
        Generates a response for all resources
        Args:
            resources: a list containing resource objects
            total_resources: total number of resources
        """
        if not resources or len(resources) == 0:
            return AllResourcesResponse(
                message="No Resource(s) for this query",
                status="success",
                status_code=200,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                total=0,
                data=[],
            )
        all_resources = [
            ResourceData.model_validate(usr, from_attributes=True) for usr in resources
        ]
        return AllResourcesResponse(
            message="Resources successfully retrieved",
            status="success",
            status_code=200,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            total=total_resources,
            data=all_resources,
        )

    def fetch(self, db: Session, id):
        """Fetches a resource by their id"""

        resource = check_model_existence(db, Resource, id)

        # return resource if resource is not deleted
        if not resource.is_deleted:
            return resource
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No Such resource exists"
            )

    def get_resource_by_id(self, db: Session, id: str):
        """Fetches a resource by their id"""

        resource = check_model_existence(db, Resource, id)
        return resource

    def update(
        self,
        db: Session,
        resource_id: str,
        schema: UpdateResource,
        image: UploadFile,
        cover_image: UploadFile,
    ) -> Resource | None:
        """Updates an Resource

        Args:
            db (Session): db Session object
            Resource_id (str)
            schema (UpdateResource): Pydantic schema object

        Returns:
            Resource
        """
        resource = self.fetch(db=db, id=resource_id)
        if not resource:
            return None

        # Update the fields with the provided schema data
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resource, key, value)

        if cover_image:
            resource.cover_image_url = self.get_image_url(
                image=cover_image, resource_id=resource_id
            )
        if image:
            resource.image_url = self.get_image_url(
                image=image, resource_id=resource_id
            )

        db.commit()
        db.refresh(resource)
        return resource

    def delete(self, db: Session, Resource_id: str) -> bool:
        """Deletes an Resource

        Args:
            db (Session)
            Resource_id (str)

        Returns:
            bool: True if Resource object is found else False
        """
        resource = self.fetch(db=db, id=Resource_id)

        resource.is_deleted = True
        db.commit()

        return super().delete()

    def publish(self, db: Session, Resource_id: str):
        """Publish a Resource"""

        resource = check_model_existence(db, Resource, id=Resource_id)

        resource.is_published = True
        db.commit()

    def unpublish(self, db: Session, Resource_id: str):
        """Unpublish a Resource"""

        resource = check_model_existence(db, Resource, id=Resource_id)

        resource.is_published = False
        db.commit()

    def search_resources(self, db: Session, search_query: str) -> List[Resource]:
        """Search resources with pagination.

        Args:
            db: Database session object.
            search_query: Search terms provided by the user.
            skip: Number of items to skip (for pagination).
            limit: Number of items to fetch per page (for pagination).

        Returns:
            Paginated search results.
        """

        tokens = search_query.split()

        # Build the query with filters
        query = db.query(Resource).filter(
            or_(
                *[
                    or_(
                        Resource.title.ilike(f"%{token}%"),
                        Resource.content.ilike(f"%{token}%"),
                        Resource.tags.any(token),
                    )
                    for token in tokens
                ]
            )
        )

        return query


resource_service = ResourceService()
