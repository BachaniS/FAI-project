from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import numpy as np
from bson import ObjectId
from urllib.parse import unquote
from collections import defaultdict

from utils import (
    load_course_data, save_schedules, get_subject_name, get_unmet_prerequisites, 
    load_student_data, update_knowledge_profile, save_knowledge_profile,
    get_student_completed_courses, get_student_core_subjects, load_scores, save_scores, MONGO_URI
)
from burnout_calculator import calculate_burnout, calculate_outcome_alignment_score
from ga_recommender import (
    genetic_algorithm, rerun_genetic_algorithm
)

from CLI_recommendation_system import (
    load_student_data, load_course_data, get_student_completed_courses,
    get_student_core_subjects, calculate_burnout, calculate_utility,
    calculate_outcome_alignment_score, get_burnout_score, get_utility_score,
    get_student_desired_outcomes, filter_courses_by_interests,
    run_genetic_algorithm_with_animation, convert_ga_schedule_to_recommendations,
    identify_competitive_courses, get_unmet_prerequisites, get_subject_name,
    get_burnout_status, get_difficulty_status, optimize_schedule,
    rerun_genetic_algorithm, save_plan_to_db
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    selected_courses: Optional[List[str]] = None
    blacklisted_courses: Optional[List[str]] = None

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

class UserLoginRequest(BaseModel):
    nuid: str
    name: str

class CompletedCourse(BaseModel):
    subject_code: str
    course_name: str
    weekly_workload: int
    final_grade: str
    experience_rating: int

class UserRegisterRequest(BaseModel):
    nuid: str
    name: str
    interests: List[str]
    programming_experience: Dict[str, float]
    math_experience: Dict[str, float]
    completed_courses: List[CompletedCourse]
    core_subjects: List[str]

class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SaveScheduleRequest(BaseModel):
    name: str
    courses: List[str]

# Add this helper class for handling ObjectId serialization
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Update the SaveScheduleResponse model to handle ObjectId
class SaveScheduleResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

# Add this new model for schedule responses
class ScheduleListResponse(BaseModel):
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

# Add this new model for delete response
class DeleteScheduleResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

def convert_numpy_to_native(obj):
    """Convert NumPy types to native Python types"""
    if isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_native(item) for item in obj]
    return obj

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
            "GET /recommendations/{nuid}": "Get course recommendations using genetic algorithm",
            "GET /schedule/{nuid}": "Get saved schedule for a student",
            "PUT /knowledge-profile/{nuid}": "Update student knowledge profile",
            "POST /burnout-scores": "Save burnout scores",
            "POST /auth/login": "Login user",
            "POST /auth/register": "Register user"
        }
    }

@app.get("/students/{nuid}")
def get_student(nuid: str):
    """Get student data by NUID"""
    try:
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            raise HTTPException(status_code=404, detail=f"Student with NUID {nuid} not found")
        
        student_dict = student_data.iloc[0].to_dict()
        
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

@app.get("/recommendations/{nuid}")
async def get_recommendations(nuid: str):
    """Get course recommendations using genetic algorithm - returns exactly 2 recommended courses"""
    try:
        # Load student data
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            return {
                "success": False,
                "message": f"Student with NUID {nuid} not found",
                "data": None
            }
        
        # Get student's completed courses and core subjects
        completed_courses = set(get_student_completed_courses(student_data))
        core_subjects = get_student_core_subjects(student_data)
        core_remaining = [c for c in core_subjects if c not in completed_courses]
        
        # Load all courses and get available subjects
        subjects_df = load_course_data()
        all_subjects = subjects_df['subject_id'].tolist()
        available_subjects = [s for s in all_subjects if s not in completed_courses]
        
        # Apply interest-based filtering
        interests = get_student_desired_outcomes(student_data)
        if interests:
            available_subjects = filter_courses_by_interests(available_subjects, interests, subjects_df)
        
        # Run genetic algorithm to get exactly 2 courses
        best_courses = genetic_algorithm(available_subjects, completed_courses, student_data, core_remaining)
        best_courses = best_courses[:2]  # Ensure we only get 2 courses
        
        # Format recommendations
        recommendations = []
        for course in best_courses:
            # Convert numpy floats to Python floats
            burnout = float(calculate_burnout(student_data, course, subjects_df))
            utility = float(calculate_utility(student_data, course, subjects_df))
            alignment = float(calculate_outcome_alignment_score(student_data, course, subjects_df))
            
            # Get prerequisites
            prereqs = get_unmet_prerequisites(subjects_df, course, completed_courses)
            
            # Generate recommendation reasons
            reasons = [
                "Selected by genetic algorithm for optimal academic fit",
                "Aligns with your academic progress",
                "Fits well with your current knowledge profile"
            ]
            
            recommendations.append({
                "subject_id": course,
                "subject_name": get_subject_name(subjects_df, course),
                "burnout_risk": round(float(burnout), 2),
                "workload_level": "High" if burnout > 0.7 else "Medium" if burnout > 0.4 else "Low",
                "prerequisites": int(len(prereqs)),
                "reasons": reasons[0]
            })
        # Calculate average burnout for the pair
        avg_burnout = sum(r["burnout_risk"] for r in recommendations) / len(recommendations)
        
        print("recommendations", recommendations)
        return {
            "success": True,
            "message": "Recommendations generated successfully",
            "data": {
                "recommendations": recommendations,
                "summary": {
                    "total_courses": int(len(recommendations)),
                    "average_burnout": round(float(avg_burnout), 2),
                    "completed_courses": int(len(completed_courses)),
                    "remaining_core": int(len(core_remaining))
                }
            }
        }
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating recommendations: {str(e)}",
            "data": None
        }

