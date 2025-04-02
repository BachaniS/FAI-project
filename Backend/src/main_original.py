import numpy as np
import random
import json
from typing import List, Dict, Set, Tuple
from pymongo import MongoClient
from StudentDataCollector import StudentDataCollector
import burnout_calculator

# MongoDB Connection
MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
client = MongoClient(MONGO_URI)

class CourseRecommender:
    def __init__(self):
        try:
            # MongoDB connections
            self.db = client["subject_details"]
            self.courses_collection = self.db["courses"]
            self.outcomes_collection = self.db["outcomes"]
            self.prereqs_collection = self.db["prerequisites"]
            
            print("Loading course data into memory...")
            
            # Get all subjects and their data
            self.subjects_data = {}
            for doc in self.courses_collection.find():
                self.subjects_data[doc['subject_id']] = {
                    'name': doc.get('name', 'Unknown Course'),
                    'difficulty': doc.get('difficulty', 5),
                    'workload': doc.get('workload', 5),
                    'outcomes': [],
                    'prereqs': set()
                }
            
            # Load prerequisites
            for doc in self.prereqs_collection.find():
                subject_id = doc['subject_id']
                if subject_id in self.subjects_data:
                    self.subjects_data[subject_id]['prereqs'].add(doc['prereq_subject_id'])
            
            # Load outcomes
            for doc in self.outcomes_collection.find():
                subject_id = doc['subject_id']
                if subject_id in self.subjects_data:
                    self.subjects_data[subject_id]['outcomes'].append(doc['outcome'].lower())
            
            self.all_subjects = list(self.subjects_data.keys())
            if not self.all_subjects:
                raise ValueError("No subjects found in database")
            
            print(f"Loaded {len(self.all_subjects)} subjects")
            print(f"Sample subjects: {', '.join(sorted(self.all_subjects)[:10])}")
            
            # Planning parameters
            self.SEMESTERS = 4
            self.COURSES_PER_SEMESTER = 2
            self.blacklist = set()
            
        except Exception as e:
            print(f"Error initializing CourseRecommender: {str(e)}")
            raise

    def get_student_data(self) -> Dict:
        """Get or create student data from MongoDB."""
        nuid = input("Enter your NUid: ").strip()
        try:
            print("\nAttempting to load existing student data...")
            self.student_data = self.load_existing_student_data(nuid)
            
            # Clean up core subjects
            if 'core_subjects' in self.student_data:
                core_subjects = [s.strip() for s in self.student_data['core_subjects'].split(',') if s.strip()]
                self.student_data['core_subjects'] = ','.join(core_subjects)
            
            print("Successfully loaded existing student data")
            print(f"Core subjects: {self.student_data.get('core_subjects', 'None')}")
            print(f"Completed courses: {list(self.student_data.get('completed_courses', {}).keys())}")
            return self.student_data
        except Exception as e:
            print(f"\nNo existing data found: {str(e)}")
            print("Creating new student profile...")
            collector = StudentDataCollector()
            self.student_data = collector.collect_student_data()
            return self.student_data

    def load_existing_student_data(self, nuid: str) -> Dict:
        """Load existing student data from MongoDB."""
        users_collection = client["user_details"]["users"]
        student_data = users_collection.find_one({"NUID": nuid})
        if not student_data:
            raise Exception("Student not found")
            
        # Validate required fields
        required_fields = ['NUID', 'core_subjects', 'completed_courses', 'desired_outcomes']
        missing_fields = [field for field in required_fields if field not in student_data]
        if missing_fields:
            print(f"Warning: Missing fields in student data: {missing_fields}")
            # Initialize missing fields with defaults
            if 'completed_courses' not in student_data:
                student_data['completed_courses'] = {}
            if 'core_subjects' not in student_data:
                student_data['core_subjects'] = ''
            if 'desired_outcomes' not in student_data:
                student_data['desired_outcomes'] = ''
                
        return student_data

    def calculate_burnout(self, course: str) -> float:
        """Calculate burnout score for a course."""
        course_data = self.subjects_data[course]
        difficulty = course_data['difficulty']
        workload = course_data['workload']
        
        prog_exp = self.student_data['programming_experience']
        math_exp = self.student_data['math_experience']
        
        burnout = (difficulty * (10 - prog_exp) + workload * (10 - math_exp)) / 20
        return max(1, min(10, burnout))

    def get_available_courses(self, taken_courses: Set[str]) -> List[str]:
        """Get list of available courses that meet prerequisites."""
        available = []
        for course in self.all_subjects:
            if (course not in taken_courses and 
                course not in self.blacklist and 
                all(p in taken_courses for p in self.subjects_data[course]['prereqs'])):
                available.append(course)
        return available

    def score_course(self, course: str, desired_outcomes: Set[str], taken_courses: Set[str]) -> float:
        """Score a course based on burnout and outcomes."""
        burnout = self.calculate_burnout(course)
        course_outcomes = set(self.subjects_data[course]['outcomes'])
        outcome_match = len(desired_outcomes & course_outcomes)
        return outcome_match * 5 - burnout

    def plan_semester(self, taken_courses: Set[str], semester_num: int) -> List[str]:
        """Plan a single semester by selecting best available courses."""
        available_courses = self.get_available_courses(taken_courses)
        if len(available_courses) < self.COURSES_PER_SEMESTER:
            raise ValueError(f"Not enough available courses for semester {semester_num}")
        
        desired_outcomes = set(self.student_data['desired_outcomes'].lower().split(','))
        
        # Score all available courses
        course_scores = [(course, self.score_course(course, desired_outcomes, taken_courses)) 
                        for course in available_courses]
        
        # Sort by score and take the best courses
        course_scores.sort(key=lambda x: x[1], reverse=True)
        selected_courses = [course for course, _ in course_scores[:self.COURSES_PER_SEMESTER]]
        
        return selected_courses

    def generate_course_plan(self) -> None:
        """Generate course plan semester by semester."""
        taken_courses = set(self.student_data['completed_courses'].keys())
        plan = [[] for _ in range(self.SEMESTERS)]
        
        for semester in range(self.SEMESTERS):
            while True:
                try:
                    print(f"\nPlanning Semester {semester + 1}...")
                    semester_courses = self.plan_semester(taken_courses, semester + 1)
                    self.display_semester(semester + 1, semester_courses)
                    
                    response = input("\nAre you satisfied with this semester? (yes/no): ").lower()
                    if response == 'yes':
                        plan[semester] = semester_courses
                        taken_courses.update(semester_courses)
                        break
                    else:
                        remove_code = input("Enter course code to blacklist (or 'skip' to try again): ").strip()
                        if remove_code != 'skip':
                            self.blacklist.add(remove_code)
                            print(f"Added {remove_code} to blacklist")
                except Exception as e:
                    print(f"Error planning semester: {str(e)}")
                    if input("Try again? (yes/no): ").lower() != 'yes':
                        return
        
        print("\nFinal Course Plan:")
        self.display_plan(plan)

    def display_semester(self, semester_num: int, courses: List[str]) -> None:
        """Display courses for a single semester."""
        print(f"\nSemester {semester_num}:")
        for course in courses:
            course_data = self.subjects_data[course]
            name = course_data['name']
            burnout = self.calculate_burnout(course)
            print(f"  {course} - {name}")
            print(f"  Estimated Burnout: {burnout:.2f}")
            
            prereqs = course_data['prereqs']
            if prereqs:
                print(f"  Prerequisites: {', '.join(sorted(prereqs))}")

    def display_plan(self, plan: List[List[str]]) -> None:
        """Display the complete course plan."""
        print("\nComplete Course Plan:")
        print("-" * 50)
        for i, semester in enumerate(plan, 1):
            self.display_semester(i, semester)
            print("-" * 30)

    def save_plan(self, plan: List[List[str]], fitness_score: float) -> None:
        """Save the course plan."""
        try:
            subject_list = {}
            for i, semester in enumerate(plan, 1):
                for j, subject_code in enumerate(semester, 1):
                    name = self.subjects_data[subject_code]['name']
                    burnout = self.calculate_burnout(subject_code)
                    subject_list[f"Semester {i} Subject {j}"] = f"{subject_code}: {name} (Burnout: {burnout:.2f})"
            
            plan_doc = {
                'NUid': self.student_data['NUid'],
                'schedule': json.dumps(subject_list),
                'fitness_score': fitness_score
            }
            
            self.db['course_plans'].insert_one(plan_doc)
            print(f"\nPlan saved to database for student {self.student_data['NUid']}")
            
        except Exception as e:
            print(f"Error saving plan: {str(e)}")

    def debug_data(self):
        """Print debug information about loaded data."""
        print("\nDebug Information:")
        print(f"Total subjects in database: {len(self.all_subjects)}")
        print("Sample subjects:")
        print(self.all_subjects[:5])
        
        if self.student_data:
            print("\nStudent Data:")
            print(f"Core subjects: {self.student_data['core_subjects']}")
            print(f"Completed courses: {list(self.student_data['completed_courses'].keys())}")

