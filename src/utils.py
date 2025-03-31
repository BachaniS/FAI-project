import pandas as pd
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
client = MongoClient(MONGO_URI)

## Load functions ##

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
    
    # Print diagnostic information
    # Find the document
    student_data = collection.find_one({"NUID": student_id})
    
    # Convert to DataFrame
    student_df = pd.DataFrame([student_data])
    return student_df

def load_scores(nuid):
    '''
    Load score details from DB
    '''
    db = client["user_details"]
    collection = db["user_scores"]
    student_data = collection.find_one({"NUID": nuid})
    return pd.DataFrame(student_data["courses"]) if student_data else None

def save_scores(nuid, burnout_scores):
    """
    Save burnout scores to MongoDB
    """
    try:
        db = client["user_details"]
        burnout_collection = db["user_scores"]
        
        # Prepare document
        burnout_doc = {
            "NUID": nuid,
            "courses": burnout_scores,
            "updated": pd.Timestamp.now(),
        }
        
        # Upsert document (replace if exists)
        burnout_collection.replace_one(
            {"NUID": nuid},
            burnout_doc,
            upsert=True
        )
        
        print(f"Burnout scores saved for student {nuid}")
    except Exception as e:
        print(f"Error saving burnout scores: {e}")