@app.get("/schedule/{nuid}")
def get_schedule(nuid: str):
    """Get saved schedule for a student"""
    try:
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        schedule_collection = db["user_schedules"]
        
        schedule = schedule_collection.find_one({"NUID": nuid})
        
        if schedule is None:
            raise HTTPException(status_code=404, detail=f"No schedule found for student {nuid}")
        
        schedule["_id"] = str(schedule["_id"]) 
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

@app.get("/dashboard/overview/{nuid}")
async def get_dashboard_overview(nuid: str):
    """Get the main dashboard overview with real calculated data"""
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        completed_courses = get_student_completed_courses(student_data)
        core_subjects = get_student_core_subjects(student_data)
        
        # Get current workload and burnout calculations
        current_courses = completed_courses  # Get current semester courses
        current_workload = sum(4 for _ in current_courses)  # Assuming 4 credits per course
        
        # Calculate burnout risk for current schedule
        burnout_scores = [calculate_burnout(student_data, course, subjects_df) 
                         for course in current_courses]
        avg_burnout = sum(burnout_scores) / len(burnout_scores) if burnout_scores else 0
        
        # Get recommended courses using the genetic algorithm
        available_subjects = [s for s in subjects_df['subject_id'].tolist() 
                            if s not in completed_courses]
        interests = get_student_desired_outcomes(student_data)
        
        if interests:
            available_subjects = filter_courses_by_interests(available_subjects, interests, subjects_df)
        
        recommended_courses = run_genetic_algorithm_with_animation(
            available_subjects, completed_courses, student_data, core_subjects
        )
        
        # Convert recommendations to detailed format
        recommendations = convert_ga_schedule_to_recommendations(
            recommended_courses, student_data, subjects_df, interests
        )
        
        return {
            "current_semester": {
                "term": "Spring 2024",  # You might want to calculate this based on current date
                "credit_hours": current_workload,
                "burnout_risk": {
                    "level": "High" if avg_burnout > 0.7 else "Medium" if avg_burnout > 0.4 else "Low",
                    "score": avg_burnout
                }
            },
            "recommended_courses": [
                {
                    "subject_id": rec["subject_code"],
                    "name": rec["name"],
                    "alignment_score": rec["match_score"],
                    "burnout_risk": rec["burnout_score"],
                    "utility_score": rec["utility_score"]
                } for rec in recommendations[:2]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/catalog")
async def get_course_catalog(
    nuid: str,
    search: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    """Get the course catalog with real data and calculations"""
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        completed_courses = get_student_completed_courses(student_data)
        
        # Filter available courses
        all_courses = subjects_df['subject_id'].tolist()
        available_courses = [c for c in all_courses if c not in completed_courses]
        
        # Apply category filter if specified
        if category:
            available_courses = [c for c in available_courses 
                               if category.lower() in subjects_df[subjects_df['subject_id'] == c]['category'].iloc[0].lower()]
        
        # Calculate course details
        courses = []
        for subject_id in available_courses:
            subject_row = subjects_df[subjects_df['subject_id'] == subject_id].iloc[0]
            burnout_score = calculate_burnout(student_data, subject_id, subjects_df)
            utility_score = calculate_utility(student_data, subject_id, subjects_df)
            alignment_score = calculate_outcome_alignment_score(student_data, subject_id, subjects_df)
            
            courses.append({
                "subject_id": subject_id,
                "name": subject_row['subject_name'],
                "description": subject_row.get('description', ''),
                "credits": 4,  # You might want to get this from your data
                "prerequisites": subject_row.get('prerequisites', []),
                "workload": "High" if burnout_score > 0.7 else "Medium" if burnout_score > 0.4 else "Low",
                "alignment_score": alignment_score,
                "burnout_risk": burnout_score,
                "utility_score": utility_score
            })
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_courses = courses[start_idx:end_idx]
        
        return {
            "courses": paginated_courses,
            "total": len(courses),
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{nuid}")
async def get_student_schedule(nuid: str):
    """Get student's schedule with real calculations"""
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        completed_courses = get_student_completed_courses(student_data)
        core_subjects = get_student_core_subjects(student_data)
        
        available_subjects = [s for s in subjects_df['subject_id'].tolist() 
                            if s not in completed_courses]
        
        schedule = []
        taken = set(completed_courses)
        for _ in range(2):
            semester_courses = run_genetic_algorithm_with_animation(
                available_subjects, taken, student_data, core_subjects
            )
            schedule.append(semester_courses)
            taken.update(semester_courses)
            available_subjects = [s for s in available_subjects if s not in taken]
        
        optimized_schedule, total_burnout = optimize_schedule(schedule, student_data, completed_courses)
        
        formatted_schedule = {
            "current_semester": {
                "term": "Spring 2024",
                "courses": [
                    {
                        "subject_id": course,
                        "name": get_subject_name(subjects_df, course),
                        "credits": 4,
                        "burnout_risk": calculate_burnout(student_data, course, subjects_df),
                        "utility_score": calculate_utility(student_data, course, subjects_df)
                    } for course in optimized_schedule[0]
                ],
                "total_credits": len(optimized_schedule[0]) * 4,
                "workload_status": "High" if total_burnout > 0.7 else "Moderate" if total_burnout > 0.4 else "Low"
            },
            "upcoming_semesters": [
                {
                    "term": f"Fall 2024",
                    "courses": [
                        {
                            "subject_id": course,
                            "name": get_subject_name(subjects_df, course),
                            "credits": 4,
                            "prerequisites": list(get_unmet_prerequisites(subjects_df, course, completed_courses))
                        } for course in semester
                    ],
                    "total_credits": len(semester) * 4
                } for semester in optimized_schedule[1:]
            ]
        }
        
        return formatted_schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/burnout-analysis/{nuid}")
async def get_burnout_analysis(nuid: str):
    """Get detailed burnout analysis with real calculations"""
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        current_courses = get_student_completed_courses(student_data)  # Get current semester courses
        
        # Calculate burnout metrics for each course
        workload_distribution = []
        total_hours = 0
        for course in current_courses:
            burnout_score = calculate_burnout(student_data, course, subjects_df)
            # Estimate weekly hours based on burnout score
            estimated_hours = int(10 + (burnout_score * 10))  # Scale 10-20 hours
            total_hours += estimated_hours
            
            workload_distribution.append({
                "course_id": course,
                "hours_per_week": estimated_hours,
                "status": "high" if burnout_score > 0.7 else "normal"
            })
        
        # Calculate overall metrics
        avg_burnout = sum(calculate_burnout(student_data, course, subjects_df) 
                         for course in current_courses) / len(current_courses) if current_courses else 0
        
        print("avg_burnout", avg_burnout)
        
        return {
            "overall_burnout_risk": {
                "level": "High" if avg_burnout > 0.7 else "Medium" if avg_burnout > 0.4 else "Low",
                "description": "Based on current schedule"
            },
            "weekly_study_hours": {
                "total": total_hours,
                "trend": "increasing" if avg_burnout > 0.6 else "stable"
            },
            "course_difficulty": {
                "level": "High" if avg_burnout > 0.7 else "Moderate",
                "description": "Relative to your background"
            },
            "workload_distribution": workload_distribution,
            "stress_factors": {
                "assignment_deadlines": "High" if avg_burnout > 0.85 else "Medium",
                "course_complexity": "High" if avg_burnout > 0.6 else "Medium",
                "weekly_workload": "High" if total_hours > 40 else "Medium",
                "prerequisite_match": "Low" if avg_burnout < 0.3 else "Medium"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress/{nuid}")
async def get_academic_progress(nuid: str):
    """Get academic progress with real calculations based on user data"""
    try:
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db_users = client["user_details"]
        db_courses = client["subject_details"]
        users_collection = db_users["users"]
        courses_collection = db_courses["courses"]
        
        user = users_collection.find_one({"NUID": nuid})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with NUID {nuid} not found"
            )
        
        def gpa_to_letter(gpa):
            if gpa >= 4.0: return 'A'
            elif gpa >= 3.67: return 'A-'
            elif gpa >= 3.33: return 'B+'
            elif gpa >= 3.0: return 'B'
            elif gpa >= 2.67: return 'B-'
            elif gpa >= 2.33: return 'C+'
            elif gpa >= 2.0: return 'C'
            elif gpa >= 1.67: return 'C-'
            elif gpa >= 1.33: return 'D+'
            elif gpa >= 1.0: return 'D'
            else: return 'F'
            
        def numeric_to_letter(numeric_grade: int):
            if int(numeric_grade) >= 93: return 'A'
            elif int(numeric_grade) >= 90: return 'A-'
            elif int(numeric_grade) >= 87: return 'B+'
            elif int(numeric_grade) >= 83: return 'B'
            elif int(numeric_grade) >= 80: return 'B-'
            elif int(numeric_grade) >= 77: return 'C+'
            elif int(numeric_grade) >= 73: return 'C'
            elif int(numeric_grade) >= 70: return 'C-'
            elif int(numeric_grade) >= 67: return 'D+'
            elif int(numeric_grade) >= 60: return 'D'
            else: return 'F'
    
        grade_to_gpa = {
            'A': 4.0, 'A-': 3.67,
            'B+': 3.33, 'B': 3.0, 'B-': 2.67,
            'C+': 2.33, 'C': 2.0, 'C-': 1.67,
            'D+': 1.33, 'D': 1.0, 'F': 0.0
        }
        
        CREDITS_PER_COURSE = 4
        completed_courses = user.get('completed_courses', {})
        
        # Calculate total GPA
        total_gpa_points = 0
        for details in completed_courses.values():
            print("details", details["final_grade"])
            numeric_grade = details["final_grade"]
            letter_grade = numeric_to_letter(numeric_grade)
            print("asdfasdfasdf")
            grade_value = grade_to_gpa.get(letter_grade, 0.0)
            total_gpa_points += grade_value
        
        num_completed_courses = len(completed_courses)
        cumulative_gpa = total_gpa_points / num_completed_courses if num_completed_courses > 0 else 0.0
        letter_grade = gpa_to_letter(cumulative_gpa)
        
        formatted_completed_courses = {}
        course_outcomes = []
        
        for subject_code in completed_courses.keys():
            course_details = courses_collection.find_one({"subject_id": subject_code})
            if course_details:
                formatted_completed_courses[subject_code] = course_details["subject_name"]
                if "course_outcomes" in course_details:
                    course_outcomes.extend(course_details["course_outcomes"])
            else:
                formatted_completed_courses[subject_code] = subject_code

        programming_experience = user.get('programming_experience', {})
        math_experience = user.get('math_experience', {})
        
        response = {
            "total_credits": num_completed_courses * CREDITS_PER_COURSE,
            "total_courses": num_completed_courses,
            "current_grade": letter_grade,
            "completed_courses": formatted_completed_courses,
            "programming_experience": programming_experience,
            "math_experience": math_experience,
            "course_outcomes": list(set(course_outcomes))  # Remove duplicates
        }
        
        print("response", response)
        
        return {
            "success": True,
            "message": "Academic progress retrieved successfully",
            "data": response
        }
        
    except Exception as e:
        print(f"Error retrieving academic progress: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving academic progress: {str(e)}"
        )

@app.post("/auth/login")
async def login_user(user_data: UserLoginRequest):
    """Login endpoint to verify user credentials"""
    try:
        # Connect to MongoDB
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        users_collection = db["users"]
        
        for user in users_collection.find():
            print(user["name"])
        
        # Find user by NUID and name
        user = users_collection.find_one({
            "NUID": user_data.nuid,
            "name": user_data.name
        })
        
        print(user)
        
        if user is None:
            return UserResponse(
                success=False,
                message="Invalid credentials. User not found.",
                data=None
            )
        
        user.pop('_id', None)
        
        return UserResponse(
            success=True,
            message="Login successful",
            data=user
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during login: {str(e)}"
        )

@app.post("/auth/check-user")
async def check_user(user_data: UserLoginRequest):
    """Check if user exists endpoint"""
    try:
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        users_collection = db["users"]
        
        # Check for existing user
        existing_user = users_collection.find_one({
            "NUID": user_data.nuid
        })
        
        if existing_user:
            return UserResponse(
                success=False,
                message="User with this NUID already exists",
                data=None
            )
            
        return UserResponse(
            success=True,
            message="User does not exist, proceed with registration",
            data=None
        )

    except Exception as e:
        print(f"User check error: {str(e)}")
        return UserResponse(
            success=False,
            message=f"Error checking user: {str(e)}",
            data=None
        )

@app.post("/auth/register")
async def register_user(user_data: UserRegisterRequest):
    """Register endpoint to create new user with complete profile"""
    try:
        from pymongo import MongoClient
        from utils import MONGO_URI
        
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        users_collection = db["users"]
        
        print("user_data", user_data)
            
        # Create new user document with all the provided data
        new_user = {
            "NUID": user_data.nuid,
            "name": user_data.name,
            "desired_outcomes": user_data.interests,  # This matches your DB schema
            "programming_experience": user_data.programming_experience,
            "math_experience": user_data.math_experience,
            "completed_courses": {  # Convert list to dictionary as per your DB schema
                course.subject_code: {
                    "name": course.course_name,
                    "weekly_workload": course.weekly_workload,
                    "final_grade": course.final_grade,
                    "experience_rating": course.experience_rating
                } for course in user_data.completed_courses
            },
            "core_subjects": user_data.core_subjects,
            "created_at": datetime.now()
        }
        
        # Insert the new user
        result = users_collection.insert_one(new_user)
        
        print("result", result)
        
        if not result.inserted_id:
            return UserResponse(
                success=False,
                message="Failed to create user",
                data=None
            )
        
        return UserResponse(
            success=True,
            message="User registered successfully", 
            data={
                "nuid": user_data.nuid,
                "name": user_data.name,
                "interests": user_data.interests,
                "completed_courses_count": len(user_data.completed_courses),
                "core_subjects_count": len(user_data.core_subjects)
            }
        )

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return UserResponse(
            success=False,
            message=f"Error during registration: {str(e)}",
            data=None
        )

@app.get("/course-catalog/{nuid}")
async def get_course_catalog(nuid: Optional[str] = None):
    """Get all courses from the database with their subject ID, name, description, core status, and detailed information"""
    try:
        # Use the existing load_course_data function
        courses_df = load_course_data()
        
        # Get student's core subjects if NUID is provided
        core_subjects = set()
        if nuid:
            student_data = load_student_data(nuid)
            if student_data is not None and not student_data.empty:
                core_subjects = set(get_student_core_subjects(student_data))
        
        # Convert to list of dictionaries with all required fields
        course_list = courses_df[[
            'subject_id', 
            'subject_name', 
            'description', 
            'seats', 
            'enrollments',
            'assignment_count',
            'exam_count',
            'course_outcomes',
            'programming_knowledge_needed',
            'math_requirements',
            'prerequisite'
        ]].to_dict(orient='records')
        
        # Create two lists: one for core courses and one for non-core courses
        core_courses = []
        non_core_courses = []
        
        # Separate courses into core and non-core, and add enrollment demand
        for course in course_list:
            # Add core status
            course['is_core'] = course['subject_id'] in core_subjects
            
            # Calculate enrollment demand
            seats = course.get('seats', 0)
            enrollments = course.get('enrollments', 0)
            
            # Calculate enrollment percentage
            if seats > 0:
                enrollment_percentage = (enrollments / seats) * 100
                if enrollment_percentage >= 100:
                    course['enrollment_demand'] = "High"
                elif enrollment_percentage >= 90:
                    course['enrollment_demand'] = "Medium"
                else:
                    course['enrollment_demand'] = "Low"
            else:
                course['enrollment_demand'] = "Low"
            
            # Remove seats and enrollments from response
            course.pop('seats')
            course.pop('enrollments')
            
            # Ensure lists are empty lists instead of None
            course['course_outcomes'] = course.get('course_outcomes', []) or []
            course['programming_knowledge_needed'] = course.get('programming_knowledge_needed', []) or []
            course['math_requirements'] = course.get('math_requirements', []) or []
            course['prerequisite'] = course.get('prerequisite', []) or []
            
            # Sort into appropriate list
            if course['is_core']:
                core_courses.append(course)
            else:
                non_core_courses.append(course)
        
        # Combine the lists with core courses first
        sorted_course_list = core_courses + non_core_courses
        
        print("sorted_course_list", sorted_course_list)
        
        return {
            "success": True,
            "message": "Course catalog retrieved successfully",
            "data": sorted_course_list
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving course catalog: {str(e)}",
            "data": None
        }

@app.post("/recommend-full/{nuid}")
async def get_full_recommendations(
    nuid: str,
    request: RecommendationRequest
):
    """
    Get course recommendations recursively, taking into account previously selected courses.
    If no previous selections exist, falls back to basic recommendations.
    """
    try:
        # Initialize lists from request model
        selected_courses = request.selected_courses or []
        blacklisted_courses = request.blacklisted_courses or []
        
        # If no selected courses and no blacklisted courses, use basic recommendations
        if not selected_courses and not blacklisted_courses:
            return await get_recommendations(nuid)
        
        # Load necessary data
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            return await get_recommendations(nuid)
        
        subjects_df = load_course_data()
        
        # Get student's completed courses and core subjects
        completed_courses = set(get_student_completed_courses(student_data))
        core_subjects = get_student_core_subjects(student_data)
        
        # Add selected courses to completed set for recommendation purposes
        taken = completed_courses.union(set(selected_courses))
        
        # Update core remaining based on selected courses
        core_remaining = [c for c in core_subjects if c not in taken]
        
        # Get all available subjects excluding completed, selected, and blacklisted
        all_subjects = subjects_df['subject_id'].tolist()
        available_subjects = [
            s for s in all_subjects 
            if s not in taken and s not in blacklisted_courses
        ]
        
        # Apply interest-based filtering
        interests = get_student_desired_outcomes(student_data)
        if interests:
            available_subjects = filter_courses_by_interests(available_subjects, interests, subjects_df)
            
        if len(available_subjects) < 2:
            return {
                "success": False,
                "message": "Not enough available courses for recommendations",
                "data": None
            }
            
        # Run genetic algorithm to get exactly 2 courses
        best_courses = genetic_algorithm(available_subjects, taken, student_data, core_remaining)
        best_courses = best_courses[:2]
        
        # Format recommendations with detailed information
        recommendations = []
        for course in best_courses:
            burnout = float(calculate_burnout(student_data, course, subjects_df))
            utility = float(calculate_utility(student_data, course, subjects_df))
            alignment = float(calculate_outcome_alignment_score(student_data, course, subjects_df))
            prereqs = get_unmet_prerequisites(subjects_df, course, taken)
            
            course_row = subjects_df[subjects_df['subject_id'] == course].iloc[0]
            
            recommendations.append({
                "subject_id": str(course),
                "subject_name": str(get_subject_name(subjects_df, course)),
                "description": str(course_row.get('description', '')),
                "burnout_risk": float(burnout),
                "workload_level": str("High" if burnout > 0.7 else "Medium" if burnout > 0.4 else "Low"),
                "utility_score": float(utility),
                "alignment_score": float(alignment),
                "prerequisites": int(len(prereqs)),
                "unmet_prerequisites": list(map(str, prereqs)),
                "is_core": bool(course in core_subjects),
                "reasons": [
                    "Selected by genetic algorithm for optimal academic fit",
                    "Aligns with your academic progress",
                    "Fits well with your current knowledge profile"
                ],
                "assignment_count": int(course_row.get('assignment_count', 0)),
                "exam_count": int(course_row.get('exam_count', 0)),
                "course_outcomes": list(map(str, course_row.get('course_outcomes', []))),
                "programming_knowledge_needed": list(map(str, course_row.get('programming_knowledge_needed', []))),
                "math_requirements": list(map(str, course_row.get('math_requirements', [])))
            })
        
        # Calculate summary statistics
        avg_burnout = float(sum(r["burnout_risk"] for r in recommendations) / len(recommendations))
        avg_utility = float(sum(r["utility_score"] for r in recommendations) / len(recommendations))
        
        response_data = {
            "success": True,
            "message": "Recommendations generated successfully",
            "data": {
                "recommendations": recommendations,
                "summary": {
                    "total_recommended": int(len(recommendations)),
                    "average_burnout": float(round(avg_burnout, 2)),
                    "average_utility": float(round(avg_utility, 2)),
                    "completed_courses": int(len(completed_courses)),
                    "selected_courses": int(len(selected_courses)),
                    "remaining_core": int(len(core_remaining)),
                    "semester_number": int((len(selected_courses) // 2) + 1)
                }
            }
        }

        # Convert any remaining NumPy types
        response_data = convert_numpy_to_native(response_data)
        return response_data
        
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating recommendations: {str(e)}",
            "data": None
        }

@app.post("/save-schedule/{nuid}", response_model=SaveScheduleResponse)
async def save_schedule(
    nuid: str,
    request: SaveScheduleRequest
):
    """
    Save a course schedule for a student
    
    Args:
        nuid: Student ID
        request: SaveScheduleRequest containing schedule name and list of course IDs
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        schedules_collection = db["user_schedules"]
        
        # Load necessary data
        student_data = load_student_data(nuid)
        if student_data is None or student_data.empty:
            return SaveScheduleResponse(
                success=False,
                message=f"Student with NUID {nuid} not found",
                data=None
            )
        
        subjects_df = load_course_data()
        
        # Validate that all courses exist
        invalid_courses = [
            course for course in request.courses 
            if course not in subjects_df['subject_id'].values
        ]
        if invalid_courses:
            return SaveScheduleResponse(
                success=False,
                message=f"Invalid course IDs: {', '.join(invalid_courses)}",
                data=None
            )
        
        # Calculate schedule metrics
        course_details = []
        total_burnout = 0
        total_utility = 0
        
        for course in request.courses:
            burnout = float(calculate_burnout(student_data, course, subjects_df))
            utility = float(calculate_utility(student_data, course, subjects_df))
            course_row = subjects_df[subjects_df['subject_id'] == course].iloc[0]
            
            course_details.append({
                "subject_id": str(course),
                "subject_name": str(get_subject_name(subjects_df, course)),
                "burnout_risk": float(burnout),
                "utility_score": float(utility),
                "workload_level": "High" if burnout > 0.7 else "Medium" if burnout > 0.4 else "Low",
                "assignment_count": int(course_row.get('assignment_count', 0)),
                "exam_count": int(course_row.get('exam_count', 0))
            })
            
            total_burnout += burnout
            total_utility += utility
        
        avg_burnout = total_burnout / len(request.courses) if request.courses else 0
        avg_utility = total_utility / len(request.courses) if request.courses else 0
        
        # Create schedule document
        schedule_doc = {
            "nuid": nuid,
            "name": request.name,
            "created_at": datetime.now(),
            "courses": course_details,
            "metrics": {
                "total_courses": len(request.courses),
                "average_burnout": float(round(avg_burnout, 2)),
                "average_utility": float(round(avg_utility, 2)),
                "workload_assessment": "High" if avg_burnout > 0.7 else "Medium" if avg_burnout > 0.4 else "Low"
            }
        }
        
        # Check if schedule with this name already exists for this student
        existing_schedule = schedules_collection.find_one({
            "nuid": nuid,
            "name": request.name
        })
        
        if existing_schedule:
            # Update existing schedule
            result = schedules_collection.update_one(
                {"_id": ObjectId(existing_schedule["_id"])},
                {
                    "$set": schedule_doc,
                    "$push": {
                        "history": {
                            "timestamp": datetime.now(),
                            "previous_state": existing_schedule
                        }
                    }
                }
            )
            
            if result.modified_count > 0:
                schedule_doc['_id'] = existing_schedule['_id']  # Add the string ID to response
                return SaveScheduleResponse(
                    success=True,
                    message=f"Schedule '{request.name}' updated successfully",
                    data=convert_numpy_to_native(schedule_doc)
                )
            else:
                return SaveScheduleResponse(
                    success=False,
                    message="Failed to update schedule",
                    data=None
                )
        else:
            # Create new schedule
            result = schedules_collection.insert_one(schedule_doc)
            
            if result.inserted_id:
                schedule_doc['_id'] = str(result.inserted_id)
                return SaveScheduleResponse(
                    success=True,
                    message=f"Schedule '{request.name}' saved successfully",
                    data=convert_numpy_to_native(schedule_doc)
                )
            else:
                return SaveScheduleResponse(
                    success=False,
                    message="Failed to save schedule",
                    data=None
                )
                
    except Exception as e:
        print(f"Error saving schedule: {str(e)}")
        return SaveScheduleResponse(
            success=False,
            message=f"Error saving schedule: {str(e)}",
            data=None
        )

@app.get("/schedules/{nuid}", response_model=ScheduleListResponse)
async def get_schedules(nuid: str):
    """
    Get all saved schedules for a student
    
    Args:
        nuid: Student ID
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        schedules_collection = db["user_schedules"]
        
        # Get all schedules for this student
        schedules = list(schedules_collection.find({"nuid": nuid}))
        
        if not schedules:
            return ScheduleListResponse(
                success=True,
                message="No saved schedules found",
                data=[]
            )
        
        # Process each schedule
        formatted_schedules = []
        for schedule in schedules:
            # Convert ObjectId to string
            schedule['_id'] = str(schedule['_id'])
            
            # Recalculate metrics for each schedule
            courses = schedule.get('courses', [])
            num_courses = len(courses)
            
            if num_courses > 0:
                # Calculate total burnout and utility
                total_burnout = sum(float(course.get('burnout_risk', 0)) for course in courses)
                total_utility = sum(float(course.get('utility_score', 0)) for course in courses)
                
                # Calculate averages
                avg_burnout = total_burnout / num_courses
                avg_utility = total_utility / num_courses
                
                # Determine workload assessment based on average burnout
                workload_assessment = (
                    "High" if avg_burnout > 0.7 
                    else "Medium" if avg_burnout > 0.4 
                    else "Low"
                )
            else:
                avg_burnout = 0.0
                avg_utility = 0.0
                workload_assessment = "N/A"
            
            # Format the schedule data
            formatted_schedule = {
                "id": schedule['_id'],
                "name": schedule['name'],
                "created_at": schedule['created_at'],
                "courses": [
                    {
                        "subject_id": str(course['subject_id']),
                        "subject_name": str(course['subject_name']),
                        "burnout_risk": float(course['burnout_risk']),
                        "utility_score": float(course['utility_score']),
                        "workload_level": str(course['workload_level']),
                        "assignment_count": int(course['assignment_count']),
                        "exam_count": int(course['exam_count'])
                    }
                    for course in courses
                ],
                "metrics": {
                    "total_courses": int(num_courses),
                    "average_burnout": float(round(avg_burnout, 2)),
                    "average_utility": float(round(avg_utility, 2)),
                    "workload_assessment": workload_assessment
                }
            }
            
            # Add history if it exists
            if 'history' in schedule:
                formatted_schedule['history'] = [
                    {
                        "timestamp": entry['timestamp'],
                        "previous_state": {
                            k: v for k, v in entry['previous_state'].items()
                            if k != '_id'
                        }
                    }
                    for entry in schedule['history']
                ]
            
            formatted_schedules.append(formatted_schedule)
        
        # Sort schedules by creation date (newest first)
        formatted_schedules.sort(
            key=lambda x: x['created_at'],
            reverse=True
        )
        
        print("formatted_schedules", avg_burnout)
        
        return ScheduleListResponse(
            success=True,
            message="Schedules retrieved successfully",
            data=convert_numpy_to_native(formatted_schedules)
        )
        
    except Exception as e:
        print(f"Error retrieving schedules: {str(e)}")
        return ScheduleListResponse(
            success=False,
            message=f"Error retrieving schedules: {str(e)}",
            data=None
        )

@app.delete("/delete-schedule/{nuid}/{schedule_name}", response_model=DeleteScheduleResponse)
async def delete_schedule(nuid: str, schedule_name: str):
    """
    Delete a specific schedule for a student by schedule name
    
    Args:
        nuid: Student ID
        schedule_name: Name of the schedule to delete
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        schedules_collection = db["user_schedules"]
        
        # URL decode the schedule name (in case it contains spaces or special characters)
        decoded_schedule_name = unquote(schedule_name)
        
        # Verify that the schedule exists and belongs to the student
        schedule = schedules_collection.find_one({
            "nuid": nuid,
            "name": decoded_schedule_name
        })
            
        if not schedule:
            return DeleteScheduleResponse(
                success=False,
                message=f"Schedule '{decoded_schedule_name}' not found or doesn't belong to student {nuid}",
                data=None
            )
        
        # Store schedule details before deletion for response
        deleted_schedule = {
            "id": str(schedule["_id"]),
            "name": schedule["name"],
            "created_at": schedule["created_at"],
            "deleted_at": datetime.now()
        }
        
        # Delete the schedule
        result = schedules_collection.delete_one({
            "nuid": nuid,
            "name": decoded_schedule_name
        })
        
        if result.deleted_count > 0:
            return DeleteScheduleResponse(
                success=True,
                message=f"Schedule '{decoded_schedule_name}' deleted successfully",
                data=deleted_schedule
            )
        else:
            return DeleteScheduleResponse(
                success=False,
                message=f"Failed to delete schedule '{decoded_schedule_name}'",
                data=None
            )
            
    except Exception as e:
        print(f"Error deleting schedule: {str(e)}")
        return DeleteScheduleResponse(
            success=False,
            message=f"Error deleting schedule: {str(e)}",
            data=None
        )

def jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Calculate Jaccard similarity between two sets
    """
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def calculate_user_similarity(user1_data: Dict, user2_data: Dict) -> float:
    """
    Calculate similarity between two users based on multiple factors:
    - Programming experience
    - Math experience
    - Completed courses
    - Core subjects
    - Interests/desired outcomes
    """
    similarity_scores = []
    
    # Compare programming experience
    prog_exp1 = set(user1_data.get('programming_experience', {}).keys() if isinstance(user1_data.get('programming_experience'), dict) else user1_data.get('programming_experience', []))
    prog_exp2 = set(user2_data.get('programming_experience', {}).keys() if isinstance(user2_data.get('programming_experience'), dict) else user2_data.get('programming_experience', []))
    if prog_exp1 or prog_exp2:
        similarity_scores.append(jaccard_similarity(prog_exp1, prog_exp2))
    
    # Compare math experience
    math_exp1 = set(user1_data.get('math_experience', {}).keys() if isinstance(user1_data.get('math_experience'), dict) else user1_data.get('math_experience', []))
    math_exp2 = set(user2_data.get('math_experience', {}).keys() if isinstance(user2_data.get('math_experience'), dict) else user2_data.get('math_experience', []))
    if math_exp1 or math_exp2:
        similarity_scores.append(jaccard_similarity(math_exp1, math_exp2))
    
    # Compare completed courses
    courses1 = set(user1_data.get('completed_courses', {}).keys() if isinstance(user1_data.get('completed_courses'), dict) else user1_data.get('completed_courses', []))
    courses2 = set(user2_data.get('completed_courses', {}).keys() if isinstance(user2_data.get('completed_courses'), dict) else user2_data.get('completed_courses', []))
    if courses1 or courses2:
        similarity_scores.append(jaccard_similarity(courses1, courses2))
    
    # Compare core subjects
    core1 = set(user1_data.get('core_subjects', []))
    core2 = set(user2_data.get('core_subjects', []))
    if core1 or core2:
        similarity_scores.append(jaccard_similarity(core1, core2))
    
    # Compare interests/desired outcomes
    interests1 = set(user1_data.get('desired_outcomes', []))
    interests2 = set(user2_data.get('desired_outcomes', []))
    if interests1 or interests2:
        similarity_scores.append(jaccard_similarity(interests1, interests2))
    
    # Return average similarity if we have scores, otherwise 0
    return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

@app.get("/recommend-schedule/{nuid}")
async def recommend_schedule(nuid: str):
    """
    Recommend schedules based on similar users' choices.
    Uses collaborative filtering approach by finding similar users
    and recommending their successful schedules.
    """
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        users_collection = db["users"]
        schedules_collection = db["user_schedules"]
        
        # Get current user's data
        current_user = users_collection.find_one({"NUID": nuid})
        if not current_user:
            return {
                "success": False,
                "message": f"User with NUID {nuid} not found",
                "data": None
            }
        
        # Find similar users
        similar_users = []
        all_users = users_collection.find({"NUID": {"$ne": nuid}})  # Exclude current user
        
        for other_user in all_users:
            similarity = calculate_user_similarity(current_user, other_user)
            if similarity >= 0.5:  # 50% similarity threshold
                similar_users.append({
                    "nuid": other_user["NUID"],
                    "similarity": similarity
                })
        
        if not similar_users:
            return {
                "success": True,
                "message": "No similar users found for recommendations",
                "data": {
                    "recommended_schedules": [],
                    "similar_users_count": 0
                }
            }
        
        # Sort similar users by similarity score (highest first)
        similar_users.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Get schedules from similar users
        recommended_schedules = []
        seen_course_combinations = set()  # To avoid duplicate recommendations
        
        for similar_user in similar_users:
            user_schedules = schedules_collection.find({"nuid": similar_user["nuid"]})
            
            for schedule in user_schedules:
                # Create a frozen set of courses for comparison
                course_set = frozenset(course["subject_id"] for course in schedule.get("courses", []))
                
                # Skip if we've already seen this combination
                if course_set in seen_course_combinations:
                    continue
                
                seen_course_combinations.add(course_set)
                
                # Add similarity score to schedule metadata
                schedule_with_similarity = {
                    "schedule_name": schedule["name"],
                    "similarity_score": round(similar_user["similarity"] * 100, 2),
                    "courses": schedule.get("courses", []),
                    "metrics": schedule.get("metrics", {}),
                    "recommended_by": {
                        "similarity": round(similar_user["similarity"] * 100, 2)
                    }
                }
                
                recommended_schedules.append(schedule_with_similarity)
        
        # Sort recommendations by similarity score
        recommended_schedules.sort(
            key=lambda x: x["similarity_score"],
            reverse=True
        )
        
        return {
            "success": True,
            "message": "Schedule recommendations generated successfully",
            "data": {
                "recommended_schedules": recommended_schedules,
                "similar_users_count": len(similar_users),
                "similarity_threshold": 50,  # 50%
                "total_recommendations": len(recommended_schedules)
            }
        }
        
    except Exception as e:
        print(f"Error generating schedule recommendations: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating schedule recommendations: {str(e)}",
            "data": None
        }

# Add this at the end of your main.py file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

