import numpy as np
import random
from utils import (
    load_course_data, save_schedules, get_subject_name, get_unmet_prerequisites, load_student_data, update_knowledge_profile, save_knowledge_profile,
    get_student_completed_courses, get_student_core_subjects
)
from burnout_calculator import (
    calculate_burnout, calculate_outcome_alignment_score
)

# GA Parameters
POPULATION_SIZE = 30
GENERATIONS = 100
SEMESTERS = 2
COURSES_PER_SEMESTER = 2
MUTATION_RATE = 0.2
blacklist = set()
final_list = []

def initialize_population(available_subjects, core_remaining):
    '''
    Initialize a population of possible semester schedules
    
    Args:
        available_subjects: List of available subjects to choose from
        core_remaining: List of remaining core subjects that need to be scheduled
        
    Returns:
        List of semester schedules
    '''
    population = []
    core_available = [c for c in core_remaining if c in available_subjects]
    
    for _ in range(POPULATION_SIZE):
        if core_available and random.random() < 0.5:
            # Prioritize scheduling core subjects
            core_to_schedule = min(COURSES_PER_SEMESTER, len(core_available))
            semester_core = random.sample(core_available, core_to_schedule)
            remaining_slots = COURSES_PER_SEMESTER - len(semester_core)
            
            # Fill remaining slots with electives
            semester_electives = []
            if remaining_slots > 0:
                available_electives = [s for s in available_subjects if s not in semester_core]
                if available_electives:
                    semester_electives = random.sample(available_electives, remaining_slots)
        else:
            # Just schedule regular courses
            semester_core = []
            semester_electives = random.sample(available_subjects, COURSES_PER_SEMESTER)
            
        semester = semester_core + semester_electives
        population.append(semester)
        
    return population

def calculate_fitness(semester, taken, student_data, core_remaining):
    '''
    Calculate fitness score for a semester schedule
    
    Args:
        semester: List of courses for the semester
        taken: Set of already completed courses
        student_data: Student profile data
        core_remaining: List of remaining core subjects
        
    Returns:
        Fitness score (higher is better)
    '''
    subjects_df = load_course_data()
    
    # Initialize scores
    total_burnout = 0
    prereq_penalty = 0
    outcome_score = 0
    core_penalty = 0
    
    for subject_id in semester:
        # Calculate burnout for this subject
        burnout = calculate_burnout(student_data, subject_id, subjects_df)
        total_burnout += burnout
        
        # Calculate outcome alignment
        outcome_alignment = calculate_outcome_alignment_score(student_data, subject_id, subjects_df)
        outcome_score += outcome_alignment

        # Calculate prerequisite penalty
        unmet_prereqs = get_unmet_prerequisites(subjects_df, subject_id, taken)
        prereq_penalty += len(unmet_prereqs) * 10
    
    # Calculate core course penalty
    core_scheduled = sum(1 for c in semester if c in core_remaining)
    core_courses_left = len(core_remaining) - core_scheduled
    core_penalty = core_courses_left * 5  # Lower weight to allow flexibility
    
    # Calculate final fitness (higher is better)
    return outcome_score - total_burnout - prereq_penalty - core_penalty

def selection(population, fitness_scores):
    '''
    Select a schedule from the population using tournament selection
    
    Args:
        population: List of semester schedules
        fitness_scores: List of fitness scores for each schedule
        
    Returns:
        Selected schedule
    '''
    tournament_size = 3
    tournament_indices = random.sample(range(len(population)), tournament_size)
    tournament = [(population[i], fitness_scores[i]) for i in tournament_indices]
    return max(tournament, key=lambda x: x[1])[0]

