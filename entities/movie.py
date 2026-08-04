from pydantic import BaseModel, Field


class Genre(BaseModel):
    name: str = Field(..., min_length=1)


class Movie(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    price: int = Field(..., ge=0)
    description: str = Field(..., min_length=1)
    imageUrl: str | None = None
    location: str
    published: bool
    rating: float = Field(..., ge=0)
    genreId: int
    createdAt: str
    updatedAt: str | None = None
    genre: Genre


class MoviesResponse(BaseModel):
    movies: list[Movie]
    count: int
    page: int
    pageSize: int
    pageCount: int