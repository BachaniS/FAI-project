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
TOTAL_COURSES = SEMESTERS * COURSES_PER_SEMESTER  # 16 courses total
blacklist = set()

def load_student_data(nuid):
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
        print(f"Loaded student data: {student_data}")
        return student_data
    except FileNotFoundError:
        print(f"Error: student_{nuid}.csv not found. Please run student_input.py first.")
        exit(1)

def load_burnout_scores(nuid):
    try:
        scores_df = pd.read_csv(f'burnout_scores_{nuid}.csv')
        return {row['subject_code']: row['burnout_score'] for _, row in scores_df.iterrows()}
    except FileNotFoundError:
        return None

def initialize_population(available_subjects, core_subjects):
    population = []
    non_core_options = [s for s in available_subjects if s not in core_subjects]
    
    for _ in range(POPULATION_SIZE):
        plan = [[] for _ in range(SEMESTERS)]
        # Pre-allocate core subjects
        for i, core in enumerate(core_subjects):
            plan[i].append(core)
        # Fill remaining slots in core semesters
        remaining = random.sample(non_core_options, TOTAL_COURSES - len(core_subjects))
        for i in range(len(core_subjects)):
            plan[i].append(remaining.pop())
        # Fill remaining semesters
        for i in range(len(core_subjects), SEMESTERS):
            plan[i] = [remaining.pop() for _ in range(COURSES_PER_SEMESTER)]
        population.append(plan)
    return population

def calculate_fitness(plan, taken, student_data, burnout_scores=None):
    total_burnout = 0
    prereq_penalty = 0
    outcome_score = 0
    core_penalty = 0
    duplicate_penalty = 0
    
    desired = set(student_data["desired_outcomes"].split(","))
    core_subjects = set(student_data['core_subjects'].split(','))
    scheduled = set()
    all_courses = []
    
    for semester in plan:
        for subject_code in semester:
            all_courses.append(subject_code)
            scheduled.add(subject_code)
            if burnout_scores and subject_code in burnout_scores:
                burnout = burnout_scores[subject_code]
            else:
                burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
            total_burnout += burnout
            prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
            unmet_prereqs = prereqs - taken - scheduled
            prereq_penalty += len(unmet_prereqs) * 10
            subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
            overlap = len(desired & subject_outcomes)
            outcome_score += overlap
    
    missing_cores = core_subjects - scheduled
    core_penalty = len(missing_cores) * 1000
    duplicates = len(all_courses) - len(set(all_courses))
    duplicate_penalty = duplicates * 1000
    
    fitness = -total_burnout - prereq_penalty + outcome_score - core_penalty - duplicate_penalty
    return fitness

def selection(population, fitness_scores):
    tournament_size = 3
    tournament = random.sample(list(zip(population, fitness_scores)), tournament_size)
    return max(tournament, key=lambda x: x[1])[0]

def crossover(parent1, parent2, core_subjects):
    child1 = [sem[:] for sem in parent1]
    child2 = [sem[:] for sem in parent2]
    
    # Preserve core subjects in their original semesters
    for i, core in enumerate(core_subjects):
        child1[i][0] = core
        child2[i][0] = core
    
    # Crossover non-core slots
    flat_parent1 = [sem[j] for i, sem in enumerate(parent1) for j in range(len(sem)) if (j > 0 or i >= len(core_subjects))]
    flat_parent2 = [sem[j] for i, sem in enumerate(parent2) for j in range(len(sem)) if (j > 0 or i >= len(core_subjects))]
    remaining_slots = TOTAL_COURSES - len(core_subjects)
    
    point = random.randint(1, remaining_slots - 1)
    child1_flat = flat_parent1[:point] + [c for c in flat_parent2[point:] if c not in flat_parent1[:point]]
    child2_flat = flat_parent2[:point] + [c for c in flat_parent1[point:] if c not in flat_parent2[:point]]
    
    available = [c for c in all_subjects if c not in blacklist and c not in core_subjects]
    while len(child1_flat) < remaining_slots:
        new_course = random.choice([c for c in available if c not in child1_flat])
        child1_flat.append(new_course)
    while len(child2_flat) < remaining_slots:
        new_course = random.choice([c for c in available if c not in child2_flat])
        child2_flat.append(new_course)
    
    child1_flat = child1_flat[:remaining_slots]
    child2_flat = child2_flat[:remaining_slots]
    
    # Rebuild plans
    flat_idx = 0
    for i in range(SEMESTERS):
        if i < len(core_subjects):
            child1[i][1] = child1_flat[flat_idx]
            child2[i][1] = child2_flat[flat_idx]
            flat_idx += 1
        else:
            child1[i] = child1_flat[flat_idx:flat_idx + COURSES_PER_SEMESTER]
            child2[i] = child2_flat[flat_idx:flat_idx + COURSES_PER_SEMESTER]
            flat_idx += COURSES_PER_SEMESTER
    
    return child1, child2