def crossover(parent1, parent2):
    '''
    Perform crossover between two parent schedules
    
    Args:
        parent1: First parent schedule
        parent2: Second parent schedule
        
    Returns:
        Two child schedules
    '''
    all_subjects = load_course_data()['subject_id'].tolist()
    
    # Create children starting with subset of each parent
    crossover_point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:crossover_point]
    child2 = parent2[:crossover_point]
    
    # Add courses from other parent that aren't already in child
    for course in parent2:
        if course not in child1:
            child1.append(course)
            if len(child1) == COURSES_PER_SEMESTER:
                break
                
    for course in parent1:
        if course not in child2:
            child2.append(course)
            if len(child2) == COURSES_PER_SEMESTER:
                break
    
    # If children still need courses, add from available pool
    available = [c for c in all_subjects if c not in blacklist and c not in final_list]
    
    while len(child1) < COURSES_PER_SEMESTER:
        available_for_child1 = [c for c in available if c not in child1]
        if not available_for_child1:
            break  # No more courses available
        child1.append(random.choice(available_for_child1))
        
    while len(child2) < COURSES_PER_SEMESTER:
        available_for_child2 = [c for c in available if c not in child2]
        if not available_for_child2:
            break  # No more courses available
        child2.append(random.choice(available_for_child2))
    
    return child1, child2

def mutation(semester):
    '''
    Perform mutation on a schedule
    
    Args:
        semester: Schedule to mutate
        
    Returns:
        Mutated schedule
    '''
    all_subjects = load_course_data()['subject_id'].tolist()
    
    if random.random() < MUTATION_RATE:
        idx = random.randint(0, len(semester) - 1)
        available = [c for c in all_subjects if c not in blacklist and c not in final_list and c not in semester]
        if available:
            semester[idx] = random.choice(available)
    
    return semester

def genetic_algorithm(available_subjects, taken, student_data, core_remaining):
    '''
    Run the genetic algorithm to find the best semester schedule
    
    Args:
        available_subjects: List of available subjects
        taken: Set of completed courses
        student_data: Student profile data
        core_remaining: List of remaining core subjects
        
    Returns:
        Best semester schedule
    '''
    taken = set(taken)
    core_remaining = list(core_remaining)
    # Initialize population
    population = initialize_population(available_subjects, core_remaining)
    
    # Track the best schedule found
    best_fitness = float('-inf')
    best_schedule = None
    
    # Stopping condition parameters
    max_stall_generations = 20     # Stop if no improvement for this many generations
    function_tolerance = 1e-6      # Relative change tolerance for stopping
    stall_counter = 0
    fitness_history = []
    
    # Run for specified number of generations
    for generation in range(GENERATIONS):
        # Calculate fitness for each schedule
        fitness_scores = [calculate_fitness(semester, taken, student_data, core_remaining) for semester in population]
        
        # Keep track of the best schedule
        gen_best_idx = np.argmax(fitness_scores)
        gen_best_fitness = fitness_scores[gen_best_idx]
        
        # Check if we found a better solution
        if gen_best_fitness > best_fitness:
            best_fitness = gen_best_fitness
            best_schedule = population[gen_best_idx]
            stall_counter = 0  # Reset stall counter
        else:
            stall_counter += 1  # Increment stall counter
            
        # Update fitness history for function tolerance check
        fitness_history.append(gen_best_fitness)
        if len(fitness_history) > max_stall_generations:
            fitness_history.pop(0)  # Remove oldest entry
            
        # Check MaxStallGenerations stopping condition
        if stall_counter >= max_stall_generations:
            print(f"Stopping early: No improvement for {max_stall_generations} generations")
            break
            
        # Check FunctionTolerance stopping condition
        if len(fitness_history) >= max_stall_generations:
            avg_fitness = sum(fitness_history) / len(fitness_history)
            if avg_fitness != 0:  # Avoid division by zero
                relative_change = abs(fitness_history[-1] - fitness_history[0]) / abs(avg_fitness)
                if relative_change < function_tolerance:
                    print(f"Stopping early: Relative change in fitness below tolerance ({relative_change:.8f} < {function_tolerance})")
                    break
        
        # Create new population with elitism (keep the best)
        new_population = [population[gen_best_idx]]
        
        # Fill rest of population with children from crossover and mutation
        while len(new_population) < POPULATION_SIZE:
            # Select parents
            parent1 = selection(population, fitness_scores)
            parent2 = selection(population, fitness_scores)
            
            # Create children through crossover
            child1, child2 = crossover(parent1, parent2)
            
            # Apply mutation
            child1 = mutation(child1)
            child2 = mutation(child2)
            
            # Add to new population
            new_population.extend([child1, child2])
        
        # Replace old population (keeping population size the same)
        population = new_population[:POPULATION_SIZE]
        
        # Log progress occasionally
        if generation % 20 == 0:
            print(f"Generation {generation}: Best Fitness = {best_fitness}")
    
    return best_schedule

