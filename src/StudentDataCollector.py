import pandas as pd
import json
from typing import Dict, List

class StudentDataCollector:
    def __init__(self):
        self.PROGRAMMING_LANGUAGES = [
            "Python", "Java", "C++", "JavaScript", "C#", "R", "MATLAB",
            "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "TypeScript",
            "SQL", "Scala", "Julia", "Haskell", "Perl", "Assembly"
        ]
        
        self.MATH_AREAS = [
            "Calculus", "Linear Algebra", "Statistics", "Probability",
            "Discrete Mathematics", "Number Theory", "Graph Theory",
            "Differential Equations", "Numerical Analysis", "Real Analysis",
            "Complex Analysis", "Topology", "Abstract Algebra", "Optimization",
            "Game Theory", "Set Theory", "Logic", "Geometry", "Trigonometry",
            "Combinatorics"
        ]
    
    def display_options(self, options: List[str], title: str) -> None:
        """Display numbered list of options."""
        print(f"\n{title}")
        print("-" * 50)
        for i, option in enumerate(options, 1):
            print(f"{i:2}. {option}")
        print("-" * 50)
    
    def get_valid_rating(self, prompt: str, min_val: int = 1, max_val: int = 5) -> int:
        """Get valid rating input from user."""
        while True:
            try:
                rating = int(input(prompt))
                if min_val <= rating <= max_val:
                    return rating
                print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")
    
    def collect_student_data(self) -> Dict:
        """Collect all student information."""
        print("\nWelcome to the Course Planning System!")
        print("Please provide your information to help us create your personalized course plan.")
        
        # Basic Information
        nuid = input("\nEnter your NUid: ").strip()
        
        # Programming Experience
        self.display_options(self.PROGRAMMING_LANGUAGES, "Programming Languages")
        prog_exp = {}
        while True:
            lang = input("\nEnter a programming language (or 'done' to finish): ").strip()
            if lang.lower() == 'done':
                break
            if lang in self.PROGRAMMING_LANGUAGES:
                rating = self.get_valid_rating(f"Rate your proficiency in {lang} (1-5): ")
                prog_exp[lang] = rating
            else:
                print("Please select from the listed languages")
        
        # Math Experience
        self.display_options(self.MATH_AREAS, "Mathematics Areas")
        math_exp = {}
        while True:
            area = input("\nEnter a math area (or 'done' to finish): ").strip()
            if area.lower() == 'done':
                break
            if area in self.MATH_AREAS:
                rating = self.get_valid_rating(f"Rate your proficiency in {area} (1-5): ")
                math_exp[area] = rating
            else:
                print("Please select from the listed areas")
        
        # Completed Courses
        completed_courses = {}
        if input("\nHave you completed any courses? (yes/no): ").lower().startswith('y'):
            print("\nEnter completed courses information:")
            print("Format: COURSE_CODE,GRADE (e.g., CS5001,A)")
            while True:
                course_input = input("\nEnter course and grade (or 'done' to finish): ").strip()
                if course_input.lower() == 'done':
                    break
                try:
                    code, grade = course_input.split(',')
                    code = code.strip().upper()
                    grade = grade.strip().upper()
                    
                    completed_courses[code] = {
                        "grade": grade,
                        "rating": self.get_valid_rating(f"Rate your experience with {code} (1-5): ")
                    }
                except ValueError:
                    print("Invalid format. Please use COURSE_CODE,GRADE format")
        
        # Core Subjects and Desired Outcomes
        print("\nEnter your core subjects (required courses)")
        print("Format: comma-separated course codes (e.g., CS5001,CS5002,CS5004)")
        core_subjects = input("Core subjects: ").strip()
        
        print("\nEnter your desired learning outcomes")
        print("Format: comma-separated outcomes (e.g., machine_learning,data_science,software_engineering)")
        desired_outcomes = input("Desired outcomes: ").strip()
        
        # Calculate average experiences
        avg_prog_exp = round(sum(prog_exp.values()) / len(prog_exp)) if prog_exp else 1
        avg_math_exp = round(sum(math_exp.values()) / len(math_exp)) if math_exp else 1
        
        # Create student data dictionary
        student_data = {
            'NUid': nuid,
            'programming_experience': avg_prog_exp,
            'math_experience': avg_math_exp,
            'completed_courses': completed_courses,
            'core_subjects': core_subjects,
            'desired_outcomes': desired_outcomes,
            'detailed_programming_exp': prog_exp,
            'detailed_math_exp': math_exp
        }
        
        # Save to CSV
        self.save_student_data(student_data)
        return student_data
    
    def save_student_data(self, student_data: Dict) -> None:
        """Save student data to CSV file."""
        df = pd.DataFrame([{
            'NUid': student_data['NUid'],
            'programming_experience': student_data['programming_experience'],
            'math_experience': student_data['math_experience'],
            'completed_courses_details': json.dumps(student_data['completed_courses']),
            'core_subjects': student_data['core_subjects'],
            'desired_outcomes': student_data['desired_outcomes'],
            'detailed_programming_exp': json.dumps(student_data['detailed_programming_exp']),
            'detailed_math_exp': json.dumps(student_data['detailed_math_exp'])
        }])
        
        filename = f"student_{student_data['NUid']}.csv"
        df.to_csv(filename, index=False)
        print(f"\nStudent data saved to {filename}")

if __name__ == "__main__":
    collector = StudentDataCollector()
    student_data = collector.collect_student_data()
