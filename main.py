import pandas as pd
import numpy as np
import random
import json
from typing import List, Dict, Set, Tuple
from load_subject_data import load_subject_data
from StudentDataCollector import StudentDataCollector
from burnout_calculator import calculate_burnout

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
        """Initialize population of course plans."""
        # Validate subjects exist in database
        valid_subjects = set(self.subjects_df['subject_code'].unique())
        available_subjects = [s for s in available_subjects if s in valid_subjects]
        core_subjects = [s for s in core_subjects if s in valid_subjects]
        
        if not available_subjects:
            raise ValueError("No valid subjects available")
        
        if not core_subjects:
            print("Warning: No valid core subjects found")
        
        population = []
        for _ in range(self.POPULATION_SIZE):
            plan = [[] for _ in range(self.SEMESTERS)]
            remaining_subjects = set(available_subjects) - set(core_subjects)
            
            # Place core subjects first
            for i, core in enumerate(core_subjects):
                if i < self.SEMESTERS:
                    plan[i].append(core)
            
            # Fill remaining slots
            for semester in range(self.SEMESTERS):
                while len(plan[semester]) < self.COURSES_PER_SEMESTER:
                    available = list(remaining_subjects - set([course for sem in plan for course in sem]))
                    if available:
                        course = random.choice(available)
                        plan[semester].append(course)
                    else:
                        break  # No more available courses
            
            if all(len(sem) == self.COURSES_PER_SEMESTER for sem in plan):
                population.append(plan)
        
        if not population:
            raise ValueError("Could not generate valid course plans. Not enough valid courses available.")
        
        return population

    def calculate_fitness(self, plan: List[List[str]], taken: Set[str]) -> float:
        """Calculate fitness score for a course plan."""
        total_fitness = 0
        current_taken = taken.copy()
        
        for semester in plan:
            semester_burnout = 0
            prereq_penalty = 0
            outcome_bonus = 0
            
            for course in semester:
                # Calculate burnout
                burnout = calculate_burnout(self.student_data, course, 
                                         self.subjects_df, self.prereqs_df, self.outcomes_df)
                semester_burnout += burnout
                
                # Check prerequisites
                prereqs = set(self.prereqs_df[self.prereqs_df['subject_code'] == course]['prereq_subject_code'])
                unmet_prereqs = prereqs - current_taken
                prereq_penalty += len(unmet_prereqs) * 10
                
                # Calculate outcome matching
                desired_outcomes = set(self.student_data['desired_outcomes'].split(','))
                course_outcomes = set(self.outcomes_df[self.outcomes_df['subject_code'] == course]['outcome'])
                outcome_bonus += len(desired_outcomes & course_outcomes)
            
            current_taken.update(semester)
            total_fitness += (-semester_burnout - prereq_penalty + outcome_bonus)
        
        return total_fitness

    def crossover(self, parent1: List[List[str]], parent2: List[List[str]]) -> Tuple[List[List[str]], List[List[str]]]:
        """Perform crossover between two parent plans."""
        child1 = [semester[:] for semester in parent1]
        child2 = [semester[:] for semester in parent2]
        
        if random.random() < 0.5:  # 50% chance of crossover
            crossover_point = random.randint(1, self.SEMESTERS - 1)
            child1[crossover_point:] = [semester[:] for semester in parent2[crossover_point:]]
            child2[crossover_point:] = [semester[:] for semester in parent1[crossover_point:]]
        
        return child1, child2

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
                burnout = calculate_burnout(self.student_data, course, 
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