def rerun_genetic_algorithm(final_subjects, student_data, initial_taken):
    '''
    Re-run the genetic algorithm on the final list of selected subjects to optimize ordering
    
    Args:
        final_subjects: List of selected subjects
        student_data: Student profile data
        initial_taken: Initial set of completed courses
        
    Returns:
        Optimized plan and burnout score
    '''
    print("\nRe-optimizing course order to minimize burnout...")
    
    population = []
    # Identify core subjects for special handling
    core_subjects = list(get_student_core_subjects(student_data))
    final_subjects = list(final_subjects)
    initial_taken = set(initial_taken)
    
    # Stopping condition parameters
    max_stall_generations = 20     # Stop if no improvement for this many generations
    function_tolerance = 1e-6      # Relative change tolerance for stopping
    stall_counter = 0
    fitness_history = []
    best_fitness = float('-inf')
    best_plan = None
    
    # Create initial population of different course orderings
    for _ in range(POPULATION_SIZE):
        # Shuffle the subjects
        shuffled = random.sample(final_subjects, len(final_subjects))
        
        # Make sure core subjects aren't scheduled in the same semester if possible
        while True:
            # Distribute into semesters
            plan = []
            for i in range(0, len(shuffled), COURSES_PER_SEMESTER):
                semester = shuffled[i:i+COURSES_PER_SEMESTER]
                plan.append(semester)
                
            # Check if core subjects are in the same semester
            cores_in_same_semester = False
            for semester in plan:
                core_count = sum(1 for course in semester if course in core_subjects)
                if core_count > 1:
                    cores_in_same_semester = True
                    break
                    
            # If no cores in same semester or can't avoid it, use this plan
            if not cores_in_same_semester or len([c for c in final_subjects if c in core_subjects]) > SEMESTERS:
                break
                
            # Otherwise shuffle again
            shuffled = random.sample(final_subjects, len(final_subjects))
        
        population.append(plan)
    
    # Run the genetic algorithm
    for generation in range(GENERATIONS):
        # Calculate fitness (negative burnout)
        fitness_scores = [-calculate_total_burnout(plan, student_data, initial_taken) 
                         for plan in population]
        
        # Find best solution in this generation
        best_idx = np.argmax(fitness_scores)
        gen_best_fitness = fitness_scores[best_idx]
        
        # Check if we found a better solution
        if gen_best_fitness > best_fitness:
            best_fitness = gen_best_fitness
            best_plan = population[best_idx]
            stall_counter = 0  # Reset stall counter
        else:
            stall_counter += 1  # Increment stall counter
            
        # Update fitness history for function tolerance check
        fitness_history.append(gen_best_fitness)
        if len(fitness_history) > max_stall_generations:
            fitness_history.pop(0)  # Remove oldest entry
            
        # Check MaxStallGenerations stopping condition
        if stall_counter >= max_stall_generations:
            print(f"Stopping early: No improvement for {max_stall_generations} generations")
            break
            
        # Check FunctionTolerance stopping condition
        if len(fitness_history) >= max_stall_generations:
            avg_fitness = sum(fitness_history) / len(fitness_history)
            if avg_fitness != 0:  # Avoid division by zero
                relative_change = abs(fitness_history[-1] - fitness_history[0]) / abs(avg_fitness)
                if relative_change < function_tolerance:
                    print(f"Stopping early: Relative change in fitness below tolerance ({relative_change:.8f} < {function_tolerance})")
                    break
        
        # Create new population (elitism)
        new_population = [population[best_idx]]
        
        # Fill rest of population
        while len(new_population) < POPULATION_SIZE:
            # Select parents
            parent1 = selection(population, fitness_scores)
            parent2 = selection(population, fitness_scores)
            
            # Flatten parents and perform crossover
            parent1_flat = [course for semester in parent1 for course in semester]
            parent2_flat = [course for semester in parent2 for course in semester]
            
            # Single-point crossover
            crossover_point = random.randint(1, len(parent1_flat) - 1)
            child1_flat = parent1_flat[:crossover_point] + [c for c in parent2_flat if c not in parent1_flat[:crossover_point]]
            child2_flat = parent2_flat[:crossover_point] + [c for c in parent1_flat if c not in parent2_flat[:crossover_point]]
            
            # Convert back to semester structure
            child1_plan = []
            for i in range(0, len(child1_flat), COURSES_PER_SEMESTER):
                semester = child1_flat[i:i+COURSES_PER_SEMESTER]
                child1_plan.append(semester)
                
            child2_plan = []
            for i in range(0, len(child2_flat), COURSES_PER_SEMESTER):
                semester = child2_flat[i:i+COURSES_PER_SEMESTER]
                child2_plan.append(semester)
            
            # Mutation - swap two courses
            if random.random() < MUTATION_RATE:
                # Flatten, swap, and restructure
                child1_flat = [course for semester in child1_plan for course in semester]
                if len(child1_flat) > 1:  # Make sure we have at least 2 courses
                    idx1, idx2 = random.sample(range(len(child1_flat)), 2)
                    child1_flat[idx1], child1_flat[idx2] = child1_flat[idx2], child1_flat[idx1]
                    
                    child1_plan = []
                    for i in range(0, len(child1_flat), COURSES_PER_SEMESTER):
                        semester = child1_flat[i:i+COURSES_PER_SEMESTER]
                        child1_plan.append(semester)
                    
            if random.random() < MUTATION_RATE:
                # Flatten, swap, and restructure
                child2_flat = [course for semester in child2_plan for course in semester]
                if len(child2_flat) > 1:  # Make sure we have at least 2 courses
                    idx1, idx2 = random.sample(range(len(child2_flat)), 2)
                    child2_flat[idx1], child2_flat[idx2] = child2_flat[idx2], child2_flat[idx1]
                    
                    child2_plan = []
                    for i in range(0, len(child2_flat), COURSES_PER_SEMESTER):
                        semester = child2_flat[i:i+COURSES_PER_SEMESTER]
                        child2_plan.append(semester)
            
            # Add to new population
            new_population.extend([child1_plan, child2_plan])
        
        # Replace old population
        population = new_population[:POPULATION_SIZE]
        
        # Log progress
        if generation % 20 == 0:
            best_burnout = -best_fitness
            print(f"Generation {generation}: Best Burnout = {best_burnout:.3f}")
    
    # Get best solution if not already set
    if best_plan is None:
        fitness_scores = [-calculate_total_burnout(plan, student_data, initial_taken) 
                         for plan in population]
        best_plan = population[np.argmax(fitness_scores)]
    
    return best_plan, -best_fitness

