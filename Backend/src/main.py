from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime

# Import custom modules
from utils import (
    load_course_data, save_schedules, get_subject_name, get_unmet_prerequisites, 
    load_student_data, update_knowledge_profile, save_knowledge_profile,
    get_student_completed_courses, get_student_core_subjects, load_scores, save_scores
)
from burnout_calculator import calculate_burnout, calculate_outcome_alignment_score
from ga_recommender import (
    genetic_algorithm, rerun_genetic_algorithm
)


# Models for request/response data
class Student(BaseModel):
    nuid: str
    completed_courses: List[str] = []
    core_subjects: List[str] = []
    programming_experience: Dict[str, float] = {}
    math_experience: Dict[str, float] = {}

class CourseScore(BaseModel):
    subject_id: str
    burnout_score: float
    outcome_alignment: float
    
class BurnoutScores(BaseModel):
    nuid: str
    courses: List[Dict[str, Any]]

class RecommendationRequest(BaseModel):
    nuid: str
    semesters: int = 2
    courses_per_semester: int = 2
    blacklist: List[str] = []

class CourseDetail(BaseModel):
    subject_id: str
    subject_name: str
    burnout: float
    fitness_score: float

class SemesterSchedule(BaseModel):
    semester: int
    courses: List[CourseDetail]

class Schedule(BaseModel):
    nuid: str
    schedule: List[SemesterSchedule]
    total_burnout: float
    updated: datetime = Field(default_factory=datetime.now)

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Course Recommendation System API",
        "version": "1.0.0",
        "endpoints": {
            "GET /students/{nuid}": "Get student data by NUID",
            "GET /courses": "Get all courses",
            "GET /courses/{subject_id}": "Get course details by subject ID",
            "GET /burnout/{nuid}/{subject_id}": "Calculate burnout score for a student and course",
            "POST /recommendations": "Generate course recommendations",
            "GET /schedule/{nuid}": "Get saved schedule for a student",
            "PUT /knowledge-profile/{nuid}": "Update student knowledge profile",
            "POST /burnout-scores": "Save burnout scores"
        }
    }

@app.get("/students/{nuid}")
def get_student(nuid: str):
    """Get student data by NUID"""
    try:
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        # Convert DataFrame to dict for the first row
        student_dict = student_data.iloc[0].to_dict()
        
        # Get scores if available
        scores_df = load_scores(nuid)
        if scores_df is not None:
            student_dict["scores"] = scores_df.to_dict(orient="records")
        
        return student_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving student data: {str(e)}")

@app.get("/courses")
def get_courses():
    """Get all courses"""
    try:
        courses_df = load_course_data()
        return courses_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving courses: {str(e)}")

@app.get("/courses/{subject_id}")
def get_course(subject_id: str):
    """Get course details by subject ID"""
    try:
        courses_df = load_course_data()
        course = courses_df[courses_df['subject_id'] == subject_id]
        
        if course.empty:
            raise HTTPException(status_code=404, detail=f"Course {subject_id} not found")
        
        return course.iloc[0].to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving course: {str(e)}")