def main():
    try:
        recommender = CourseRecommender()
        
        # Get student data
        student_data = recommender.get_student_data()
        print("\nStudent data loaded successfully!")
        
        # Debug data
        recommender.debug_data()
        
        while True:
            try:
                print("\nGenerating optimal course plan...")
                recommender.generate_course_plan()
                
                # Ask for user satisfaction
                response = input("\nAre you satisfied with this plan? (yes/no): ").lower()
                if response == 'yes':
                    recommender.save_plan(recommender.final_plan, 0)
                    print("\nCourse plan finalized and saved!")
                    break
                else:
                    print("\nEnter course codes to exclude (comma-separated, or 'skip' to try again):")
                    blacklist_input = input().strip()
                    if blacklist_input.lower() != 'skip':
                        new_blacklist = {code.strip() for code in blacklist_input.split(',')}
                        recommender.blacklist.update(new_blacklist)
                        print(f"Added {len(new_blacklist)} courses to blacklist.")
                    print("\nGenerating new plan...")
            except Exception as e:
                print(f"Error generating course plan: {str(e)}")
                print("Would you like to:")
                print("1. Try again")
                print("2. Debug data")
                print("3. Exit")
                choice = input("Enter choice (1-3): ")
                if choice == '2':
                    recommender.debug_data()
                elif choice == '3':
                    break
                continue

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 