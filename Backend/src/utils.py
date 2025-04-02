import pandas as pd
from pymongo import MongoClient
import json
import os

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
client = MongoClient(MONGO_URI)

## Loading functions ##

def load_course_data():
    '''
    Load all course data from MongoDB
    Returns:
        all course data in the monogodb
    '''
    db = client["subject_details"]
    collection = db["courses"]
    course_data = list(collection.find({}, {'_id': 0}))  # exclude _id field
    return pd.DataFrame(course_data)

def load_student_data(student_id):
    '''
    Load student data from MongoDB given the student ID
    Params:
        student_id: given student id
    Returns:
        Data for the given student
    '''
    db = client["user_details"]
    collection = db["users"]
    
    # Find the document
    student_data = collection.find_one({"NUID": student_id})
    
    # Convert to DataFrame
    student_df = pd.DataFrame([student_data])
    return student_df

def load_scores(nuid):
    '''
    Load score details from database
    Params:
        nuid: Student ID
        
    Return:
        DataFrame: DataFrame containing score details, or None if not found
    '''
    db = client["user_details"]
    collection = db["user_scores"]
    student_data = collection.find_one({"NUID": nuid})
    return pd.DataFrame(student_data["courses"]) if student_data else None

def load_interest_categories():
    '''
    Load interest categories from JSON file
    Return:
        Dictionary of interest categories and their related terms
    '''
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interest_categories.json")
        
        with open(file_path, 'r') as f:
            interest_categories = json.load(f)
            
        return interest_categories
    except Exception as e:
        print(f"⚠️ Error loading interest categories: {e}")
        return {
            "artificial intelligence": ["Artificial Intelligence"],
            "machine learning": ["Machine Learning"],
            "web": ["JavaScript", "Web Development"],
            "data science": ["Data Science"],
            "computer vision": ["Computer Vision"]
        }
## Saving functions ##

def save_scores(nuid, burnout_scores):
    '''
    Save burnout scores to MongoDB
    
    Params:
        nuid: Student ID
        burnout_scores: List of dictionaries containing burnout scores
    '''
    try:
        db = client["user_details"]
        burnout_collection = db["user_scores"]
        
        burnout_doc = {
            "NUID": nuid,
            "courses": burnout_scores,
            "updated": pd.Timestamp.now(),
        }
        
        # replace if exists
        burnout_collection.replace_one(
            {"NUID": nuid},
            burnout_doc,
            upsert=True
        )
        
        print(f"Burnout scores saved for student {nuid}")
    except Exception as e:
        print(f"Error saving burnout scores: {e}")

def save_schedules(nuid, schedule_data):
    '''
    Save course schedule to MongoDB
    
    Params:
        nuid: Student ID
        schedule: Dictionary containing course schedule
    '''
    try:
        db = client["user_details"]
        schedule_collection = db["user_schedules"]

        schedule_doc = {
            "NUID": nuid,
            "updated": pd.Timestamp.now(),
            "schedule": schedule_data
        }

        # Replace if exists, otherwise insert
        schedule_collection.replace_one(
            {"NUID": nuid},
            schedule_doc,
            upsert=True
        )

        print(f"Schedule saved for student {nuid}")

    except Exception as e:
            print(f"Error saving schedule: {e}")
            return None

