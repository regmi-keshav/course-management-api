from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Chapter(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)
    positive_ratings: int = Field(0)
    negative_ratings: int = Field(0)


class Course(BaseModel):
    name: str
    date: datetime
    description: str
    domain: List[str]
    chapters: List[Chapter]
    ratings: Optional[dict] = Field(default_factory=lambda: {
                                    "positive": 0, "negative": 0})


class CourseResponse(Course):
    id: str


class RateChapterRequest(BaseModel):
    chapter_index: Optional[int] = None
    chapter_name: Optional[str] = None
    rating: bool
