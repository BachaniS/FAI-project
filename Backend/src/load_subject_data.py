from pymongo import MongoClient
import pandas as pd

def load_subject_data():
    """Load and process subject data from MongoDB."""
    try:
        # MongoDB Connection
        MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
        client = MongoClient(MONGO_URI)
        db = client["subject_details"]

        # Get collections
        courses_collection = db["courses"]
        outcomes_collection = db["outcomes"]
        prereqs_collection = db["prerequisites"]
        coreqs_collection = db["corequisites"]

        # Convert MongoDB collections to DataFrames
        # This maintains compatibility with existing code that expects DataFrames
        subjects_df = pd.DataFrame(list(courses_collection.find({}, {'_id': 0})))
        outcomes_df = pd.DataFrame(list(outcomes_collection.find({}, {'_id': 0})))
        prereqs_df = pd.DataFrame(list(prereqs_collection.find({}, {'_id': 0})))
        coreqs_df = pd.DataFrame(list(coreqs_collection.find({}, {'_id': 0})))

        # Basic validation
        if subjects_df.empty:
            raise ValueError("No subjects found in database")

        # Ensure required columns exist
        required_columns = [
            'subject_code',
            'name',
            'weekly_course_time',
            'assignment_count',
            'assignment_time',
            'assignment_weight',
            'assignment_grade',
            'project_weight',
            'project_grade',
            'exam_count',
            'exam_grade',
            'exam_weight',
            'final_grade',
            'seats',
            'enrollments'
        ]

        missing_columns = [col for col in required_columns if col not in subjects_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in subjects collection: {missing_columns}")

        return subjects_df, outcomes_df, prereqs_df, coreqs_df

    except Exception as e:
        raise Exception(f"Error loading subject data from MongoDB: {str(e)}")

if __name__ == "__main__":
    try:
        subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
        print("Subject data loaded successfully!")
        print(f"\nSubjects shape: {subjects_df.shape}")
        print(f"Outcomes shape: {outcomes_df.shape}")
        print(f"Prerequisites shape: {prereqs_df.shape}")
        print(f"Corequisites shape: {coreqs_df.shape}")
    except Exception as e:
        print(f"Error: {str(e)}") 