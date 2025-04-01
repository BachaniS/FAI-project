import pandas as pd
import numpy as np
import random
import json
from load_subject_data import load_subject_data
from burnout_calculator import load_student_data, load_burnout_scores, update_knowledge_profile, calculate_burnout

subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
all_subjects = subjects_df['subject_code'].tolist()

# GA Parameters
POPULATION_SIZE = 50
GENERATIONS = 200  # More generations for better optimization
SEMESTERS = 4
COURSES_PER_SEMESTER = 2
MUTATION_RATE = 0.2  # Higher mutation for diversity
blacklist = set()
final_list = []

def initialize_population(available_subjects, core_remaining, semester_idx):
    population = []
    core_available = [c for c in core_remaining if c in available_subjects]
    for _ in range(POPULATION_SIZE):
        if core_available and random.random() < 0.5:
            core_to_schedule = min(COURSES_PER_SEMESTER, len(core_available))
            semester_core = random.sample(core_available, core_to_schedule)
            remaining_slots = COURSES_PER_SEMESTER - len(semester_core)
            semester_electives = random.sample([s for s in available_subjects if s not in semester_core], 
                                               remaining_slots) if remaining_slots > 0 else []
        else:
            semester_core = []
            semester_electives = random.sample(available_subjects, COURSES_PER_SEMESTER)
        semester = semester_core + semester_electives
        population.append(semester)
    return population

def calculate_fitness(semester, taken, student_data, knowledge, core_remaining):
    total_burnout = 0
    prereq_penalty = 0
    outcome_score = 0
    core_penalty = 0
    desired = set(student_data["desired_outcomes"].split(","))
    for subject_code in semester:
        burnout = calculate_burnout(student_data, subject_code, taken, knowledge)
        total_burnout += burnout
        prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
        unmet_prereqs = prereqs - taken
        prereq_penalty += len(unmet_prereqs) * 10
        subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
        overlap = len(desired & subject_outcomes)
        outcome_score += overlap
    core_scheduled = sum(1 for c in semester if c in core_remaining)
    core_penalty = (len(core_remaining) - core_scheduled) * 50
    return -total_burnout - prereq_penalty + outcome_score - core_penalty

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

def genetic_algorithm(available_subjects, taken, student_data, knowledge, core_remaining, semester_idx):
    population = initialize_population(available_subjects, core_remaining, semester_idx)
    for generation in range(GENERATIONS):
        fitness_scores = [calculate_fitness(semester, taken, student_data, knowledge, core_remaining) for semester in population]
        new_population = [population[np.argmax(fitness_scores)]]
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population, fitness_scores)
            parent2 = selection(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutation(child1)
            child2 = mutation(child2)
            new_population.extend([child1, child2])
        population = new_population[:POPULATION_SIZE]
        if generation % 10 == 0:
            print(f"Generation {generation}: Best Fitness = {max(fitness_scores)}")
    fitness_scores = [calculate_fitness(semester, taken, student_data, knowledge, core_remaining) for semester in population]
    return population[np.argmax(fitness_scores)]

def calculate_total_burnout(plan, student_data, initial_taken, initial_knowledge):
    total_burnout = 0
    current_taken = initial_taken.copy()
    current_knowledge = initial_knowledge.copy()
    for semester in plan:
        if semester:
            for subject_code in semester:
                burnout = calculate_burnout(student_data, subject_code, current_taken, current_knowledge)
                total_burnout += burnout
                current_taken.add(subject_code)
                current_knowledge = update_knowledge_profile(student_data, current_taken)
    return total_burnout

def optimize_schedule(plan, student_data, initial_taken, initial_knowledge):
    flat_plan = [course for semester in plan for course in semester if semester]
    best_plan = plan.copy()
    best_burnout = calculate_total_burnout(best_plan, student_data, initial_taken, initial_knowledge)
    
    for _ in range(20):
        shuffled_plan = random.sample(flat_plan, len(flat_plan))
        new_plan = [[] for _ in range(SEMESTERS)]
        for i, course in enumerate(shuffled_plan):
            semester_idx = i // COURSES_PER_SEMESTER
            new_plan[semester_idx].append(course)
        
        total_burnout = calculate_total_burnout(new_plan, student_data, initial_taken, initial_knowledge)
        if total_burnout < best_burnout:
            best_burnout = total_burnout
            best_plan = new_plan.copy()
    
    return best_plan, best_burnout

def display_plan(plan, student_data, taken, knowledge):
    print("\nCurrent 4-Semester Course Plan:")
    current_taken = taken.copy()
    current_knowledge = knowledge.copy()
    for i, semester in enumerate(plan, 1):
        if semester:
            print(f"Semester {i}:")
            for subject_code in semester:
                burnout = calculate_burnout(student_data, subject_code, current_taken, current_knowledge)
                name = subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0]
                print(f"  {subject_code} - {name}: Burnout Score = {burnout:.3f}")
                current_taken.add(subject_code)
                current_knowledge = update_knowledge_profile(student_data, current_taken)

