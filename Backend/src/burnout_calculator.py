import pandas as pd
import numpy as np
import json

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

def calculate_requirement_mismatch(student_data, subject_code, prereqs_df):
    taken = set(student_data['completed_courses'].keys()) if student_data['completed_courses'] else set()
    prereqs = set(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
    unmet_prereqs = len(prereqs - taken)
    return unmet_prereqs / (len(prereqs) + 1) if prereqs else 0  # [0,1]

def calculate_outcome_mismatch(student_data, subject_code, outcomes_df):
    desired = set(student_data['desired_outcomes'].split(','))  # Use desired_outcomes
    subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
    overlap = len(desired & subject_outcomes) / len(desired) if desired else 0
    return 1 - overlap  # [0,1], lower mismatch = better alignment

def calculate_workload_factor(subject_code: str, subjects_df: pd.DataFrame) -> float:
    """Calculate workload factor for a subject."""
    # First verify the subject exists
    subject_data = subjects_df[subjects_df['subject_code'] == subject_code]
    if subject_data.empty:
        print(f"Warning: Subject {subject_code} not found in database")
        return 1.0  # Return default value
    
    subject = subject_data.iloc[0]
    
    # Calculate workload factor
    weekly_workload = subject['hours_per_week']
    num_assignments = subject['num_assignments']
    hours_per_assignment = subject['hours_per_assignment']
    
    total_workload = weekly_workload + (num_assignments * hours_per_assignment)
    
    # Normalize workload (you might want to adjust these values)
    MAX_WORKLOAD = 20  # Maximum expected weekly workload
    workload_factor = total_workload / MAX_WORKLOAD
    
    return min(max(workload_factor, 0.1), 2.0)  # Keep between 0.1 and 2.0

def calculate_stress_factor(student_data, subject_code, subjects_df):
    subject = subjects_df[subjects_df['subject_code'] == subject_code].iloc[0]
    if subject_code in student_data['completed_courses']:
        avg_grade = student_data['completed_courses'][subject_code]['Avg Final Grade']
    else:
        avg_grade = subject['avg_final_grade']
    S_prime = ((100 - avg_grade) / 100) ** 2
    return S_prime  # [0,1]

def calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df):
    M_req = calculate_requirement_mismatch(student_data, subject_code, prereqs_df)
    M_out = calculate_outcome_mismatch(student_data, subject_code, outcomes_df)
    W_prime = calculate_workload_factor(subject_code, subjects_df)
    S_prime = calculate_stress_factor(student_data, subject_code, subjects_df)
    P_prime = (M_req + M_out + W_prime + S_prime) / 4
    return 1 / (1 + np.exp(-(P_prime - 0.5)))  # [0,1]

def calculate_scores(nuid):
    subjects_df, outcomes_df, prereqs_df, _ = load_subject_data()
    student_df = pd.read_csv(f'student_{nuid}.csv')
    student_data = {
        'NUid': student_df['NUid'].iloc[0],
        'programming_experience': student_df['programming_experience'].iloc[0],
        'math_experience': student_df['math_experience'].iloc[0],
        'completed_courses': json.loads(student_df['completed_courses_details'].iloc[0]),
        'core_subjects': student_df['core_subjects'].iloc[0],
        'desired_outcomes': student_df['desired_outcomes'].iloc[0]
    }
    
    scores = []
    for subject_code in subjects_df['subject_code']:
        burnout = calculate_burnout(student_data, subject_code, subjects_df, prereqs_df, outcomes_df)
        scores.append({'subject_code': subject_code, 'burnout_score': burnout})
    
    scores_df = pd.DataFrame(scores)
    scores_df.to_csv(f'burnout_scores_{nuid}.csv', index=False)
    print(f"Burnout scores saved to burnout_scores_{nuid}.csv")

if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_scores(nuid)