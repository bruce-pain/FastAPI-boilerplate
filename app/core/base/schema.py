from pydantic import BaseModel


class BaseResponseModel(BaseModel):
    status_code: int
    message: str


class PaginatedResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    items: list