def save_plan_to_csv(plan, nuid, fitness_score, student_data, taken, knowledge):
    subject_list = {}
    current_taken = taken.copy()
    current_knowledge = knowledge.copy()
    for i, semester in enumerate(plan, 1):
        if semester:
            for j, subject_code in enumerate(semester, 1):
                burnout = calculate_burnout(student_data, subject_code, current_taken, current_knowledge)
                name = subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0]
                subject_list[f"Semester {i} Subject {j}"] = f"{subject_code}: {name} (Burnout: {burnout:.3f})"
                current_taken.add(subject_code)
                current_knowledge = update_knowledge_profile(student_data, current_taken)
    
    schedule_df = pd.DataFrame([{'NUid': nuid, 'schedule': json.dumps(subject_list), 'fitness_score': fitness_score}])
    schedule_df.to_csv(f'course_plan_{nuid}.csv', index=False)
    print(f"\nPlan saved to course_plan_{nuid}.csv")

def rerun_genetic_algorithm(final_subjects, student_data, initial_taken, initial_knowledge):
    print("\nRerunning GA on finalized subjects...")
    population = []
    core_subjects = ['CS5010', 'CS5800']
    for _ in range(POPULATION_SIZE):
        shuffled = random.sample(final_subjects, len(final_subjects))
        # Ensure CS5010 and CS5800 are in different semesters
        while True:
            plan = [shuffled[i:i+COURSES_PER_SEMESTER] for i in range(0, len(shuffled), COURSES_PER_SEMESTER)]
            semesters_with_cores = [i for i, sem in enumerate(plan) if any(c in sem for c in core_subjects)]
            if len(semesters_with_cores) >= 2 or not all(c in final_subjects for c in core_subjects):
                break
            shuffled = random.sample(final_subjects, len(final_subjects))
    
        population.append(plan)
    
    for generation in range(GENERATIONS):
        fitness_scores = [calculate_total_burnout(plan, student_data, initial_taken, initial_knowledge) for plan in population]
        new_population = [population[np.argmin(fitness_scores)]]
        while len(new_population) < POPULATION_SIZE:
            parent1 = selection(population, [-score for score in fitness_scores])
            parent2 = selection(population, [-score for score in fitness_scores])
            child1_flat = parent1[0] + parent1[1] + parent1[2] + parent1[3]
            child2_flat = parent2[0] + parent2[1] + parent2[2] + parent2[3]
            crossover_point = random.randint(1, len(child1_flat) - 1)
            child1_new = child1_flat[:crossover_point] + [c for c in child2_flat if c not in child1_flat[:crossover_point]]
            child2_new = child2_flat[:crossover_point] + [c for c in child1_flat if c not in child2_flat[:crossover_point]]
            child1_plan = [child1_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child1_new), COURSES_PER_SEMESTER)]
            child2_plan = [child2_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child2_new), COURSES_PER_SEMESTER)]
            # Mutation with core split enforcement
            if random.random() < MUTATION_RATE:
                idx1, idx2 = random.sample(range(len(child1_new)), 2)
                child1_new[idx1], child1_new[idx2] = child1_new[idx2], child1_new[idx1]
                child1_plan = [child1_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child1_new), COURSES_PER_SEMESTER)]
                while any(all(c in sem for c in core_subjects) for sem in child1_plan):
                    idx1, idx2 = random.sample(range(len(child1_new)), 2)
                    child1_new[idx1], child1_new[idx2] = child1_new[idx2], child1_new[idx1]
                    child1_plan = [child1_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child1_new), COURSES_PER_SEMESTER)]
            if random.random() < MUTATION_RATE:
                idx1, idx2 = random.sample(range(len(child2_new)), 2)
                child2_new[idx1], child2_new[idx2] = child2_new[idx2], child2_new[idx1]
                child2_plan = [child2_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child2_new), COURSES_PER_SEMESTER)]
                while any(all(c in sem for c in core_subjects) for sem in child2_plan):
                    idx1, idx2 = random.sample(range(len(child2_new)), 2)
                    child2_new[idx1], child2_new[idx2] = child2_new[idx2], child2_new[idx1]
                    child2_plan = [child2_new[i:i+COURSES_PER_SEMESTER] for i in range(0, len(child2_new), COURSES_PER_SEMESTER)]
            new_population.extend([child1_plan, child2_plan])
        population = new_population[:POPULATION_SIZE]
        if generation % 10 == 0:
            print(f"Generation {generation}: Best Burnout = {min(fitness_scores):.3f}")
    
    fitness_scores = [calculate_total_burnout(plan, student_data, initial_taken, initial_knowledge) for plan in population]
    best_plan = population[np.argmin(fitness_scores)]
    return best_plan, min(fitness_scores)

