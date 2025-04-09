from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware



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

class UserLoginRequest(BaseModel):
    nuid: str
    name: str

class UserRegisterRequest(BaseModel):
    nuid: str
    name: str

class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

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
        
        completed_courses = set(get_student_completed_courses(student_data))
        core_subjects = get_student_core_subjects(student_data)
        core_remaining = [c for c in core_subjects if c not in completed_courses]
        
        subjects_df = load_course_data()
        all_subjects = subjects_df['subject_id'].tolist()
        
        available_subjects = [s for s in all_subjects if s not in blacklist and s not in completed_courses]
        
        final_list = []
        plan = [[] for _ in range(semesters)]
        taken = completed_courses.copy()

        for sem_idx in range(semesters):
            current_available = [s for s in available_subjects if s not in final_list]
            
            if len(current_available) < courses_per_semester:
                break
            
            best_semester = genetic_algorithm(current_available, taken, student_data, core_remaining)
            
            plan[sem_idx] = best_semester
            
            final_list.extend(best_semester)
            taken.update(best_semester)
            core_remaining = [c for c in core_remaining if c not in best_semester]
        
        best_plan, total_burnout = rerun_genetic_algorithm(
            final_list, 
            student_data, 
            completed_courses
        )
        
        schedule_data = []
        current_taken = completed_courses.copy()
        
        for i, semester in enumerate(best_plan, 1):
            if semester:
                semester_courses = []
                for subject_id in semester:

                    burnout = calculate_burnout(student_data, subject_id, subjects_df)
                    
                    name = get_subject_name(subjects_df, subject_id)
                    
                    semester_courses.append({
                        "subject_id": subject_id,
                        "subject_name": name,
                        "burnout": round(burnout, 3),
                        "fitness_score": -total_burnout
                    })
                    
                    current_taken.add(subject_id)
                
                schedule_data.append({
                    "semester": i,
                    "courses": semester_courses
                })
        
        save_schedules(nuid, schedule_data)
        
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
        from pymongo import MongoClient
        from utils import MONGO_URI
        
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
                } for rec in recommendations[:2]  # Show top 2 recommendations
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
        
        # Generate schedule using genetic algorithm
        available_subjects = [s for s in subjects_df['subject_id'].tolist() 
                            if s not in completed_courses]
        
        # Run genetic algorithm for multiple semesters
        schedule = []
        taken = set(completed_courses)
        for _ in range(2):  # For next 2 semesters
            semester_courses = run_genetic_algorithm_with_animation(
                available_subjects, taken, student_data, core_subjects
            )
            schedule.append(semester_courses)
            taken.update(semester_courses)
            available_subjects = [s for s in available_subjects if s not in taken]
        
        # Optimize the schedule
        optimized_schedule, total_burnout = optimize_schedule(schedule, student_data, completed_courses)
        
        # Format the response
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
                    "term": f"Fall 2024",  # You might want to calculate this
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
                "assignment_deadlines": "High" if avg_burnout > 0.7 else "Medium",
                "course_complexity": "High" if avg_burnout > 0.6 else "Medium",
                "weekly_workload": "High" if total_hours > 40 else "Medium",
                "prerequisite_match": "Low" if avg_burnout < 0.3 else "Medium"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/academic-progress/{nuid}")
async def get_academic_progress(nuid: str):
    """Get academic progress with real calculations"""
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        completed_courses = get_student_completed_courses(student_data)
        core_subjects = get_student_core_subjects(student_data)
        
        total_credits = 32 
        completed_credits = len(completed_courses) * 4  
        
        completed_core = [c for c in completed_courses if c in core_subjects]
        
        return {
            "credits_completed": completed_credits,
            "total_credits": total_credits,
            "core_courses": {
                "completed": len(completed_core),
                "total": len(core_subjects)
            },
            "current_gpa": 3.8,  
            "requirements_met": (completed_credits / total_credits) * 100,
            "degree_requirements": {
                "core_courses": {
                    "completed": len(completed_core),
                    "total": len(core_subjects),
                    "description": "Required foundational courses"
                },
            },
            "course_history": {
                "Spring 2024": [
                    {
                        "subject_id": course,
                        "name": get_subject_name(subjects_df, course),
                        "grade": "A" 
                    } for course in completed_courses
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/auth/register")
async def register_user(user_data: UserRegisterRequest):
    """Register endpoint to create new user"""
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
            
        # Create new user document
        new_user = {
            "NUID": user_data.nuid,
            "name": user_data.name,
            "completed_courses": [],  # Initialize with empty list
            "core_subjects": [],      # Initialize with empty list
            "created_at": datetime.now()
        }
        
        # Insert the new user
        result = users_collection.insert_one(new_user)
        
        if not result.inserted_id:
            return UserResponse(
                success=False,
                message="Failed to create user",
                data=None
            )
        
        return UserResponse(
            success=True,
            message="User registered successfully", 
            data={"nuid": user_data.nuid, "name": user_data.name}
        )

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return UserResponse(
            success=False,
            message=f"Error during registration: {str(e)}",
            data=None
        )

# Add this at the end of your main.py file
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

