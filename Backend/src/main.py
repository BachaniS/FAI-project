import numpy as np
import random
import json
from pymongo import MongoClient
import burnout_calculator

# MongoDB connection
client = MongoClient('mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/')
db = client["subject_details"]

# Load course data from MongoDB
def load_subject_data():
    """Load subject data from MongoDB."""
    courses_collection = db["courses"]
    outcomes_collection = db["outcomes"]
    prereqs_collection = db["prerequisites"]
    
    # Convert MongoDB data to DataFrame-like structures
    subjects_data = list(courses_collection.find())
    outcomes_data = list(outcomes_collection.find())
    prereqs_data = list(prereqs_collection.find())
    
    return subjects_data, outcomes_data, prereqs_data

# Load course data
subjects_data, outcomes_data, prereqs_data = load_subject_data()
all_subjects = [subject['subject_id'] for subject in subjects_data]

# GA Parameters
POPULATION_SIZE = 50
GENERATIONS = 100
SEMESTERS = 8
COURSES_PER_SEMESTER = 2
MUTATION_RATE = 0.1
blacklist = set()
final_list = []

def load_student_data(nuid):
    """Load student data from MongoDB."""
    try:
        students_collection = client["user_details"]["users"]
        student_doc = students_collection.find_one({"NUid": nuid})
        if not student_doc:
            raise ValueError(f"Student with NUid {nuid} not found")
            
        student_data = {
            'NUid': student_doc['NUid'],
            'programming_experience': student_doc['programming_experience'],
            'math_experience': student_doc['math_experience'],
            'completed_courses': student_doc['completed_courses'],
            'core_subjects': student_doc['core_subjects'],
            'desired_outcomes': student_doc['desired_outcomes']
        }
        return student_data
    except Exception as e:
        print(f"Error loading student data: {str(e)}")
        exit(1)

def initialize_population(available_subjects):
    population = []
    for _ in range(POPULATION_SIZE):
        semester = random.sample(available_subjects, COURSES_PER_SEMESTER)
        population.append(semester)
    return population

def calculate_fitness(semester, taken, student_data):
    total_burnout = 0
    prereq_penalty = 0
    outcome_score = 0
    
    desired = set(student_data["desired_outcomes"].split(","))
    for subject_code in semester:
        # Calculate burnout
        burnout = burnout_calculator.calculate_burnout(
            student_data, subject_code,
            db["courses"], db["prerequisites"], db["outcomes"]
        )
        total_burnout += burnout
        
        # Check prerequisites
        prereqs = {doc['prereq_subject_id'] for doc in prereqs_data if doc['subject_id'] == subject_code}
        unmet_prereqs = prereqs - taken
        prereq_penalty += len(unmet_prereqs) * 10
        
        # Check outcomes
        subject_outcomes = {doc['outcome'] for doc in outcomes_data if doc['subject_id'] == subject_code}
        overlap = len(desired & subject_outcomes)
        outcome_score += overlap
    
    fitness = -total_burnout - prereq_penalty + outcome_score
    return fitness

def selection(population, fitness_scores):
    tournament_size = 3
    tournament = random.sample(list(zip(population, fitness_scores)), tournament_size)
    return max(tournament, key=lambda x: x[1])[0]

def crossover(parent1, parent2):
    child1 = parent1[:1] + [c for c in parent2[1:] if c not in parent1[:1]]
    child2 = parent2[:1] + [c for c in parent1[1:] if c not in parent2[:1]]
    available = [c for c in all_subjects if c not in blacklist and c not in final_list]
    while len(child1) < COURSES_PER_SEMESTER:
        new_course = random.choice([c for c in available if c not in child1])
        child1.append(new_course)
    while len(child2) < COURSES_PER_SEMESTER:
        new_course = random.choice([c for c in available if c not in child2])
        child2.append(new_course)
    return child1, child2

def mutation(semester):
    if random.random() < MUTATION_RATE:
        idx = random.randint(0, COURSES_PER_SEMESTER - 1)
        available = [c for c in all_subjects if c not in blacklist and c not in final_list and c not in semester]
        if available:
            semester[idx] = random.choice(available)
    return semester