def main():
    global blacklist, final_list
    
    nuid = input("Enter your NUid to load existing student data: ")
    student_data = load_student_data(nuid)
    burnout_scores = load_burnout_scores(nuid)
    core_subjects = student_data["core_subjects"].split(",")
    core_remaining = core_subjects.copy()
    
    plan = [[] for _ in range(SEMESTERS)]
    taken = set(student_data["completed_courses"].keys())
    knowledge = update_knowledge_profile(student_data, taken)
    final_fitness = 0
    
    for sem_idx in range(SEMESTERS):
        available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
        if len(available_subjects) < COURSES_PER_SEMESTER:
            print(f"Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
            break
        
        print(f"\nPlanning Semester {sem_idx + 1}...")
        while True:
            best_semester = genetic_algorithm(available_subjects, taken, student_data, knowledge, core_remaining, sem_idx)
            plan[sem_idx] = best_semester
            display_plan(plan, student_data, taken, knowledge)
            fitness = calculate_fitness(best_semester, taken, student_data, knowledge, core_remaining)
            final_fitness += fitness
            satisfied = input(f"\nAre you satisfied with Semester {sem_idx + 1}? (yes/no): ").lower()
            if satisfied == "yes":
                final_list.extend(best_semester)
                taken.update(best_semester)
                knowledge = update_knowledge_profile(student_data, taken)
                core_remaining = [c for c in core_remaining if c not in best_semester]
                break
            elif satisfied == "no":
                remove_code = input("Enter the subject code to remove (e.g., CS5520): ")
                if remove_code in best_semester:
                    blacklist.add(remove_code)
                    print(f"{remove_code} added to blacklist. Re-planning Semester {sem_idx + 1}...")
                    available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
                else:
                    print("Subject not in this semester. Try again.")
            else:
                print("Please enter 'yes' or 'no'.")
    
    if core_remaining:
        print(f"Warning: Core subjects {core_remaining} were not scheduled!")
    
    print("\nOptimizing initial schedule...")
    optimized_plan, total_burnout = optimize_schedule(plan, student_data, taken, knowledge)
    plan = optimized_plan
    print(f"Initial Optimized Total Burnout: {total_burnout:.3f}")
    
    print("\nInitial 4-Semester Plan Confirmed!")
    display_plan(plan, student_data, taken, knowledge)
    
    final_subjects = final_list.copy()
    best_plan, best_burnout = rerun_genetic_algorithm(final_subjects, student_data, set(student_data["completed_courses"].keys()), update_knowledge_profile(student_data, set(student_data["completed_courses"].keys())))
    
    print(f"\nFinal Optimized Total Burnout: {best_burnout:.3f}")
    print("\nFinal 4-Semester Plan After GA Rerun!")
    display_plan(best_plan, student_data, set(student_data["completed_courses"].keys()), update_knowledge_profile(student_data, set(student_data["completed_courses"].keys())))
    save_plan_to_csv(best_plan, nuid, -best_burnout, student_data, set(student_data["completed_courses"].keys()), update_knowledge_profile(student_data, set(student_data["completed_courses"].keys())))

if __name__ == "__main__":
    main()