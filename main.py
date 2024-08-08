from fastapi import FastAPI
from app.routes import router as courses_router

app = FastAPI()

app.include_router(courses_router, prefix="/api", tags=["courses"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Courses API"}
