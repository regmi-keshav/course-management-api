import json
from pymongo import MongoClient, ASCENDING, DESCENDING


def initialize_db():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["course_db"]
    collection = db["courses"]

    # Create indices for sorting
    collection.create_index([("name", ASCENDING)])
    collection.create_index([("date", DESCENDING)])
    collection.create_index([("ratings.average_rating", DESCENDING)])
    collection.create_index([("domain", ASCENDING)])

    # Load courses.json
    with open("courses.json", "r") as f:
        courses = json.load(f)

    # Insert data into the collection
    collection.insert_many(courses)
    print("Database initialized and courses added.")


if __name__ == "__main__":
    initialize_db()
