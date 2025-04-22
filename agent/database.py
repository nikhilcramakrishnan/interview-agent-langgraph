from typing import List, Dict, Any, Optional
from .config import db

def fetch_questions_from_db(job_role: str) -> List[Dict[str, Any]]:
    print(f"-> DB: Fetching questions for {job_role} from MongoDB (using _id)")

    if db is None:
        print("MongoDB client is not available. Cannot fetch questions.")
        return []

    questions_collection = db.questions

    questions_list_formatted = []
    try:

        questions_cursor = questions_collection.find(
            {"job_role": job_role},
            {"_id": 1, "text": 1, "topic": 1, "difficulty": 1}
        )

        for doc in questions_cursor:
            formatted_question = {
                "id": str(doc["_id"]),
                "text": doc.get("text"),
                "topic": doc.get("topic"),
                "difficulty": doc.get("difficulty"),
            }
            questions_list_formatted.append(formatted_question)


        print(f"Found and formatted {len(questions_list_formatted)} questions in DB for role '{job_role}'.")
        return questions_list_formatted

    except Exception as e:
        print(f"Error fetching questions from MongoDB for role '{job_role}': {e}")
        return []