def genetic_algorithm(available_subjects, taken, student_data):
    population = initialize_population(available_subjects)
    for generation in range(GENERATIONS):
        fitness_scores = [calculate_fitness(semester, taken, student_data) for semester in population]
        new_population = []
        best_idx = np.argmax(fitness_scores)
        new_population.append(population[best_idx])
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population, fitness_scores)
            parent2 = selection(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutation(child1)
            child2 = mutation(child2)
            new_population.extend([child1, child2])
        population = new_population[:POPULATION_SIZE]
        if generation % 10 == 0:
            best_fitness = max(fitness_scores)
            print(f"Generation {generation}: Best Fitness = {best_fitness}")
    fitness_scores = [calculate_fitness(semester, taken, student_data) for semester in population]
    best_semester = population[np.argmax(fitness_scores)]
    return best_semester

def display_plan(plan):
    print("\nCurrent 8-Semester Course Plan:")
    for i, semester in enumerate(plan, 1):
        print(f"Semester {i}:")
        for subject_code in semester:
            burnout = burnout_calculator.calculate_burnout(
                student_data, subject_code,
                db["courses"], db["prerequisites"], db["outcomes"]
            )
            subject_doc = next((s for s in subjects_data if s['subject_id'] == subject_code), None)
            name = subject_doc['name'] if subject_doc else 'Unknown Course'
            print(f"  {subject_code} - {name}: Burnout Score = {burnout:.3f}")

def save_plan(plan, nuid, fitness_score):
    """Save the plan to MongoDB."""
    try:
        subject_list = {}
        for i, semester in enumerate(plan, 1):
            for j, subject_code in enumerate(semester, 1):
                burnout = burnout_calculator.calculate_burnout(
                    student_data, subject_code,
                    db["courses"], db["prerequisites"], db["outcomes"]
                )
                subject_doc = next((s for s in subjects_data if s['subject_id'] == subject_code), None)
                name = subject_doc['name'] if subject_doc else 'Unknown Course'
                subject_list[f"Semester {i} Subject {j}"] = f"{subject_code}: {name} (Burnout: {burnout:.3f})"
        
        plan_doc = {
            'NUid': nuid,
            'schedule': json.dumps(subject_list),
            'fitness_score': fitness_score
        }
        
        db['course_plans'].insert_one(plan_doc)
        print(f"\nPlan saved to database for student {nuid}")
        
    except Exception as e:
        print(f"Error saving plan: {str(e)}")

def main():
    global blacklist, final_list, student_data
    
    nuid = input("Enter your NUid to load existing student data: ")
    student_data = load_student_data(nuid)
    
    plan = [[] for _ in range(SEMESTERS)]
    taken = set(student_data["completed_courses"].keys())
    final_fitness = 0
    
    for sem_idx in range(SEMESTERS):
        while True:
            available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
            if len(available_subjects) < COURSES_PER_SEMESTER:
                print(f"Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
                display_plan(plan)
                save_plan(plan, nuid, final_fitness)
                return
            
            print(f"\nPlanning Semester {sem_idx + 1}...")
            best_semester = genetic_algorithm(available_subjects, taken, student_data)
            plan[sem_idx] = best_semester
            display_plan(plan)
            
            # Calculate fitness for display and final score
            fitness = calculate_fitness(best_semester, taken, student_data)
            final_fitness += fitness
            
            satisfied = input(f"\nAre you satisfied with Semester {sem_idx + 1}? (yes/no): ").lower()
            if satisfied == "yes":
                final_list.extend(best_semester)
                taken.update(best_semester)
                break
            else:
                remove_code = input("Enter the subject code to remove (e.g., CS5001): ")
                if remove_code in best_semester:
                    blacklist.add(remove_code)
                    print(f"{remove_code} added to blacklist. Re-planning Semester {sem_idx + 1}...")
                else:
                    print("Subject not in this semester. Try again.")
    
    print("\nFinal 8-Semester Plan Confirmed!")
    display_plan(plan)
    save_plan(plan, nuid, final_fitness)

if __name__ == "__main__":
    main()