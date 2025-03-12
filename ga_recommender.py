import pandas as pd
import random
from deap import base, creator, tools, algorithms
import json
import numpy as np

def load_subject_data():
    df = pd.read_csv('subject_analysis.csv')
    subjects_df = df[['Subject', 'Subject Names', 'Weekly Workload (hours)', 'Assignments #', 'Hours per Assignment', 
                      'Assignment Weight', 'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade', 'Exam #', 
                      'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade']].rename(columns={
        'Subject': 'subject_code', 'Subject Names': 'name', 'Weekly Workload (hours)': 'hours_per_week', 
        'Assignments #': 'num_assignments', 'Hours per Assignment': 'hours_per_assignment', 
        'Assignment Weight': 'assignment_weight', 'Avg Assignment Grade': 'avg_assignment_grade', 
        'Project Weight': 'project_weight', 'Avg Project Grade': 'avg_project_grade', 'Exam #': 'exam_count', 
        'Avg Exam Grade': 'avg_exam_grade', 'Exam Weight': 'exam_weight', 'Avg Final Grade': 'avg_final_grade'
    })
    for col in ['hours_per_week', 'num_assignments', 'hours_per_assignment', 'assignment_weight', 
                'avg_assignment_grade', 'project_weight', 'avg_project_grade', 'exam_count', 
                'avg_exam_grade', 'exam_weight', 'avg_final_grade']:
        subjects_df[col] = pd.to_numeric(subjects_df[col], errors='coerce')
    outcomes = []
    for _, row in df.iterrows():
        course_outcomes = row['Course Outcomes']
        if pd.isna(course_outcomes) or not isinstance(course_outcomes, str):
            continue
        for outcome in course_outcomes.split(', '):
            outcomes.append({'subject_code': row['Subject'], 'outcome': outcome.strip()})
    outcomes_df = pd.DataFrame(outcomes)
    prereqs = df[df['Prerequisite'] != 'None'][['Subject', 'Prerequisite']].rename(columns={
        'Subject': 'subject_code', 'Prerequisite': 'prereq_subject_code'
    }).dropna()
    coreqs = df[df['Corequisite'] != 'None'][['Subject', 'Corequisite']].rename(columns={
        'Subject': 'subject_code', 'Corequisite': 'coreq_subject_code'
    }).dropna()
    return subjects_df, outcomes_df, prereqs, coreqs

def calculate_alignment(student_data, subject_code, outcomes_df):
    desired = set(student_data['desired_outcomes'].split(','))
    subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
    overlap = len(desired & subject_outcomes) / len(desired) if desired else 0
    return overlap

def evaluate_schedule(individual, subjects, nuid, subjects_df, scores_df, prereqs_df, coreqs_df, student_data, outcomes_df):
    schedule_subjects = [subjects[i] for i in individual]
    taken = set(student_data['completed_courses'])

    violations = 0
    scheduled = set()
    for idx, subj in enumerate(schedule_subjects):
        scheduled.add(subj)
        prereqs = set(prereqs_df[prereqs_df['subject_code'] == subj]['prereq_subject_code'])
        prior_scheduled = taken.union(set(schedule_subjects[:idx]))
        if prereqs and not prereqs.issubset(prior_scheduled):
            violations += len(prereqs - prior_scheduled)
            print(f"Violation: {subj} needs prereqs {prereqs - prior_scheduled} before it")
        coreqs = set(coreqs_df[coreqs_df['subject_code'] == subj]['coreq_subject_code'])
        if coreqs and not coreqs.issubset(scheduled):
            violations += len(coreqs - scheduled)
            print(f"Coreq Violation: {subj} needs {coreqs - scheduled}")

    if violations > 0:
        return -10000 * violations,

    total_burnout = sum(scores_df[scores_df['subject_code'] == s]['burnout_score'].iloc[0] for s in schedule_subjects)
    total_hours = sum(subjects_df[subjects_df['subject_code'] == s]['hours_per_week'].iloc[0] for s in schedule_subjects)
    excess_hours = max(0, total_hours - (20 * ((len(schedule_subjects) + 1) // 2)))
    desired = set(student_data['desired_outcomes'].split(','))
    total_alignment = sum(len(desired & set(outcomes_df[outcomes_df['subject_code'] == s]['outcome'])) / len(desired) 
                          for s in schedule_subjects)

    return -total_burnout - 10 * excess_hours + 15 * total_alignment,

def generate_schedule(nuid, subjects_df, scores_df, student_data, outcomes_df, prereqs_df, coreqs_df, all_subjects, num_subjects):
    if len(all_subjects) < num_subjects:
        raise ValueError(f"Cannot schedule {num_subjects} subjects; only {len(all_subjects)} available: {all_subjects}")

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("indices", random.sample, range(len(all_subjects)), num_subjects)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate_schedule, subjects=all_subjects, nuid=nuid, subjects_df=subjects_df, 
                     scores_df=scores_df, prereqs_df=prereqs_df, coreqs_df=coreqs_df, 
                     student_data=student_data, outcomes_df=outcomes_df)
    toolbox.register("mate", tools.cxPartialyMatched)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=100)
    algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.2, ngen=100, verbose=False)

    best = tools.selBest(pop, 1)[0]
    schedule = [all_subjects[i] for i in best]
    return schedule, best.fitness.values[0]

