from datetime import date, datetime
from typing import Optional, List, Literal
from pydantic import UUID4
from pydantic import BaseModel, Field, field_validator
from fastapi import Query

from database.models.movies import MovieStatusEnum
from schemas.examples.movies import (
    country_schema_example,
    language_schema_example,
    genre_schema_example,
    actor_schema_example,
    movie_item_schema_example,
    movie_list_response_schema_example,
    movie_create_schema_example,
    movie_detail_schema_example,
    movie_update_schema_example, director_schema_example
)


class LanguageSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                language_schema_example
            ]
        }
    }


class CountrySchema(BaseModel):
    id: int
    code: str
    name: Optional[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                country_schema_example
            ]
        }
    }


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                genre_schema_example
            ]
        }
    }


class ActorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                actor_schema_example
            ]
        }
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                director_schema_example
            ]
        }
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieBaseSchema(BaseModel):
    # uuid: int = Field(..., ge=0)
    name: str = Field(..., max_length=255)
    year: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    time: int = Field(..., ge=0)
    imdb: float = Field(..., ge=0)
    votes: int = Field(..., ge=0)
    meta_score: float = Field(..., ge=0)
    gross: float = Field(..., ge=0)
    certification: str
    model_config = {
        "from_attributes": True
    }

    @field_validator("year")
    @classmethod
    def validate_date(cls, value):
        current_year = datetime.now().year
        if value.year > current_year + 1:
            raise ValueError(f"The year in 'date' cannot be greater than {current_year + 1}.")
        return value


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: UUID4
    certification: CertificationSchema
    country: CountrySchema
    genres: List[GenreSchema]
    actors: List[ActorSchema]
    languages: List[LanguageSchema]
    directors: List[DirectorSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_detail_schema_example
            ]
        }
    }


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    year: date
    time: int
    imdb: float
    languages: List[LanguageSchema]
    directors: List[DirectorSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_item_schema_example
            ]
        }
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_list_response_schema_example
            ]
        }
    }


class MovieCreateSchema(MovieBaseSchema):
    directors: List[str]
    country: str
    genres: List[str]
    actors: List[str]
    languages: List[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_create_schema_example
            ]
        }
    }

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.upper()

    @field_validator("genres", "actors", "languages", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: List[str]) -> List[str]:
        return [item.title() for item in value]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = Field(None, ge=0)
    gross: Optional[float] = Field(None, ge=0)

    # genre_ids: Optional[List[int]] = None
    # languages: Optional[List[LanguageSchema]] = None
    # directors: Optional[List[DirectorSchema]] = None
    # certification: Optional[CertificationSchema] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                movie_update_schema_example
            ]
        }
    }


class MovieLikeSchema(BaseModel):
    movie_id: int
    is_like: bool

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str
    movie_id: int


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    movie_id: int

    class Config:
        from_attributes = True


class MovieFilter:
    def __init__(
        self,
        year: Optional[int] = Query(None),
        imdb_min: Optional[float] = Query(None),
        imdb_max: Optional[float] = Query(None),
        genre_id: Optional[int] = Query(None),
        name: Optional[str] = Query(None),
    ):
        self.year = year
        self.imdb_min = imdb_min
        self.imdb_max = imdb_max
        self.genre_id = genre_id
        self.name = name


class MovieSortParams:
    def __init__(
        self,
        sort_by: Optional[Literal["year", "imdb", "votes", "price"]] = Query("year"),
        order: Optional[Literal["asc", "desc"]] = Query("asc"),
    ):
        self.sort_by = sort_by
        self.order = order


class MovieSearch:
    def __init__(
        self,
        genres: Optional[List[str]] = Query(None),
        actors: Optional[List[str]] = Query(None),
        directors: Optional[List[str]] = Query(None),
        overview: Optional[str] = Query(None),
    ):
        self.genres = genres
        self.actors = actors
        self.directors = directors
        self.overview = overview


class FavoriteMovieCreate(BaseModel):
    movie_id: int


class FavoriteMovieOut(BaseModel):
    id: int
    name: str
    year: date
    imdb: float

    class Config:
        from_attributes = True


class GenreWithCountOut(BaseModel):
    id: int
    name: str
    movie_count: int