def update_knowledge_profile(student_data, taken):
    """
    Update the knowledge profile of a student based on their experience and completed courses.
    
    Args:
        student_data: Dictionary containing student information including experience and completed courses.
        taken: Set of completed course subject codes.
        
    Returns:
        Tuple of two dictionaries: (programming_skills, math_skills)
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_tags.json")
    with open(path, "r") as file:
        tags = json.load(file)

    programming_tags = set(tags.get('programming_tags', []))
    math_tags = set(tags.get('math_tags', []))

    if not student_data.empty:
        programming_skills = student_data['programming_experience'].iloc[0]
        math_skills = student_data['math_experience'].iloc[0]
    else:
        programming_skills = {}
        math_skills = {}

    subjects_df = load_course_data()

    # Update skills based on completed courses
    for subject_code in taken:
        subject_outcomes = get_subject_outcomes(subjects_df, subject_code)
        for outcome in subject_outcomes:
            if outcome in programming_skills:
                programming_skills[outcome] = programming_skills.get(outcome, 0) + 1
            elif outcome in math_skills:
                math_skills[outcome] = math_skills.get(outcome, 0) + 1
            # If new skill not in student profile
            else:
                if outcome in math_tags:
                    math_skills[outcome] = math_skills.get(outcome, 0) + 1
                elif outcome in programming_tags:
                    programming_skills[outcome] = programming_skills.get(outcome, 0) + 1
                # not in either, just default to programming
                else:
                    programming_skills[outcome] = programming_skills.get(outcome, 0) + 1


    # Normalize skills based on cumulative experience
    normalized_programming_skills = {k: min(v, 5.0) for k, v in programming_skills.items()}
    normalized_math_skills = {k: min(v, 5.0) for k, v in math_skills.items()}

    return normalized_programming_skills, normalized_math_skills

def save_knowledge_profile(nuid, programming_experience, math_experience):
    """
    Save the updated knowledge profile of a student to the database.
    
    Args:
        nuid: The student's NUid (unique identifier).
        knowledge_profile: Dictionary containing the updated knowledge profile.
    """
    db = client["user_details"]
    collection = db["users"]
    
    # Find the document
    student_data = collection.find_one({"NUID": nuid})

    update_query = {
        '$set': {
            'programming_experience': programming_experience,
            'math_experience': math_experience,
        }
    }
    
    result = collection.update_one(student_data, update_query)

    if result.matched_count > 0:
        print(f"Profile updated for student {nuid}.")
    else:
        print(f"No student found with NUid {nuid}. Profile not updated.")

def save_desired_outcomes(nuid, desired_outcomes):
    db = client["user_details"]
    collection = db["users"]
    
    result = collection.update_one(
    {"NUID": nuid}, 
    {"$set": {"desired_outcomes": desired_outcomes}}, 
    upsert=True
    )

    if result.matched_count > 0:
        print(f"Profile updated for student {nuid}.")
    else:
        print(f"No student found with NUid {nuid}. Profile not updated.")

## Getter functions ##

def get_student_completed_courses(student_data):
    courses = student_data['completed_courses'].iloc[0]

    if courses:
        return courses
    else:
        return []
    
def get_student_core_subjects(student_data):
    core_subjects = student_data['core_subjects'].iloc[0]

    if core_subjects:
        core_subjects = [s.strip() for s in core_subjects if s.strip()]
        return core_subjects
    else:
        return []

def get_subject(subjects_df, subject_code):
    '''
    Get subject data for a given subject code
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find
    Return:
        specific subject data or none if not found
    '''
    subject_rows = subjects_df[subjects_df['subject_id'] == subject_code]
    return subject_rows.iloc[0] if not subject_rows.empty else None

def get_subject_name(subjects_df, subject_code):
    '''
    Get subject data for a given subject code
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find
    Return:
        subject name for a subject code
    '''
    subject_row = subjects_df.loc[subjects_df['subject_id'] == subject_code, 'subject_name']
    if not subject_row.empty:
        return subject_row.iloc[0]  # Return the subject name
    else:
        return 'Unknown Course'

def get_subject_requirements(subjects_df, subject_code):
    '''
    Get math/programming requirements for a subject
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find
    Return:
        math/programming requirements for a specific subject
    '''
    subject = get_subject(subjects_df, subject_code)
    
    # If no subject
    if subject is None:
        return [], []
    
    programming_reqs = subject.get('programming_knowledge_needed', [])
    math_reqs = subject.get('math_requirements', [])

    return programming_reqs, math_reqs

def get_subject_prerequisites(subjects_df, subject_code):
    '''
    Get prerequisites for a given subject
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find    
    Return:
        prereqs for a given subject
    '''
    subject = get_subject(subjects_df, subject_code)
    
    # If no subject
    if subject is None:
        return []
    
    prereq_str = subject.get('prerequisite', [])
    return prereq_str

def get_subject_outcomes(subjects_df, subject_code):
    '''
    Get learning outcomes for a subject
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find
    Return:
        subject outcomes
    '''
    subject = get_subject(subjects_df, subject_code)

    # if no subject
    if subject is None:
        return set()
        
    outcomes = subject.get('course_outcomes', [])
        
    return outcomes

def get_unmet_prerequisites(subjects_df, subject_code, taken):
    '''
    Get unmet prerequisites for a subject
    Params:
        subjects_df: all subject data
        subject_code: subject wanting to find
        taken: courses have taken
    Return:
        courses that haven't taken
    '''
    prereqs = set(get_subject_prerequisites(subjects_df, subject_code))
    return prereqs - taken

def get_utility_score(subject_code, scores_df):
    # Find the course in the database
    if 'courses' in scores_df.iloc[0]:
        courses = scores_df.iloc[0]['courses']
        for course in courses:
            if course['subject_id'] == subject_code:
                utility = course.get('utility')
                if utility is not None:
                    return utility
    return 0

def get_burnout_score(subject_code, scores_df):
    if 'courses' in scores_df.iloc[0]:
        courses = scores_df.iloc[0]['courses']
        for course in courses:
            if course['subject_id'] == subject_code:
                burnout_score = course.get('burnout_score')
                if burnout_score is not None:
                    return burnout_score
    return 0

def get_student_desired_outcomes(student_data):
    interests = student_data['desired_outcomes'].iloc[0]

    if interests:
        return interests
    else:
        return []

def prereq_satisfied(student_data, prereqs):
    '''
    Check if a student has satisfied all prerequisites for a subject.
    Params:
        student_data: given student data
        prereqs: prereqs for a given subject
    Return:
        boolean if prereq met or not
    '''
    if student_data is None or student_data.empty:
        return False
    
    # all completed courses
    completed_courses = student_data.iloc[0]['completed_courses']

    # No prerequisites, boolean is True
    if not prereqs or len(prereqs) == 0:
        return True    
        
    # Check if all prerequisites are in completed courses
    return all(prereq in completed_courses for prereq in prereqs)


if __name__ == "__main__":
    subjects_df = load_course_data()

    # Test get_subject_name function
    print("Testing get_subject_name:")
    subject_code_1 = "CS5100"
    subject_code_2 = "CS100"
    subject_code_3 = "CS7800"
    
    print(f"Subject name for {subject_code_1}: {get_subject_name(subjects_df, subject_code_1)}")
    print(f"Subject name for {subject_code_2}: {get_subject_name(subjects_df, subject_code_2)}")
    print(f"Subject name for {subject_code_3}: {get_subject_name(subjects_df, subject_code_3)}")  # Should return "Unknown Course"
    print("\n")

    # Test get_subject_requirements function
    print("Testing get_subject_requirements:")
    programming_reqs, math_reqs = get_subject_requirements(subjects_df, subject_code_1)
    print(f"Programming requirements for {subject_code_1}: {programming_reqs}")
    print(f"Math requirements for {subject_code_1}: {math_reqs}")
    print("\n")

    # Test get_subject_prerequisites function
    print("Testing get_subject_prerequisites:")
    prereqs = get_subject_prerequisites(subjects_df, subject_code_3)
    print(f"Prerequisites for {subject_code_3}: {prereqs}")
    print("\n")

    # Test get_subject_outcomes function
    print("Testing get_subject_outcomes:")
    outcomes = get_subject_outcomes(subjects_df, subject_code_1)
    print(f"Outcomes for {subject_code_1}: {outcomes}")
    print("\n")

    # Test get_unmet_prerequisites function
    print("Testing get_unmet_prerequisites:")
    completed_courses = {"CS100"}
    unmet_prereqs = get_unmet_prerequisites(subjects_df, subject_code_3, completed_courses)
    print(f"Unmet prerequisites for {subject_code_1} given completed courses {completed_courses}: {unmet_prereqs}")
    print("\n")

    # Test prereq_satisfied function
    print("Testing prereq_satisfied:")
    student_data = pd.DataFrame([{
        "NUID": "123456",
        "completed_courses": ["CS001", "CS800"]
    }])
    prereq_met = prereq_satisfied(student_data, prereqs)
    print(f"Has the student satisfied all prerequisites for {subject_code_3}? {prereq_met}")
    print("\n")

    # Test for empty completed courses (student hasn't completed any courses)
    empty_completed_courses = pd.DataFrame([{
        "NUID": "123457",
        "completed_courses": []
    }])
    prereq_met_empty = prereq_satisfied(empty_completed_courses, [])
    print(f"Has the student satisfied all prerequisites for {subject_code_3} with empty courses? {prereq_met_empty}")
    print("\n")

    # Test student completed_courses
    print("Testing student data extraction\n")
    student_id = '444'

    student_data = load_student_data(student_id)

    programming_skills = student_data['programming_experience'].iloc[0]
    math_skills = student_data['math_experience'].iloc[0]
    print(programming_skills, math_skills)

    completed = get_student_completed_courses(student_data)
    print(f"The completed courses for the student is {completed}\n")

    core_subjects = get_student_core_subjects(student_data)
    print(f"The core_subjects for student {core_subjects}")

    # Test update_knowledge_profile function
    print("\nTesting update_knowledge_profile with sequential updates:")

    # Step 1: Initial state
    print("\n===== INITIAL STATE =====")
    initial_completed = student_data["completed_courses"].iloc[0].copy()
    initial_programming = student_data["programming_experience"].iloc[0].copy()
    initial_math = student_data["math_experience"].iloc[0].copy()
    print("Initially completed courses:", initial_completed)
    print("Initial programming skills:", initial_programming)
    print("Initial math skills:", initial_math)

    # Step 2: First semester accepted
    print("\n===== AFTER FIRST SEMESTER ACCEPTANCE =====")
    # First semester courses
    first_semester = ["CS5100", "CS5800"]
    print("First semester courses accepted:", first_semester)

    # Update taken courses
    taken_courses = student_data.get("completed_courses", [])
    taken_courses.update(first_semester)

    # Update knowledge profile
    programming_skills, math_skills = update_knowledge_profile(student_data, taken_courses)

    # Display updated skills
    print("Updated programming skills:", programming_skills)
    print("Updated math skills:", math_skills)

    # Show what changed
    print("\nSkills changed after first semester:")
    for skill, value in programming_skills.items():
        initial_value = initial_programming.get(skill, 0)
        print(f"  {skill}: {initial_value} -> {value}")

    for skill, value in math_skills.items():
        initial_value = initial_math.get(skill, 0)
        print(f"  {skill}: {initial_value} -> {value}")