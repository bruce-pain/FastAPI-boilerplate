from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Query, Session

from app.core.base.model import BaseTableModel
from app.core.base.schema import PaginatedResponse

T = TypeVar("T", bound=BaseTableModel)


class BaseRepository(Generic[T]):
    """
    Base repository class for CRUD operations.
    This class provides a generic interface for performing CRUD operations on SQLAlchemy models.
    It is designed to be inherited by specific repository classes for different models.
    Attributes:
        model (Type[Model]): The SQLAlchemy model class.
        db (Session): The SQLAlchemy session.
    """

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def create(self, obj: T) -> T:
        """Create a new object of the model.
        Args:
            obj (Model): The object to be created.
        Returns:
            Model: The created object.
        """

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, id: str) -> Optional[T]:
        """Get an object of the model by id.
        Args:
            id (str): The id of the object.
        Returns:
            Optional[Model]: The object if found, None otherwise.
        """

        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self) -> List[T]:
        """Get all objects of the model.

        This method retrieves all records from the database for the current model.

        Returns:
            List[Model]: A list containing all objects of the model in the database.
        """

        return self.db.query(self.model).all()

    def update(self, obj: T) -> Optional[T]:
        """Update an existing object of the model.

        This method updates an existing record in the database with the provided object's data.
        It first checks if the object exists, then updates all attributes based on the provided object.

        Args:
            obj (Model): The object containing updated data.

        Returns:
            Model: The updated object if successful, None if the object wasn't found.
        """

        existing_obj = self.get(obj.id)
        if existing_obj:
            for key, value in obj.__dict__.items():
                setattr(existing_obj, key, value)
            self.db.commit()
            self.db.refresh(existing_obj)
            return existing_obj
        return None

    def delete(self, id: str) -> bool:
        """Delete an object of the model by id.

        This method removes a record from the database based on the provided id.

        Args:
            id (str): The id of the object to delete.

        Returns:
            bool: True if the object was successfully deleted, False if the object wasn't found.
        """

        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

    def base_query(self) -> Query[T]:
        """Get the base query for the model.

        This method returns a SQLAlchemy Query object for the current model, which can be further customized or filtered as needed.

        Returns:
            Query[Model]: A SQLAlchemy Query object for the model.
        """

        return self.db.query(self.model)

    def paginate(self, query: Query[T], page: int, page_size: int) -> PaginatedResponse:
        """Paginate the results of a query.

        Args:
            query (Query[T]): The SQLAlchemy query object to paginate.
            page (int): The page number to retrieve.
            page_size (int): The number of items per page.

        Returns:
            PaginatedResponse: A PaginatedResponse object containing pagination information and the list of items for the requested page.
        """

        # get total pages
        total_pages = (query.count() + page_size - 1) // page_size

        # return a dict with pagination info
        if page > total_pages and total_pages != 0:
            page = total_pages

        return PaginatedResponse(
            total_items=query.count(),
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            items=query.offset((page - 1) * page_size).limit(page_size).all(),
        )