def mutation(plan, core_subjects):
    plan_copy = [sem[:] for sem in plan]
    if random.random() < MUTATION_RATE:
        mutable_slots = [(i, j) for i in range(SEMESTERS) for j in range(COURSES_PER_SEMESTER) 
                         if (i >= len(core_subjects) or j > 0)]
        if mutable_slots:
            sem_idx, course_idx = random.choice(mutable_slots)
            available = [c for c in all_subjects if c not in blacklist and c not in [c for sem in plan_copy for c in sem]]
            if available:
                plan_copy[sem_idx][course_idx] = random.choice(available)
    return plan_copy

def genetic_algorithm(available_subjects, taken, student_data, burnout_scores, core_subjects):
    population = initialize_population(available_subjects, core_subjects)
    for generation in range(GENERATIONS):
        fitness_scores = [calculate_fitness(plan, taken, student_data, burnout_scores) for plan in population]
        new_population = []
        best_idx = np.argmax(fitness_scores)
        new_population.append(population[best_idx])
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population, fitness_scores)
            parent2 = selection(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2, core_subjects)
            child1 = mutation(child1, core_subjects)
            child2 = mutation(child2, core_subjects)
            new_population.extend([child1, child2])
        population = new_population[:POPULATION_SIZE]
        if generation % 10 == 0:
            best_fitness = max(fitness_scores)
            print(f"Generation {generation}: Best Fitness = {best_fitness}")
    fitness_scores = [calculate_fitness(plan, taken, student_data, burnout_scores) for plan in population]
    best_plan = population[np.argmax(fitness_scores)]
    return best_plan, max(fitness_scores)

def display_plan(plan):
    print("\nProposed 8-Semester Course Plan:")
    for i, semester in enumerate(plan, 1):
        print(f"Semester {i}:")
        for subject_code in semester:
            burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
            name = subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0]
            print(f"  {subject_code} - {name}: Burnout Score = {burnout:.3f}")

def save_plan_to_csv(plan, nuid, fitness_score):
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
    global blacklist, student_data
    
    nuid = input("Enter your NUid to load existing student data: ")
    student_data = load_student_data(nuid)
    burnout_scores = load_burnout_scores(nuid)
    
    core_subjects = student_data['core_subjects'].split(',')
    print(f"Core subjects to include: {core_subjects}")
    taken = set(student_data["completed_courses"].keys())
    print(f"Completed courses: {taken}")
    
    while True:
        available_subjects = [s for s in all_subjects if s not in blacklist]
        if len(available_subjects) < TOTAL_COURSES:
            print(f"Not enough subjects available ({len(available_subjects)}). Need {TOTAL_COURSES}. Stopping.")
            return
        
        for core in core_subjects:
            if core not in available_subjects:
                print(f"Core subject {core} not available. Adjust blacklist or subject data.")
                return
        
        print("\nGenerating full 8-semester plan...")
        plan, fitness_score = genetic_algorithm(available_subjects, taken, student_data, burnout_scores, core_subjects)
        display_plan(plan)
        
        satisfied = input("\nAre you satisfied with this plan? (yes/no): ").lower()
        if satisfied == "yes":
            save_plan_to_csv(plan, nuid, fitness_score)
            print("Plan finalized!")
            break
        else:
            remove_codes = input("Enter subject codes to remove (comma-separated, e.g., CS5001,CS5002): ").split(',')
            remove_codes = [code.strip() for code in remove_codes if code.strip()]
            for code in remove_codes:
                if code in [c for sem in plan for c in sem]:
                    blacklist.add(code)
                    print(f"{code} added to blacklist.")
                else:
                    print(f"{code} not in plan.")
            print("Re-generating plan with updated blacklist...")

if __name__ == "__main__":
    main()