from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel
import json
import pandas as pd

from src.burnout_calculator import calculate_scores
from src.ga_recommender import generate_recommendations, save_schedule
from src.utils import load_subject_data, load_burnout_scores
from src.student_input import get_student_input

app = FastAPI(
    title="Course Recommendation System API",
    description="Backend API for AI-Based Subject Recommendation System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class StudentInput(BaseModel):
    nuid: str
    programming_experience: Dict[str, int]
    math_experience: Dict[str, int]
    completed_courses: Dict[str, Dict]
    core_subjects: str
    desired_outcomes: str

class RecommendationRequest(BaseModel):
    nuid: str
    semester: int
    additional_interests: Optional[List[str]] = []

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to Course Recommendation System API"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

@app.post("/api/student")
async def create_student(student_data: StudentInput):
    try:
        # Save student data to CSV
        df = pd.DataFrame([{
            "NUid": student_data.nuid,
            "programming_experience": json.dumps(student_data.programming_experience),
            "math_experience": json.dumps(student_data.math_experience),
            "completed_courses": ",".join(student_data.completed_courses.keys()),
            "core_subjects": student_data.core_subjects,
            "desired_outcomes": student_data.desired_outcomes,
            "completed_courses_details": json.dumps(student_data.completed_courses)
        }])
        df.to_csv(f"data/students/student_{student_data.nuid}.csv", index=False)
        return {"message": "Student data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/subjects")
async def get_subjects():
    try:
        subjects_df, outcomes_df, prereqs_df, coreqs_df, requirements_df = load_subject_data()
        return {
            "subjects": subjects_df.to_dict(orient='records'),
            "outcomes": outcomes_df.to_dict(orient='records'),
            "prerequisites": prereqs_df.to_dict(orient='records'),
            "corequisites": coreqs_df.to_dict(orient='records'),
            "requirements": requirements_df.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/burnout-scores")
async def get_burnout_scores(nuid: str):
    try:
        result = calculate_scores(nuid)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No data found for student {nuid}")
        
        scores = result.to_dict(orient='records')
        return {
            "nuid": nuid,
            "scores": scores,
            "top_scores": scores[:5] if len(scores) >= 5 else scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    try:
        recommended_courses, highly_competitive_courses = generate_recommendations(
            request.nuid,
            request.semester,
            request.additional_interests
        )
        
        if recommended_courses is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate recommendations for student {request.nuid}"
            )
        
        return {
            "nuid": request.nuid,
            "semester": request.semester,
            "recommended_courses": recommended_courses,
            "highly_competitive_courses": highly_competitive_courses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 