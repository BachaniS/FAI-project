import pandas as pd
import numpy as np
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["subject_details"]

def calculate_requirement_mismatch(student_data, subject_code, prereqs_collection):
    """Calculate how many prerequisites are unmet."""
    taken = set(student_data['completed_courses'].keys()) if student_data['completed_courses'] else set()
    prereqs = set(prereq['prereq_subject_code'] for prereq in prereqs_collection.find({'subject_code': subject_code}))
    unmet_prereqs = len(prereqs - taken)
    return unmet_prereqs / (len(prereqs) + 1) if prereqs else 0  # [0,1]

def calculate_outcome_mismatch(student_data, subject_code, courses_collection):
    """Calculate how well the course outcomes match student's desired outcomes."""
    desired = set(student_data['desired_outcomes'].lower().split(','))
    subject = courses_collection.find_one({'subject_code': subject_code})
    if not subject or 'course_outcomes' not in subject:
        return 1.0
    subject_outcomes = set(outcome.lower() for outcome in subject['course_outcomes'])
    overlap = len(desired & subject_outcomes) / len(desired) if desired else 0
    return 1 - overlap  # [0,1], lower mismatch = better alignment

def calculate_workload_factor(subject_code: str, courses_collection) -> float:
    """Calculate workload factor for a subject."""
    subject = courses_collection.find_one({'subject_code': subject_code})
    if not subject:
        print(f"Warning: Subject {subject_code} not found in database")
        return 1.0
    
    # Calculate workload based on available metrics
    weekly_workload = subject.get('weekly_course_time', 0)
    num_assignments = subject.get('assignment_count', 0)
    assignment_time = subject.get('assignment_time', 0)
    
    total_workload = weekly_workload + (num_assignments * assignment_time)
    
    # Normalize workload
    MAX_WORKLOAD = 20  # Maximum expected weekly workload
    workload_factor = total_workload / MAX_WORKLOAD
    
    return min(max(workload_factor, 0.1), 2.0)  # Keep between 0.1 and 2.0

def calculate_stress_factor(student_data, subject_code, courses_collection):
    """Calculate stress factor based on grades."""
    subject = courses_collection.find_one({'subject_code': subject_code})
    if not subject:
        return 0.5  # Default middle value if subject not found
        
    if subject_code in student_data['completed_courses']:
        avg_grade = student_data['completed_courses'][subject_code].get('final_grade', subject['final_grade'])
    else:
        avg_grade = subject.get('final_grade', 85)  # Default to 85 if not specified
        
    S_prime = ((100 - avg_grade) / 100) ** 2
    return S_prime  # [0,1]

def calculate_burnout(student_data, subject_code, courses_collection, prereqs_collection, outcomes_collection):
    """Calculate overall burnout score for a subject."""
    M_req = calculate_requirement_mismatch(student_data, subject_code, prereqs_collection)
    M_out = calculate_outcome_mismatch(student_data, subject_code, courses_collection)
    W_prime = calculate_workload_factor(subject_code, courses_collection)
    S_prime = calculate_stress_factor(student_data, subject_code, courses_collection)
    
    # Calculate weighted average of factors
    P_prime = (M_req + M_out + W_prime + S_prime) / 4
    
    # Apply sigmoid function to get final burnout score
    return 1 / (1 + np.exp(-(P_prime - 0.5)))  # [0,1]

def calculate_scores(nuid):
    """Calculate burnout scores for all subjects for a given student."""
    # Get collections
    courses_collection = db["courses"]
    prereqs_collection = db["prerequisites"]
    outcomes_collection = db["outcomes"]
    users_collection = client["user_details"]["users"]
    
    # Get student data
    student_data = users_collection.find_one({"NUID": nuid})
    if not student_data:
        raise ValueError(f"Student with NUID {nuid} not found")
    
    scores = []
    for subject in courses_collection.find():
        subject_code = subject['subject_code']
        burnout = calculate_burnout(student_data, subject_code, 
                                  courses_collection, prereqs_collection, outcomes_collection)
        scores.append({'subject_code': subject_code, 'burnout_score': burnout})
    
    return scores

if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    try:
        scores = calculate_scores(nuid)
        print("\nBurnout Scores:")
        for score in sorted(scores, key=lambda x: x['burnout_score'], reverse=True):
            print(f"{score['subject_code']}: {score['burnout_score']:.2f}")
    except Exception as e:
        print(f"Error calculating burnout scores: {str(e)}")