@app.get("/burnout/{nuid}/{subject_id}")
def calculate_course_burnout(nuid: str, subject_id: str):
    """Calculate burnout score for a student and course"""
    try:
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        courses_df = load_course_data()
        if subject_id not in courses_df['subject_id'].values:
            raise HTTPException(status_code=404, detail=f"Course {subject_id} not found")
        
        burnout = calculate_burnout(student_data, subject_id, courses_df)
        outcome_alignment = calculate_outcome_alignment_score(student_data, subject_id, courses_df)
        
        completed_courses = get_student_completed_courses(student_data)
        prereqs = get_unmet_prerequisites(courses_df, subject_id, set(completed_courses))
        
        return {
            "nuid": nuid,
            "subject_id": subject_id,
            "subject_name": get_subject_name(courses_df, subject_id),
            "burnout": burnout,
            "outcome_alignment": outcome_alignment,
            "unmet_prerequisites": list(prereqs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating burnout: {str(e)}")

@app.post("/recommendations", response_model=Schedule)
def generate_recommendations(request: RecommendationRequest):
    """Generate course recommendations for a student"""
    try:
        nuid = request.nuid
        semesters = request.semesters
        courses_per_semester = request.courses_per_semester
        blacklist = set(request.blacklist)
        
        # Load student data
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        # Get completed courses and core subjects
        completed_courses = set(get_student_completed_courses(student_data))
        core_subjects = get_student_core_subjects(student_data)
        core_remaining = [c for c in core_subjects if c not in completed_courses]
        
        # Load all available subjects
        subjects_df = load_course_data()
        all_subjects = subjects_df['subject_id'].tolist()
        
        # Get available subjects that aren't blacklisted or already completed
        available_subjects = [s for s in all_subjects if s not in blacklist and s not in completed_courses]
        
        final_list = []
        plan = [[] for _ in range(semesters)]
        taken = completed_courses.copy()
        
        # Generate recommendations for each semester
        for sem_idx in range(semesters):
            # Get available subjects that aren't blacklisted or already selected
            current_available = [s for s in available_subjects if s not in final_list]
            
            # Check if we have enough subjects to continue
            if len(current_available) < courses_per_semester:
                break
            
            # Run GA to get the best schedule for this semester
            best_semester = genetic_algorithm(current_available, taken, student_data, core_remaining)
            
            # Update the plan
            plan[sem_idx] = best_semester
            
            # Accept this semester
            final_list.extend(best_semester)
            taken.update(best_semester)
            core_remaining = [c for c in core_remaining if c not in best_semester]
        
        # Optimize the schedule
        best_plan, total_burnout = rerun_genetic_algorithm(
            final_list, 
            student_data, 
            completed_courses
        )
        
        # Prepare response
        schedule_data = []
        current_taken = completed_courses.copy()
        
        for i, semester in enumerate(best_plan, 1):
            if semester:
                semester_courses = []
                for subject_id in semester:
                    # Calculate burnout
                    burnout = calculate_burnout(student_data, subject_id, subjects_df)
                    
                    # Get subject details
                    name = get_subject_name(subjects_df, subject_id)
                    
                    # Add to semester courses
                    semester_courses.append({
                        "subject_id": subject_id,
                        "subject_name": name,
                        "burnout": round(burnout, 3),
                        "fitness_score": -total_burnout
                    })
                    
                    # Update for next subject
                    current_taken.add(subject_id)
                
                # Add semester to schedule
                schedule_data.append({
                    "semester": i,
                    "courses": semester_courses
                })
        
        # Save schedule to database
        save_schedules(nuid, schedule_data)
        
        # Update knowledge profile
        programming_skills, math_skills = update_knowledge_profile(student_data, taken)
        save_knowledge_profile(nuid, programming_skills, math_skills)
        
        return {
            "nuid": nuid,
            "schedule": schedule_data,
            "total_burnout": total_burnout,
            "updated": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/schedule/{nuid}")
def get_schedule(nuid: str):
    """Get saved schedule for a student"""
    try:
        # Connect to MongoDB and get the schedule
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        schedule_collection = db["user_schedules"]
        
        schedule = schedule_collection.find_one({"NUID": nuid})
        
        if schedule is None:
            raise HTTPException(status_code=404, detail=f"No schedule found for student {nuid}")
        
        # Convert MongoDB document to response format
        schedule["_id"] = str(schedule["_id"])  # Convert ObjectId to string
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schedule: {str(e)}")

@app.put("/knowledge-profile/{nuid}")
def update_student_knowledge(nuid: str, programming_skills: Dict[str, float] = Body(...), math_skills: Dict[str, float] = Body(...)):
    """Update student knowledge profile"""
    try:
        save_knowledge_profile(nuid, programming_skills, math_skills)
        return {"message": f"Knowledge profile updated for student {nuid}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating knowledge profile: {str(e)}")

@app.post("/burnout-scores")
def save_burnout_scores(scores: BurnoutScores):
    """Save burnout scores for a student"""
    try:
        save_scores(scores.nuid, scores.courses)
        return {"message": f"Burnout scores saved for student {scores.nuid}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving burnout scores: {str(e)}")

@app.get("/prerequisites/{subject_id}")
def get_prerequisites(subject_id: str):
    """Get prerequisites for a course"""
    try:
        courses_df = load_course_data()
        if subject_id not in courses_df['subject_id'].values:
            raise HTTPException(status_code=404, detail=f"Course {subject_id} not found")
        
        from utils import get_subject_prerequisites
        
        prereqs = get_subject_prerequisites(courses_df, subject_id)
        return {
            "subject_id": subject_id,
            "subject_name": get_subject_name(courses_df, subject_id),
            "prerequisites": prereqs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prerequisites: {str(e)}")

@app.get("/learning-outcomes/{subject_id}")
def get_learning_outcomes(subject_id: str):
    """Get learning outcomes for a course"""
    try:
        courses_df = load_course_data()
        if subject_id not in courses_df['subject_id'].values:
            raise HTTPException(status_code=404, detail=f"Course {subject_id} not found")
        
        from utils import get_subject_outcomes
        
        outcomes = get_subject_outcomes(courses_df, subject_id)
        return {
            "subject_id": subject_id,
            "subject_name": get_subject_name(courses_df, subject_id),
            "learning_outcomes": list(outcomes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving learning outcomes: {str(e)}")

@app.post("/update-taken-courses/{nuid}")
def update_taken_courses(nuid: str, courses: List[str] = Body(...)):
    """Update courses taken by a student"""
    try:
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        # Connect to MongoDB and update courses
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        users_collection = db["users"]
        
        result = users_collection.update_one(
            {"NUID": nuid},
            {"$set": {"completed_courses": courses}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        # Update knowledge profile
        programming_skills, math_skills = update_knowledge_profile(student_data, set(courses))
        save_knowledge_profile(nuid, programming_skills, math_skills)
        
        return {"message": f"Courses updated for student {nuid}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating courses: {str(e)}")