def calculate_total_burnout(plan, student_data, initial_taken):
    '''
    Calculate the total burnout for an entire course plan
    
    Args:
        plan: List of semester schedules
        student_data: Student profile data
        initial_taken: Initial set of completed courses
        
    Returns:
        Total burnout score
    '''
    subjects_df = load_course_data()
    total_burnout = 0
    current_taken = set(initial_taken.copy())
    
    # Calculate burnout semester by semester
    for semester in plan:
        if semester:
            for subject_id in semester:
                # Calculate burnout for this subject
                burnout = calculate_burnout(student_data, subject_id, subjects_df)
                total_burnout += burnout
                
                # Update taken courses
                current_taken.add(subject_id)
    
    return total_burnout

def optimize_schedule(plan, student_data, initial_taken):
    '''
    Optimize the order of courses in the plan to minimize burnout
    
    Args:
        plan: Initial course plan
        student_data: Student profile data
        initial_taken: Initial set of completed courses
        
    Returns:
        Optimized plan and its burnout score
    '''
    initial_taken = set(initial_taken)
    subjects_df = load_course_data()
    
    # Flatten the plan to get all selected courses
    flat_plan = [course for semester in plan for course in semester if semester]
    
    # Start with the initial plan
    best_plan = plan.copy()
    best_burnout = calculate_total_burnout(best_plan, student_data, initial_taken)
    
    # Try different arrangements
    for _ in range(15):
        # Shuffle the courses
        shuffled_plan = random.sample(flat_plan, len(flat_plan))
        
        # Distribute into semesters
        new_plan = [[] for _ in range(SEMESTERS)]
        for i, course in enumerate(shuffled_plan):
            semester_idx = i // COURSES_PER_SEMESTER
            if semester_idx < SEMESTERS:
                new_plan[semester_idx].append(course)
        
        # Check if prerequisites are satisfied in the new order
        valid_plan = True
        current_taken = initial_taken.copy()
        
        for semester in new_plan:
            for course in semester:
                unmet_prereqs = get_unmet_prerequisites(subjects_df, course, current_taken)
                if unmet_prereqs:
                    valid_plan = False
                    break
                current_taken.add(course)
            
            if not valid_plan:
                break
        
        # If plan is valid, calculate burnout and compare to current best
        if valid_plan:
            total_burnout = calculate_total_burnout(new_plan, student_data, initial_taken)
            if total_burnout < best_burnout:
                best_burnout = total_burnout
                best_plan = new_plan.copy()
    
    return best_plan, best_burnout