def get_all_prereqs(subject, prereqs_df, subjects_df, collected=None):
    if collected is None:
        collected = set()
    prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject]['prereq_subject_code'])
    for prereq in prereqs:
        if prereq not in collected and prereq in subjects_df['subject_code'].values:
            collected.add(prereq)
            get_all_prereqs(prereq, prereqs_df, subjects_df, collected)
    return collected

def get_all_coreqs(subject, coreqs_df, subjects_df, collected=None):
    if collected is None:
        collected = set()
    coreqs = set(coreqs_df[coreqs_df['subject_code'] == subject]['coreq_subject_code'])
    for coreq in coreqs:
        if coreq not in collected and coreq in subjects_df['subject_code'].values:
            collected.add(coreq)
            get_all_coreqs(coreq, coreqs_df, subjects_df, collected)
    return collected

def recommend_schedule(nuid):
    subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
    scores_df = pd.read_csv(f'burnout_scores_{nuid}.csv')
    student_df = pd.read_csv(f'student_{nuid}.csv')
    student_data = {
        'NUid': student_df['NUid'].iloc[0],
        'completed_courses': set(str(student_df['completed_courses'].iloc[0]).split(',') if pd.notna(student_df['completed_courses'].iloc[0]) and str(student_df['completed_courses'].iloc[0]).strip() else []),
        'core_subjects': student_df['core_subjects'].iloc[0],
        'desired_outcomes': student_df['desired_outcomes'].iloc[0]
    }

    core_subjects = student_data['core_subjects'].split(',')
    completed = student_data['completed_courses']
    print(f"Completed courses: {completed}")
    available_subjects = [s for s in subjects_df['subject_code'].tolist() if s not in completed]
    
    remaining_core = [s for s in core_subjects if s not in completed]
    total_subjects_needed = 8
    num_completed = len([c for c in completed if c])
    num_to_schedule = total_subjects_needed - num_completed
    print(f"Num completed: {num_completed}, Num to schedule: {num_to_schedule}")

    alignment_scores = {s: calculate_alignment(student_data, s, outcomes_df) for s in available_subjects}
    print("Alignment Scores:", alignment_scores)
    sorted_subjects = sorted(available_subjects, key=lambda x: alignment_scores[x], reverse=True)
    
    # Core subjects and all dependencies
    required_subjects = set(remaining_core)
    for subj in remaining_core:
        required_subjects.update(get_all_prereqs(subj, prereqs_df, subjects_df))
        required_subjects.update(get_all_coreqs(subj, coreqs_df, subjects_df))
    required_subjects = [s for s in required_subjects if s in subjects_df['subject_code'].values]
    print(f"Required subjects (core + prereqs + coreqs): {required_subjects}")

    # Viable subjects: alignment > 0, all prereqs/coreqs in required_subjects or completed
    viable_subjects = []
    for s in sorted_subjects:
        prereqs = get_all_prereqs(s, prereqs_df, subjects_df)
        coreqs = get_all_coreqs(s, coreqs_df, subjects_df)
        if (alignment_scores[s] > 0 and 
            all(p in required_subjects or p in completed for p in prereqs) and 
            all(c in required_subjects or c in completed for c in coreqs)):
            viable_subjects.append(s)
        elif s in required_subjects:  # Ensure core subjects with dependencies are viable if possible
            viable_subjects.append(s)
    print(f"Viable subjects (alignment > 0 or required, prereqs/coreqs satisfied): {viable_subjects}")
    
    # Build all_subjects: required + priority aligned subjects
    all_subjects = required_subjects.copy()
    remaining_slots = num_to_schedule - len(all_subjects)
    priority_subjects = [s for s in viable_subjects if s not in all_subjects][:remaining_slots]
    all_subjects.extend(priority_subjects)

    # Fill remaining slots with feasible subjects
    if len(all_subjects) < num_to_schedule:
        extra_subjects = [s for s in sorted_subjects if s not in all_subjects and 
                          all(p in all_subjects or p in completed for p in get_all_prereqs(s, prereqs_df, subjects_df)) and 
                          all(c in all_subjects or c in completed for c in get_all_coreqs(s, coreqs_df, subjects_df))][:num_to_schedule - len(all_subjects)]
        all_subjects.extend(extra_subjects)
    
    print(f"Final all_subjects: {all_subjects} (Length: {len(all_subjects)})")

    while True:
        schedule, fitness_score = generate_schedule(nuid, subjects_df, scores_df, student_data, outcomes_df, prereqs_df, coreqs_df, all_subjects, num_to_schedule)
        print(f"Generated schedule codes: {schedule}")

        subject_list = {}
        for i, subj in enumerate(schedule, 1):
            subj_df = subjects_df[subjects_df['subject_code'] == subj]
            name = subj_df['name'].iloc[0] if not subj_df.empty else "Unknown Course"
            subject_list[f"Subject {i}"] = f"{subj}: {name}"

        print("\nProposed Schedule:")
        for key, value in subject_list.items():
            print(f"{key}: {value}")
        print(f"Completed Courses: {list(completed)}")
        print(f"Fitness Score: {fitness_score}")

        satisfied = input("Are you satisfied with this schedule? (yes/no): ").strip().lower()
        if satisfied == 'yes':
            schedule_df = pd.DataFrame([{
                'NUid': nuid,
                'schedule': json.dumps(subject_list),
                'fitness_score': fitness_score
            }])
            schedule_df.to_csv(f'schedule_{nuid}.csv', index=False)
            print(f"Final schedule saved to schedule_{nuid}.csv")
            break
        else:
            remove_subjects = input("Which subjects do you want to remove? (Enter subject codes separated by commas): ").strip()
            remove_list = [s.strip() for s in remove_subjects.split(',') if s.strip()]
            kept_subjects = [s for s in schedule if s not in remove_list]
            print(f"Keeping subjects: {kept_subjects}, Need to fill: {num_to_schedule - len(kept_subjects)} slots")

            prereq_set = set(kept_subjects)
            for subj in kept_subjects:
                prereq_set.update(get_all_prereqs(subj, prereqs_df, subjects_df))
                prereq_set.update(get_all_coreqs(subj, coreqs_df, subjects_df))
            all_subjects = list(set([s for s in prereq_set if s in subjects_df['subject_code'].values]))
            remaining_slots = num_to_schedule - len(all_subjects)
            additional_subjects = [s for s in sorted_subjects if s not in all_subjects and 
                                   all(p in all_subjects or p in completed for p in get_all_prereqs(s, prereqs_df, subjects_df)) and 
                                   all(c in all_subjects or c in completed for c in get_all_coreqs(s, coreqs_df, subjects_df))][:remaining_slots]
            all_subjects.extend(additional_subjects)
            print(f"Updated all_subjects: {all_subjects} (Length: {len(all_subjects)})")

def recommend_schedule_with_feedback(nuid):
    recommend_schedule(nuid)

if __name__ == "__main__":
    nuid = input("Enter NUid to recommend schedule: ")
    recommend_schedule_with_feedback(nuid)