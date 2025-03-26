import pandas as pd
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
client = MongoClient(MONGO_URI)

def load_course_data():
    """Load all course data from MongoDB"""
    db = client["subject_details"]
    collection = db["courses"]
    course_data = list(collection.find({}, {'_id': 0}))  # exclude _id field
    return pd.DataFrame(course_data)

def load_student_data(student_id):
    """Load student data from MongoDB given the student ID"""
    db = client["user_details"]
    collection = db["users"]
    student_data = list(collection.find({"NUID": student_id}, {'_id': 0}))
    return pd.DataFrame(student_data) if student_data else None

def prerequisites_satisfied(course_id, course_df, student_df):
    """Check if prerequisites for a course are satisfied"""
    # course prereqs
    prereqs = set(course_df.loc[course_df["subject_id"] == course_id, "prerequisites"].values[0])
    # completed courses
    completed = set(student_df.get("completed_courses", []))
    # check if all prereqs are satisfied
    return prereqs.issubset(completed)

### Did not touch this for DB conversion; may or may not work - Austin
def standardize_student_data(student_data, for_burnout=True):
    """Standardize student data format between modules"""
    result = {
        'NUID': student_data.get('NUID', ''),
        'desired_outcomes': student_data.get('desired_outcomes', ''),
        'core_subjects': student_data.get('core_subjects', '')
    }
    
    # For programming and math experience
    result['programming_experience'] = student_data.get('programming_experience', {})
    result['math_experience'] = student_data.get('math_experience', {})
    
    # Handle completed courses based on target module
    completed_courses = student_data.get('completed_courses', {})
    if for_burnout:
        # Burnout calculator expects a dictionary
        if isinstance(completed_courses, (list, set)):
            result['completed_courses'] = {course: {} for course in completed_courses}
        else:
            result['completed_courses'] = completed_courses
    else:
        # GA recommender expects a set
        if isinstance(completed_courses, dict):
            result['completed_courses'] = set(completed_courses.keys())
        elif isinstance(completed_courses, list):
            result['completed_courses'] = set(completed_courses)
        else:
            result['completed_courses'] = completed_courses
    
    # Copy any other fields that might be present
    for key in ['interests', 'semester']:
        if key in student_data:
            result[key] = student_data[key]
    
    return result