def display_plan(plan, student_data, taken):
    '''
    Display the course plan with burnout scores
    
    Args:
        plan: Course plan to display
        student_data: Student profile data
        taken: Set of initially completed courses
    '''
    subjects_df = load_course_data()
    
    print("\nCurrent Course Plan:")
    
    # Fix: Ensure taken is a set, not a list
    if not isinstance(taken, set):
        current_taken = set(taken)
    else:
        current_taken = taken.copy()
    
    for i, semester in enumerate(plan, 1):
        if semester:
            print(f"Semester {i}:")
            for subject_id in semester:
                # Calculate burnout
                burnout = calculate_burnout(student_data, subject_id, subjects_df)
                
                # Get subject name
                name = get_subject_name(subjects_df, subject_id)
                
                print(f"  {subject_id} - {name}: Burnout Score = {burnout:.3f}")
                
                # Update for next subject
                current_taken.add(subject_id)

def save_plan_to_db(plan, nuid, fitness_score, student_data, taken):
    '''
    Save the course plan to the database
    
    Args:
        plan: Course plan to save
        nuid: Student ID
        fitness_score: Fitness score of the plan
        student_data: Student profile data
        taken: Set of initially completed courses
    '''
    subjects_df = load_course_data()
    schedule_data = []
    
    current_taken = taken.copy()
    
    for i, semester in enumerate(plan, 1):
        if semester:
            semester_courses = []
            for subject_id in semester:
                # Calculate burnout
                burnout = calculate_burnout(student_data, subject_id, subjects_df)
                
                # Get subject details
                name = get_subject_name(subjects_df, subject_id)
                
                # Add to semester courses
                semester_courses.append({
                    "subject_id": subject_id,
                    "subject_name": name,
                    "burnout": round(burnout, 3),
                    "fitness_score": fitness_score
                })
                
                # Update for next subject
                current_taken.add(subject_id)
            
            # Add semester to schedule
            schedule_data.append({
                "semester": i,
                "courses": semester_courses
            })
    
    # Save to database
    save_schedules(nuid, schedule_data)
    print(f"\nPlan saved to database for student {nuid}")

