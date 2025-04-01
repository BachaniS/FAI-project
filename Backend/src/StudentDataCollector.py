from pymongo import MongoClient
import json
from typing import Dict, List, Any

class StudentDataCollector:
    def __init__(self):
        # MongoDB Connection
        self.MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client["subject_details"]
        self.users_db = self.client["user_details"]

    def get_available_subjects(self) -> List[Dict[str, Any]]:
        """Get list of available subjects from MongoDB."""
        courses_collection = self.db["courses"]
        return list(courses_collection.find({}, {'_id': 0}))

    def collect_student_data(self) -> Dict[str, Any]:
        """Collect student information and preferences."""
        print("\nWelcome to the Course Recommender System!")
        print("Please provide the following information to help us recommend courses.\n")

        # Basic Information
        nuid = input("Enter your NUid: ").strip()
        
        # Programming Experience
        print("\nRate your programming experience (1-5):")
        print("1: No experience")
        print("2: Basic understanding")
        print("3: Some practical experience")
        print("4: Significant experience")
        print("5: Expert level")
        programming_exp = int(input("Your rating: ").strip())

        # Math Experience
        print("\nRate your mathematics experience (1-5):")
        print("1: Basic arithmetic")
        print("2: High school algebra")
        print("3: Calculus")
        print("4: Advanced calculus")
        print("5: Graduate-level mathematics")
        math_exp = int(input("Your rating: ").strip())

        # Detailed Programming Experience
        print("\nSelect your programming experience areas (comma-separated):")
        print("Available options: Python, Java, C++, JavaScript, Web Development, Mobile Development, None")
        detailed_prog = input("Your selections: ").strip()
        detailed_programming_exp = [lang.strip() for lang in detailed_prog.split(',')]

        # Detailed Math Experience
        print("\nSelect your mathematics experience areas (comma-separated):")
        print("Available options: Algebra, Calculus, Statistics, Linear Algebra, Discrete Mathematics, None")
        detailed_math = input("Your selections: ").strip()
        detailed_math_exp = [area.strip() for area in detailed_math.split(',')]

        # Get available subjects
        available_subjects = self.get_available_subjects()
        subject_ids = [subject['subject_id'] for subject in available_subjects]

        # Completed Courses
        print("\nEnter completed courses (comma-separated) or 'none':")
        print(f"Available courses: {', '.join(subject_ids)}")
        completed_input = input("Your completed courses: ").strip().lower()
        
        completed_courses = {}
        if completed_input != 'none':
            for course in completed_input.split(','):
                course = course.strip()
                if course in subject_ids:
                    grade = float(input(f"Enter your grade for {course} (0-100): ").strip())
                    completed_courses[course] = {
                        'final_grade': grade
                    }

        # Core Subjects
        print("\nEnter your core subjects (comma-separated):")
        print(f"Available subjects: {', '.join(subject_ids)}")
        core_subjects = input("Your core subjects: ").strip()

        # Desired Outcomes
        print("\nSelect desired learning outcomes (comma-separated):")
        all_outcomes = set()
        for subject in available_subjects:
            if 'course_outcomes' in subject:
                all_outcomes.update(subject['course_outcomes'])
        print(f"Available outcomes: {', '.join(sorted(all_outcomes))}")
        desired_outcomes = input("Your desired outcomes: ").strip()

        # Create student data dictionary
        student_data = {
            'NUID': nuid,
            'programming_experience': programming_exp,
            'math_experience': math_exp,
            'completed_courses': completed_courses,
            'core_subjects': core_subjects,
            'desired_outcomes': desired_outcomes,
            'detailed_programming_exp': detailed_programming_exp,
            'detailed_math_exp': detailed_math_exp
        }

        # Save to MongoDB
        self.save_student_data(student_data)
        
        return student_data

    def save_student_data(self, student_data: Dict[str, Any]) -> None:
        """Save student data to MongoDB."""
        try:
            users_collection = self.users_db["users"]
            
            # Ensure required fields exist
            if 'NUID' not in student_data:
                raise ValueError("Student data missing NUID")
                
            # Ensure proper data types
            if not isinstance(student_data.get('completed_courses', {}), dict):
                student_data['completed_courses'] = {}
            if not isinstance(student_data.get('core_subjects', ''), str):
                student_data['core_subjects'] = ','.join(student_data['core_subjects'])
            if not isinstance(student_data.get('desired_outcomes', ''), str):
                student_data['desired_outcomes'] = ','.join(student_data['desired_outcomes'])
                
            print("\nSaving student data:")
            print(f"NUID: {student_data['NUID']}")
            print(f"Core subjects: {student_data['core_subjects']}")
            print(f"Completed courses: {list(student_data['completed_courses'].keys())}")
            
            # Save to MongoDB
            result = users_collection.replace_one(
                {"NUID": student_data['NUID']},
                student_data,
                upsert=True
            )
            
            if result.matched_count > 0:
                print(f"\nUpdated existing student record for NUID: {student_data['NUID']}")
            else:
                print(f"\nCreated new student record for NUID: {student_data['NUID']}")
                
        except Exception as e:
            print(f"Error saving student data: {str(e)}")
            raise

if __name__ == "__main__":
    collector = StudentDataCollector()
    student_data = collector.collect_student_data()
    print("\nCollected Student Data:")
    print(json.dumps(student_data, indent=2))
