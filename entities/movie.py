from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Movie(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    description: Optional[str] = None
    location: str
    published: bool
    genreId: int
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class MoviesResponse(BaseModel):
    movies: list[Movie]
    total: Optional[int] = None
    page: Optional[int] = None
    pageSize: Optional[int] = None