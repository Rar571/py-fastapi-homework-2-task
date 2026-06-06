from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from database.models import MovieStatusEnum
from dateutil.relativedelta import relativedelta

from typing import Optional


class Movie(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieRead(BaseModel):
    movies: list[Movie]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class Country(BaseModel):
    id: int
    code: str
    name: str | None


class Genre(BaseModel):
    id: int
    name: str


class Actor(BaseModel):
    id: int
    name: str


class Language(BaseModel):
    id: int
    name: str


class MovieCreate(BaseModel):
    name: str = Field(max_length=255)
    date: date

    @field_validator("date")
    @staticmethod
    def check_date(date1):
        max_date = date.today() + relativedelta(years=1)
        if date1 > max_date:
            raise ValueError("Date year can not be more than one year in the future")
        return date1

    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetail(Movie):
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: Country
    genres: list[Genre]
    actors: list[Actor]
    languages: list[Language]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    score: Optional[float] = None

    @field_validator("score")
    @staticmethod
    def check_score(score_value: Optional[float]):
        if score_value is not None and (score_value < 0 or score_value > 100):
            raise ValueError("Invalid input data.")
        return score_value

    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None

    @model_validator(mode="after")
    def check_is_negative(self):
        if self.budget is not None and self.budget < 0:
            raise ValueError("Invalid input data.")
        if self.revenue is not None and self.revenue < 0:
            raise ValueError("Invalid input data.")
        return self
