from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class APIResponse(BaseModel):
    status: bool
    message: str
    data: Optional[Any] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    status: bool
    message: str
    data: Optional[Any] = None
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20
