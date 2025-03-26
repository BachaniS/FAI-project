import pandas as pd
import numpy as np
import random
import json
from load_subject_data import load_subject_data
from burnout_calculator import calculate_burnout

# Load course data
subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
all_subjects = subjects_df['subject_code'].tolist()

# GA Parameters
POPULATION_SIZE = 50
GENERATIONS = 100
SEMESTERS = 8
COURSES_PER_SEMESTER = 2
MUTATION_RATE = 0.1
blacklist = set()
final_list = []

def load_student_data(nuid):
    """Load student data from pre-existing CSV."""
    try:
        student_df = pd.read_csv(f'student_{nuid}.csv')
        student_data = {
            'NUid': student_df['NUid'].iloc[0],
            'programming_experience': student_df['programming_experience'].iloc[0],
            'math_experience': student_df['math_experience'].iloc[0],
            'completed_courses': json.loads(student_df['completed_courses_details'].iloc[0]),
            'core_subjects': student_df['core_subjects'].iloc[0],
            'desired_outcomes': student_df['desired_outcomes'].iloc[0]
        }
        return student_data
    except FileNotFoundError:
        print(f"Error: student_{nuid}.csv not found. Please run student_input.py first.")
        exit(1)

def load_burnout_scores(nuid):
    """Load precomputed burnout scores if available."""
    try:
        scores_df = pd.read_csv(f'burnout_scores_{nuid}.csv')
        return {row['subject_code']: row['burnout_score'] for _, row in scores_df.iterrows()}
    except FileNotFoundError:
        return None

def initialize_population(available_subjects):
    population = []
    for _ in range(POPULATION_SIZE):
        semester = random.sample(available_subjects, COURSES_PER_SEMESTER)
        population.append(semester)
    return population

def calculate_fitness(semester, taken, student_data, burnout_scores=None):
    total_burnout = 0
    prereq_penalty = 0
    outcome_score = 0
    
    desired = set(student_data["desired_outcomes"].split(","))
    for subject_code in semester:
        # Use precomputed burnout scores if available, otherwise calculate
        if burnout_scores and subject_code in burnout_scores:
            burnout = burnout_scores[subject_code]
        else:
            burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
        total_burnout += burnout
        prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
        unmet_prereqs = prereqs - taken
        prereq_penalty += len(unmet_prereqs) * 10
        subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
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

def genetic_algorithm(available_subjects, taken, student_data, burnout_scores):
    population = initialize_population(available_subjects)
    for generation in range(GENERATIONS):
        fitness_scores = [calculate_fitness(semester, taken, student_data, burnout_scores) for semester in population]
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
    fitness_scores = [calculate_fitness(semester, taken, student_data, burnout_scores) for semester in population]
    best_semester = population[np.argmax(fitness_scores)]
    return best_semester

def display_plan(plan):
    print("\nCurrent 8-Semester Course Plan:")
    for i, semester in enumerate(plan, 1):
        print(f"Semester {i}:")
        for subject_code in semester:
            burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
            name = subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0]
            print(f"  {subject_code} - {name}: Burnout Score = {burnout:.3f}")

def save_plan_to_csv(plan, nuid, fitness_score):
    """Save the plan in a format similar to the example."""
    subject_list = {}
    for i, semester in enumerate(plan, 1):
        for j, subject_code in enumerate(semester, 1):
            burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
            name = subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0]
            subject_list[f"Semester {i} Subject {j}"] = f"{subject_code}: {name} (Burnout: {burnout:.3f})"
    
    schedule_df = pd.DataFrame([{
        'NUid': nuid,
        'schedule': json.dumps(subject_list),
        'fitness_score': fitness_score
    }])
    schedule_df.to_csv(f'course_plan_{nuid}.csv', index=False)
    print(f"\nPlan saved to course_plan_{nuid}.csv")

def main():
    global blacklist, final_list, student_data
    
    nuid = input("Enter your NUid to load existing student data: ")
    student_data = load_student_data(nuid)
    burnout_scores = load_burnout_scores(nuid)  # Optional precomputed scores
    
    plan = [[] for _ in range(SEMESTERS)]
    taken = set(student_data["completed_courses"].keys())
    final_fitness = 0
    
    for sem_idx in range(SEMESTERS):
        while True:
            available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
            if len(available_subjects) < COURSES_PER_SEMESTER:
                print(f"Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
                display_plan(plan)
                save_plan_to_csv(plan, nuid, final_fitness)
                return
            
            print(f"\nPlanning Semester {sem_idx + 1}...")
            best_semester = genetic_algorithm(available_subjects, taken, student_data, burnout_scores)
            plan[sem_idx] = best_semester
            display_plan(plan)
            
            # Calculate fitness for display and final score
            fitness = calculate_fitness(best_semester, taken, student_data, burnout_scores)
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
    save_plan_to_csv(plan, nuid, final_fitness)

if __name__ == "__main__":
    main()