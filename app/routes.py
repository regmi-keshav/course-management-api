from fastapi import APIRouter, HTTPException, Query, Body, Path
from typing import List, Optional
from bson import ObjectId
from .db import courses_collection
from .models import Course, CourseResponse, Chapter, RateChapterRequest

router = APIRouter()


@router.get("/courses", response_model=List[CourseResponse])
async def get_courses(
    sort_by: str = Query("alphabetical", enum=[
                         "alphabetical", "date", "rating"]),
    domain: Optional[str] = None
):
    query = {}
    if domain:
        query["domain"] = domain

    sort_criteria = {
        "alphabetical": ("name", 1),
        "date": ("date", -1),
        "rating": ("ratings.average_rating", -1)
    }
    sort_field, order = sort_criteria[sort_by]

    courses = await courses_collection.find(query).sort(sort_field, order).to_list(100)
    return [{"id": str(course["_id"]), **course} for course in courses]


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course_overview(course_id: str = Path(..., min_length=24, max_length=24)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"id": str(course["_id"]), **course}


@router.get("/courses/{course_id}/chapters/{chapter_identifier}", response_model=Chapter)
async def get_chapter_info(
    course_id: str = Path(..., min_length=24, max_length=24),
    chapter_identifier: str = Path(...)
):
    # Fetch the course from the database
    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if the chapter_identifier is an index or name
    chapter = None
    if chapter_identifier.isdigit():
        chapter_index = int(chapter_identifier)
        if 0 <= chapter_index < len(course["chapters"]):
            chapter = course["chapters"][chapter_index]
    else:
        chapter = next(
            (ch for ch in course["chapters"] if ch["name"] == chapter_identifier), None)

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return chapter


@router.post("/courses/{course_id}/rate-chapter")
async def rate_chapter(
    course_id: str = Path(..., min_length=24, max_length=24),
    body: RateChapterRequest = Body(...)
):
    if body.chapter_name is None and body.chapter_index is None:
        raise HTTPException(
            status_code=400, detail="Either chapter_name or chapter_index must be provided")

    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    chapter = None
    if body.chapter_name:
        chapter = next(
            (ch for ch in course["chapters"] if ch["name"] == body.chapter_name), None)
    elif body.chapter_index is not None:
        if 0 <= body.chapter_index < len(course["chapters"]):
            chapter = course["chapters"][body.chapter_index]

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if body.rating:
        update = {"$inc": {"ratings.positive": 1}}
    else:
        update = {"$inc": {"ratings.negative": 1}}

    await courses_collection.update_one({"_id": ObjectId(course_id)}, update)

    return {"msg": "Rating updated successfully"}


@router.get("/courses/{course_id}/ratings")
async def get_course_ratings(
    course_id: str = Path(..., min_length=24, max_length=24)
):
    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    positive_ratings = course.get('ratings', {}).get('positive', 0)
    negative_ratings = course.get('ratings', {}).get('negative', 0)

    total_ratings = positive_ratings + negative_ratings

    return {
        "course_id": course_id,
        "ratings": {
            "positive": positive_ratings,
            "negative": negative_ratings,
            "total": total_ratings
        }
    }


@router.post("/courses", response_model=CourseResponse)
async def add_course(course: Course):
    existing_course = await courses_collection.find_one({"name": course.name})
    if existing_course:
        raise HTTPException(
            status_code=400, detail="Course with this name already exists")

    result = await courses_collection.insert_one(course.dict())
    new_course = await courses_collection.find_one({"_id": result.inserted_id})

    if new_course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"id": str(new_course["_id"]), **new_course}
