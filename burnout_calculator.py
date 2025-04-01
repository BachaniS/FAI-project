import pandas as pd
import numpy as np
import json
from load_subject_data import load_subject_data

subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()

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

def update_knowledge_profile(student_data, taken):
    skills = {}
    prog_exp = student_data['programming_experience'] or ""
    math_exp = student_data['math_experience'] or ""
    for skill in prog_exp.split(','):
        if skill.strip():
            skills[skill.strip()] = skills.get(skill.strip(), 0) + 1
    for skill in math_exp.split(','):
        if skill.strip():
            skills[skill.strip()] = skills.get(skill.strip(), 0) + 1
    
    for subject_code in taken:
        subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
        for outcome in subject_outcomes:
            skills[outcome] = skills.get(outcome, 0) + 1
    
    # Normalize skills based on cumulative experience
    return {k: min(v * 0.2, 1.0) for k, v in skills.items()}  # 0.2 per skill instance, cap at 1.0

def calculate_requirement_mismatch(student_data, subject_code, taken, knowledge):
    prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
    unmet_prereqs = prereqs - taken
    base_mismatch = len(unmet_prereqs) / (len(prereqs) + 1) if prereqs else 0
    if unmet_prereqs and knowledge:
        prereq_skills = set()
        for prereq in unmet_prereqs:
            prereq_outcomes = set(outcomes_df[outcomes_df['subject_code'] == prereq]['outcome'])
            prereq_skills.update(prereq_outcomes)
        bonus = sum(knowledge.get(skill, 0) for skill in prereq_skills) / (len(prereq_skills) or 1) * 0.5
        return base_mismatch * (1 - bonus)
    return base_mismatch

def calculate_outcome_mismatch(student_data, subject_code):
    desired = set(student_data['desired_outcomes'].split(','))
    subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
    overlap = len(desired & subject_outcomes) / len(desired) if desired else 0
    return 1 - overlap

def calculate_workload_factor(subject_code):
    subject = subjects_df[subjects_df['subject_code'] == subject_code].iloc[0]
    H = subject['hours_per_week']
    A = subject['num_assignments'] * subject['hours_per_assignment'] * subject['assignment_weight']
    P = (100 - subject['avg_project_grade']) * subject['project_weight'] if subject['project_weight'] > 0 else 0
    E = subject['exam_count'] * (100 - subject['avg_exam_grade']) * subject['exam_weight'] if subject['exam_weight'] > 0 else 0
    W_prime = np.log(1 + H / 10) + A / 100 + P / 100 + E / 100
    return W_prime / 10

def calculate_stress_factor(student_data, subject_code):
    subject = subjects_df[subjects_df['subject_code'] == subject_code].iloc[0]
    if subject_code in student_data['completed_courses']:
        avg_grade = student_data['completed_courses'][subject_code]['Avg Final Grade']
    else:
        avg_grade = subject['avg_final_grade']
    return ((100 - avg_grade) / 100) ** 2

def calculate_burnout(student_data, subject_code, taken, knowledge=None):
    M_req = calculate_requirement_mismatch(student_data, subject_code, taken, knowledge)
    M_out = calculate_outcome_mismatch(student_data, subject_code)
    W_prime = calculate_workload_factor(subject_code)
    S_prime = calculate_stress_factor(student_data, subject_code)
    P_prime = (M_req + M_out + W_prime + S_prime) / 4
    if knowledge:
        subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
        overlap = sum(knowledge.get(outcome, 0) for outcome in subject_outcomes)
        reduction = overlap * 0.5  # Increased to 0.5 for stronger effect
        P_prime = max(P_prime - reduction, 0)
    return 1 / (1 + np.exp(-(P_prime - 0.5)))

def calculate_scores(nuid):
    student_data = load_student_data(nuid)
    taken = set(student_data['completed_courses'].keys())
    scores = []
    for subject_code in subjects_df['subject_code']:
        burnout = calculate_burnout(student_data, subject_code, taken)
        scores.append({'subject_code': subject_code, 'burnout_score': burnout})
    
    scores_df = pd.DataFrame(scores)
    scores_df.to_csv(f'burnout_scores_{nuid}.csv', index=False)
    print(f"Burnout scores saved to burnout_scores_{nuid}.csv")

if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_scores(nuid)