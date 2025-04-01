import pandas as pd
import numpy as np
import random
import json
from typing import List, Dict, Set, Tuple
from load_subject_data import load_subject_data
from StudentDataCollector import StudentDataCollector
import burnout_calculator

class CourseRecommender:
    def __init__(self):
        # Load course data
        self.subjects_df, self.outcomes_df, self.prereqs_df, self.coreqs_df = load_subject_data()
        self.all_subjects = self.subjects_df['subject_code'].tolist()
        
        # GA Parameters
        self.POPULATION_SIZE = 50
        self.GENERATIONS = 100
        self.SEMESTERS = 4
        self.COURSES_PER_SEMESTER = 2
        self.MUTATION_RATE = 0.1
        self.blacklist = set()
        self.final_list = []
        self.student_data = None

    def get_student_data(self) -> Dict:
        """Get or create student data."""
        nuid = input("Enter your NUid: ").strip()
        try:
            self.student_data = self.load_existing_student_data(nuid)
            return self.student_data
        except FileNotFoundError:
            print("No existing data found. Let's create your profile.")
            collector = StudentDataCollector()
            self.student_data = collector.collect_student_data()
            return self.student_data

    def load_existing_student_data(self, nuid: str) -> Dict:
        """Load existing student data from CSV."""
        student_df = pd.read_csv(f'student_{nuid}.csv')
        return {
            'NUid': student_df['NUid'].iloc[0],
            'programming_experience': student_df['programming_experience'].iloc[0],
            'math_experience': student_df['math_experience'].iloc[0],
            'completed_courses': json.loads(student_df['completed_courses_details'].iloc[0]),
            'core_subjects': student_df['core_subjects'].iloc[0],
            'desired_outcomes': student_df['desired_outcomes'].iloc[0],
            'detailed_programming_exp': json.loads(student_df['detailed_programming_exp'].iloc[0]),
            'detailed_math_exp': json.loads(student_df['detailed_math_exp'].iloc[0])
        }

    def initialize_population(self, available_subjects: List[str], core_subjects: List[str]) -> List[List[List[str]]]:
        """Initialize population of course plans with proper constraints."""
        population = []
        core_subjects = [s for s in core_subjects if s and s in self.all_subjects]
        
        for _ in range(self.POPULATION_SIZE):
            plan = [[] for _ in range(self.SEMESTERS)]
            used_courses = set()  # Track used courses to prevent duplicates
            
            # First, place core subjects
            for core in core_subjects:
                # Find earliest semester where prerequisites are met
                for sem_idx in range(self.SEMESTERS):
                    if self.can_take_course(core, used_courses, sem_idx, plan):
                        plan[sem_idx].append(core)
                        used_courses.add(core)
                        break
            
            # Fill remaining slots
            for sem_idx in range(self.SEMESTERS):
                while len(plan[sem_idx]) < self.COURSES_PER_SEMESTER:
                    # Get valid courses for this semester
                    valid_courses = [
                        c for c in available_subjects 
                        if c not in used_courses 
                        and c not in self.blacklist
                        and self.can_take_course(c, used_courses, sem_idx, plan)
                    ]
                    
                    if not valid_courses:
                        break
                        
                    course = random.choice(valid_courses)
                    plan[sem_idx].append(course)
                    used_courses.add(course)
            
            if self.is_valid_plan(plan, core_subjects):
                population.append(plan)
        
        return population

    def can_take_course(self, course: str, taken_courses: Set[str], semester: int, plan: List[List[str]]) -> bool:
        """Check if prerequisites are met and course can be taken."""
        # Get prerequisites for the course
        prereqs = set(self.prereqs_df[self.prereqs_df['subject_code'] == course]['prereq_subject_code'])
        
        # Calculate all courses taken before this semester
        previous_courses = taken_courses.copy()
        for i in range(semester):
            previous_courses.update(plan[i])
            
        # Check if all prerequisites are met
        return all(p in previous_courses for p in prereqs)

    def is_valid_plan(self, plan: List[List[str]], core_subjects: List[str]) -> bool:
        """Validate a course plan."""
        # Check if all core subjects are included
        planned_courses = set([c for sem in plan for c in sem])
        if not all(core in planned_courses for core in core_subjects):
            return False
            
        # Check for duplicates
        if len(planned_courses) != sum(len(sem) for sem in plan):
            return False
            
        # Check prerequisites for each semester
        taken = set()
        for sem_idx, semester in enumerate(plan):
            for course in semester:
                if not self.can_take_course(course, taken, sem_idx, plan):
                    return False
            taken.update(semester)
            
        return True

    def calculate_fitness(self, plan: List[List[str]], taken: Set[str]) -> float:
        """Calculate fitness score for a course plan."""
        if not self.is_valid_plan(plan, self.student_data['core_subjects'].split(',')):
            return float('-inf')
        
        total_fitness = 100  # Start with a base score of 100
        current_taken = taken.copy()
        desired_outcomes = set(self.student_data['desired_outcomes'].lower().split(','))
        
        for semester in plan:
            semester_burnout = 0
            outcome_bonus = 0
            workload_balance = 0
            enrollment_penalty = 0
            
            # Calculate semester metrics
            for course in semester:
                # Burnout score (scaled down to have less negative impact)
                burnout = burnout_calculator.calculate_burnout(self.student_data, course, 
                                         self.subjects_df, self.prereqs_df, self.outcomes_df)
                semester_burnout += burnout * 0.5  # Scale down burnout impact
                
                # Outcome matching (increased positive impact)
                course_outcomes = set(self.outcomes_df[
                    self.outcomes_df['subject_code'] == course]['outcome'].str.lower())
                outcome_bonus += len(desired_outcomes & course_outcomes) * 10  # Increased bonus
                
                # Seat availability penalty (scaled down)
                subject_data = self.subjects_df[self.subjects_df['subject_code'] == course].iloc[0]
                seats = subject_data['seats']
                enrollments = subject_data['enrollments']
                if seats > 0:
                    enrollment_percentage = (enrollments / seats) * 100
                    if enrollment_percentage >= 90:
                        enrollment_penalty += (enrollment_percentage - 90) * 0.2  # Reduced penalty
                
                # Track taken courses
                current_taken.add(course)
            
            # Balance penalty for high burnout (scaled down)
            if semester_burnout > 10:
                workload_balance -= (semester_burnout - 10) * 0.5
            
            # Add bonuses and subtract penalties
            semester_score = outcome_bonus - semester_burnout - enrollment_penalty + workload_balance
            total_fitness += semester_score
        
        return max(0, total_fitness)  # Ensure score doesn't go below 0

    def crossover(self, parent1: List[List[str]], parent2: List[List[str]]) -> Tuple[List[List[str]], List[List[str]]]:
        """Perform crossover while maintaining valid course sequences."""
        if random.random() < 0.7:  # 70% chance of crossover
            crossover_point = random.randint(1, self.SEMESTERS - 1)
            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]
            
            # Repair children if they're invalid
            child1 = self.repair_plan(child1)
            child2 = self.repair_plan(child2)
            
            return child1, child2
        return parent1, parent2

    def repair_plan(self, plan: List[List[str]]) -> List[List[str]]:
        """Repair an invalid course plan."""
        used_courses = set()
        new_plan = [[] for _ in range(self.SEMESTERS)]
        
        # First, try to keep courses in their original semesters if valid
        for sem_idx, semester in enumerate(plan):
            for course in semester:
                if (course not in used_courses and 
                    self.can_take_course(course, used_courses, sem_idx, new_plan)):
                    new_plan[sem_idx].append(course)
                    used_courses.add(course)
        
        # Add any missing core subjects
        core_subjects = self.student_data['core_subjects'].split(',')
        for core in core_subjects:
            if core not in used_courses:
                for sem_idx in range(self.SEMESTERS):
                    if self.can_take_course(core, used_courses, sem_idx, new_plan):
                        new_plan[sem_idx].append(core)
                        used_courses.add(core)
                        break
        
        # Fill remaining slots
        available_subjects = [s for s in self.all_subjects if s not in self.blacklist]
        for sem_idx in range(self.SEMESTERS):
            while len(new_plan[sem_idx]) < self.COURSES_PER_SEMESTER:
                valid_courses = [
                    c for c in available_subjects 
                    if c not in used_courses 
                    and self.can_take_course(c, used_courses, sem_idx, new_plan)
                ]
                if not valid_courses:
                    break
                course = random.choice(valid_courses)
                new_plan[sem_idx].append(course)
                used_courses.add(course)
        
        return new_plan

    def mutation(self, plan: List[List[str]], available_subjects: List[str]) -> List[List[str]]:
        """Perform mutation on a course plan."""
        if random.random() < self.MUTATION_RATE:
            sem1, sem2 = random.sample(range(self.SEMESTERS), 2)
            course1, course2 = random.sample(range(self.COURSES_PER_SEMESTER), 2)
            
            # Swap courses between semesters
            if len(plan[sem1]) > course1 and len(plan[sem2]) > course2:
                plan[sem1][course1], plan[sem2][course2] = plan[sem2][course2], plan[sem1][course1]
        
        return plan

    def generate_course_plan(self) -> Tuple[List[List[str]], float]:
        """Generate optimal course plan using genetic algorithm."""
        available_subjects = [s for s in self.all_subjects if s not in self.blacklist]
        core_subjects = self.student_data['core_subjects'].split(',')
        taken = set(self.student_data['completed_courses'].keys())
        
        # Initialize population
        population = self.initialize_population(available_subjects, core_subjects)
        
        # Evolution process
        for generation in range(self.GENERATIONS):
            # Calculate fitness for all plans
            fitness_scores = [self.calculate_fitness(plan, taken) for plan in population]
            
            # Select best plans
            sorted_population = [x for _, x in sorted(zip(fitness_scores, population), reverse=True)]
            new_population = sorted_population[:2]  # Keep top 2
            
            # Generate new population
            while len(new_population) < self.POPULATION_SIZE:
                parent1, parent2 = random.sample(sorted_population[:10], 2)  # Select from top 10
                child1, child2 = self.crossover(parent1, parent2)
                child1 = self.mutation(child1, available_subjects)
                child2 = self.mutation(child2, available_subjects)
                new_population.extend([child1, child2])
            
            population = new_population[:self.POPULATION_SIZE]
            
            if generation % 10 == 0:
                best_fitness = max(fitness_scores)
                print(f"Generation {generation}: Best Fitness = {best_fitness}")
        
        # Return best plan
        final_fitness_scores = [self.calculate_fitness(plan, taken) for plan in population]
        best_plan = population[np.argmax(final_fitness_scores)]
        best_fitness = max(final_fitness_scores)
        
        return best_plan, best_fitness

    def display_plan(self, plan: List[List[str]]) -> None:
        """Display the course plan with details."""
        print("\nProposed Course Plan:")
        print("-" * 50)
        for i, semester in enumerate(plan, 1):
            print(f"\nSemester {i}:")
            for course in semester:
                name = self.subjects_df[self.subjects_df['subject_code'] == course]['name'].iloc[0]
                burnout = burnout_calculator.calculate_burnout(self.student_data, course, 
                                         self.subjects_df, self.prereqs_df, self.outcomes_df)
                print(f"  {course} - {name}")
                print(f"  Estimated Burnout: {burnout:.2f}")
            print("-" * 30)

    def save_plan(self, plan: List[List[str]], fitness: float) -> None:
        """Save the course plan to CSV."""
        nuid = self.student_data['NUid']
        plan_data = {
            'NUid': nuid,
            'plan': json.dumps(plan),
            'fitness_score': fitness,
            'timestamp': pd.Timestamp.now()
        }
        
        df = pd.DataFrame([plan_data])
        df.to_csv(f'course_plan_{nuid}.csv', index=False)
        print(f"\nPlan saved to course_plan_{nuid}.csv")

    def debug_data(self):
        """Print debug information about loaded data."""
        print("\nDebug Information:")
        print(f"Total subjects in database: {len(self.subjects_df)}")
        print("Sample subjects:")
        print(self.subjects_df['subject_code'].head())
        print("\nTotal outcomes: {len(self.outcomes_df)}")
        print("\nTotal prerequisites: {len(self.prereqs_df)}")
        
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
                plan, fitness = recommender.generate_course_plan()
                
                # Display the plan
                recommender.display_plan(plan)
                
                # Ask for user satisfaction
                response = input("\nAre you satisfied with this plan? (yes/no): ").lower()
                if response == 'yes':
                    recommender.save_plan(plan, fitness)
                    print("\nCourse plan finalized and saved!")
                    break
                else:
                    # Get courses to blacklist
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