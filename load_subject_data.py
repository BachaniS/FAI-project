import pandas as pd
from typing import Tuple, List, Set
from burnout_calculator import calculate_burnout

def load_subject_data():
    """Load and process subject data from CSV file."""
    try:
        df = pd.read_csv('subject_analysis.csv')
        
        # Basic validation
        required_columns = [
            'Subject', 'Subject Names', 'Weekly Workload (hours)', 
            'Assignments #', 'Hours per Assignment', 'Assignment Weight',
            'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade',
            'Exam #', 'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade',
            'Course Outcomes', 'Prerequisite', 'Corequisite', 'Seats', 'Enrollments'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and process subjects data
        subjects_df = df[['Subject', 'Subject Names', 'Weekly Workload (hours)', 
                         'Assignments #', 'Hours per Assignment', 'Assignment Weight',
                         'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade',
                         'Exam #', 'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade',
                         'Seats', 'Enrollments']]
        
        subjects_df = subjects_df.rename(columns={
            'Subject': 'subject_code',
            'Subject Names': 'name',
            'Weekly Workload (hours)': 'hours_per_week',
            'Assignments #': 'num_assignments',
            'Hours per Assignment': 'hours_per_assignment',
            'Assignment Weight': 'assignment_weight',
            'Avg Assignment Grade': 'avg_assignment_grade',
            'Project Weight': 'project_weight',
            'Avg Project Grade': 'avg_project_grade',
            'Exam #': 'exam_count',
            'Avg Exam Grade': 'avg_exam_grade',
            'Exam Weight': 'exam_weight',
            'Avg Final Grade': 'avg_final_grade',
            'Seats': 'seats',
            'Enrollments': 'enrollments'
        })
        
        # Process outcomes
        outcomes = []
        for _, row in df.iterrows():
            if pd.notna(row['Course Outcomes']) and isinstance(row['Course Outcomes'], str):
                for outcome in row['Course Outcomes'].split(','):
                    outcomes.append({
                        'subject_code': row['Subject'],
                        'outcome': outcome.strip()
                    })
        outcomes_df = pd.DataFrame(outcomes)
        
        # Process prerequisites
        prereqs = df[df['Prerequisite'].notna() & (df['Prerequisite'] != 'None')]
        prereqs = prereqs[['Subject', 'Prerequisite']].rename(columns={
            'Subject': 'subject_code',
            'Prerequisite': 'prereq_subject_code'
        })
        
        # Process corequisites
        coreqs = df[df['Corequisite'].notna() & (df['Corequisite'] != 'None')]
        coreqs = coreqs[['Subject', 'Corequisite']].rename(columns={
            'Subject': 'subject_code',
            'Corequisite': 'coreq_subject_code'
        })
        
        return subjects_df, outcomes_df, prereqs, coreqs
    
    except FileNotFoundError:
        raise FileNotFoundError("subject_analysis.csv not found. Please ensure the file exists in the current directory.")
    except Exception as e:
        raise Exception(f"Error loading subject data: {str(e)}")

def check_seat_availability(self, subject_code: str) -> Tuple[bool, float]:
    """
    Check seat availability for a course.
    Returns: (is_difficult_to_enroll, enrollment_percentage)
    """
    subject_data = self.subjects_df[self.subjects_df['subject_code'] == subject_code].iloc[0]
    seats = subject_data['seats']
    enrollments = subject_data['enrollments']
    
    if seats == 0:  # Prevent division by zero
        return True, 100.0
        
    enrollment_percentage = (enrollments / seats) * 100
    
    # Consider a course hard to get if:
    # 1. Enrollments are >= 90% of seats
    # 2. Or enrollments exceed seats
    is_difficult = enrollment_percentage >= 90 or enrollments >= seats
    
    return is_difficult, enrollment_percentage

def display_plan(self, plan: List[List[str]]) -> None:
    """Display the course plan with details including seat availability."""
    print("\nProposed Course Plan:")
    print("-" * 50)
    for i, semester in enumerate(plan, 1):
        print(f"\nSemester {i}:")
        for course in semester:
            # Get course details
            name = self.subjects_df[self.subjects_df['subject_code'] == course]['name'].iloc[0]
            burnout = calculate_burnout(self.student_data, course, 
                                     self.subjects_df, self.prereqs_df, self.outcomes_df)
            
            # Check seat availability
            is_difficult, enrollment_percentage = self.check_seat_availability(course)
            
            # Display course information
            print(f"  {course} - {name}")
            print(f"  Estimated Burnout: {burnout:.2f}")
            
            # Display enrollment warning if applicable
            if is_difficult:
                print(f"  ⚠️ WARNING: This course may be difficult to enroll in")
                print(f"  Current enrollment: {enrollment_percentage:.1f}% of capacity")
            
            # Get subject details for additional information
            subject_data = self.subjects_df[self.subjects_df['subject_code'] == course].iloc[0]
            print(f"  Seats: {int(subject_data['Seats'])} | Current Enrollments: {int(subject_data['Enrollments'])}")
        print("-" * 30)

def calculate_fitness(self, plan: List[List[str]], taken: Set[str]) -> float:
    """Calculate fitness score for a course plan."""
    if not self.is_valid_plan(plan, self.student_data['core_subjects'].split(',')):
        return float('-inf')
        
    total_fitness = 0
    current_taken = taken.copy()
    desired_outcomes = set(self.student_data['desired_outcomes'].lower().split(','))
    
    for semester in plan:
        semester_burnout = 0
        outcome_bonus = 0
        workload_balance = 0
        enrollment_penalty = 0
        
        # Calculate semester metrics
        for course in semester:
            # Burnout score
            burnout = calculate_burnout(self.student_data, course, 
                                     self.subjects_df, self.prereqs_df, self.outcomes_df)
            semester_burnout += burnout
            
            # Outcome matching
            course_outcomes = set(self.outcomes_df[
                self.outcomes_df['subject_code'] == course]['outcome'].str.lower())
            outcome_bonus += len(desired_outcomes & course_outcomes) * 5
            
            # Enrollment difficulty penalty
            is_difficult, enrollment_percentage = self.check_seat_availability(course)
            if is_difficult:
                enrollment_penalty += (enrollment_percentage - 90) * 0.5  # Adjust penalty weight as needed
            
            # Track taken courses
            current_taken.add(course)
        
        # Balance penalty for high burnout in a semester
        if semester_burnout > 10:
            workload_balance -= (semester_burnout - 10) * 2
        
        total_fitness += outcome_bonus - semester_burnout + workload_balance - enrollment_penalty
    
    return total_fitness

if __name__ == "__main__":
    try:
        subjects_df, outcomes_df, prereqs, coreqs = load_subject_data()
        print("Subject data loaded successfully!")
        
        # Save processed data for verification
        subjects_df.to_csv('processed_subjects.csv', index=False)
        outcomes_df.to_csv('processed_outcomes.csv', index=False)
        prereqs.to_csv('processed_prereqs.csv', index=False)
        coreqs.to_csv('processed_coreqs.csv', index=False)
        
        print("Processed data saved to CSV files for verification.")
    except Exception as e:
        print(f"Error: {str(e)}")