def main():
    global blacklist, final_list
    
    # Load student data
    nuid = input("Enter your NUid to load existing student data: ")
    student_data = load_student_data(nuid)
    
    # Ensure student_data contains the expected keys
    if 'core_subjects' not in student_data or 'completed_courses' not in student_data:
        print("Error: Student data is missing required fields.")
        return

    # Parse core subjects
    core_subjects = get_student_core_subjects(student_data)
    core_subjects = [s.strip() for s in core_subjects if s.strip()]  # Clean up any empty entries
    core_remaining = core_subjects.copy()
    
    # Initialize plan and student state
    plan = [[] for _ in range(SEMESTERS)]
    taken = set(get_student_completed_courses(student_data))
    
    # Load all available subjects
    subjects_df = load_course_data()
    all_subjects = subjects_df['subject_id'].tolist()
    
    # Plan each semester interactively
    for sem_idx in range(SEMESTERS):
        # Get available subjects that aren't blacklisted or already selected
        available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
        
        # Check if we have enough subjects to continue
        if len(available_subjects) < COURSES_PER_SEMESTER:
            print(f"Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
            break
        
        # Plan this semester
        print(f"\nPlanning Semester {sem_idx + 1}...")
        
        # Interactive loop until user is satisfied with this semester
        while True:
            # Fix: Make sure core_remaining is a list, not a set
            if not isinstance(core_remaining, list):
                core_remaining = list(core_remaining)
                
            # Run GA to get the best schedule for this semester
            best_semester = genetic_algorithm(available_subjects, taken, student_data, core_remaining)
            
            # Update the plan
            plan[sem_idx] = best_semester
            
            # Display the current plan
            display_plan(plan, student_data, taken)
            
            # Calculate fitness score
            fitness = calculate_fitness(best_semester, taken, student_data, core_remaining)
            
            # Ask user if they're satisfied or want to blacklist courses
            satisfied = input(f"\nAre you satisfied with Semester {sem_idx + 1}? (yes/no): ").lower()
            
            if satisfied == "yes":
                # Accept this semester and move on
                final_list.extend(best_semester)
                taken.update(best_semester)
                programming_skills, math_skills = update_knowledge_profile(student_data, taken)
                save_knowledge_profile(nuid, programming_skills, math_skills)
                core_remaining = [c for c in core_remaining if c not in best_semester]
                break
            elif satisfied == "no":
                # Ask which course to blacklist
                remove_code = input("Enter the subject code to remove (e.g., CS5520): ")
                if remove_code in best_semester:
                    blacklist.add(remove_code)
                    print(f"{remove_code} added to blacklist. Re-planning Semester {sem_idx + 1}...")
                    available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
                else:
                    print("Subject not in this semester. Try again.")
            else:
                print("Please enter 'yes' or 'no'.")
    
    # Check if any core subjects weren't scheduled
    if core_remaining:
        print(f"Warning: Core subjects {core_remaining} were not scheduled!")
    
    # Optimize the initial schedule
    print("\nOptimizing initial schedule...")
    optimized_plan, total_burnout = optimize_schedule(plan, student_data, taken)
    plan = optimized_plan
    print(f"Initial Optimized Total Burnout: {total_burnout:.3f}")
    
    # Show the initial optimized plan
    print("\nInitial 4-Semester Plan Confirmed!")
    display_plan(plan, student_data, taken)
    
    # Run the GA again on the entire list of selected courses to optimize ordering
    final_subjects = final_list.copy()
    initial_taken = set(student_data.get("completed_courses", {}).keys())
    
    best_plan, best_burnout = rerun_genetic_algorithm(
        final_subjects, 
        student_data, 
        initial_taken
    )
    
    # Display the final optimized plan
    print(f"\nFinal Optimized Total Burnout: {best_burnout:.3f}")
    print("\nFinal 4-Semester Plan After GA Rerun!")
    display_plan(best_plan, student_data, initial_taken)
    
    # Save the plan to the database
    save_plan_to_db(best_plan, nuid, -best_burnout, student_data, initial_taken)

if __name__ == "__main__":
    main()