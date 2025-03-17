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

        # Extract programming and math requirements
    requirements = []
    for _, row in df.iterrows():
        # Process programming requirements
        prog_reqs = row['Programming Knowledge Needed']
        if not pd.isna(prog_reqs) and isinstance(prog_reqs, str) and prog_reqs != 'None':
            for req in prog_reqs.split(', '):
                requirements.append({
                    'subject_code': row['Subject'],
                    'requirement': req.strip(),
                    'type': 'programming'
                })
        
        # Process math requirements
        math_reqs = row['Math Requirements']
        if not pd.isna(math_reqs) and isinstance(math_reqs, str) and math_reqs != 'None':
            for req in math_reqs.split(', '):
                requirements.append({
                    'subject_code': row['Subject'],
                    'requirement': req.strip(),
                    'type': 'math'
                })
    
    requirements_df = pd.DataFrame(requirements)
    print(requirements_df)


    return subjects_df, outcomes_df, prereqs, coreqs, requirements_df


def workload_factor(subject_code, subjects_df):
    '''
    Calculate workload factor W' with the following equation:
     W' = ln(1 + H/Hmax) + A/Amax + P/Pmax + E/Emax
    '''
    subject = subjects_df[subjects_df['subject_code'] == subject_code].iloc[0]

    # Calculate the max values
    Hmax = max(subjects_df['hours_per_week'].max(), 1)
    Amax = max((subjects_df['num_assignments'] * subjects_df['hours_per_assignment'] * subjects_df['assignment_weight']).max(), 1)
    Pmax = max(((100 - subjects_df['avg_project_grade']) * subjects_df['project_weight']).max(), 1)
    Emax = max((subjects_df['exam_count'] * (100 - subjects_df['avg_exam_grade']) * subjects_df['exam_weight']).max(), 1)

    # Calculate 
    H = subject['hours_per_week']
    A = subject['num_assignments'] * subject['hours_per_assignment'] * subject['assignment_weight']
    P = (100 - subject['avg_project_grade']) * subject['project_weight']
    E = subject['exam_count'] * (100 - subject['avg_exam_grade']) * subject['exam_weight']

    W_prime = np.log(1 + H/Hmax) + A/Amax + P/Pmax + E/Emax
    return W_prime

def calculate_prerequisite_mismatch_factor(student_data, subject_code, requirements_df, prereqs_df):
    '''
    Calculate modified prerequisite mismatch factor M':
    M' = (1/T) * Σ(1 - proficiency(i))
    '''
    # Get subject requirements
    subject_reqs = requirements_df[requirements_df['subject_code'] == subject_code]
    
    T = len(subject_reqs)

    # If no prereqs / requirements, then no mismatch
    if T == 0:
        return 0 
    
    sum = 0

    for _, req in subject_reqs.iterrows():
        req_type = req['type']
        req_name = req['requirement']
        
        # Check if student has proficiency in programming requirement
        if req_type == 'programming' and req_name in student_data.get('programming_experience', {}):
            proficiency = student_data['programming_experience'][req_name] / 3.0
            total_mismatch += (1 - proficiency)
        # Check if student has proficiency in math requirement
        elif req_type == 'math' and req_name in student_data.get('math_experience', {}):
            proficiency = student_data['math_experience'][req_name] / 3.0
            total_mismatch += (1 - proficiency)
        else:
            # Is not proficient
            total_mismatch += 1


    M_prime = (1/T) * (total_mismatch)

    
def calculate_stress_factor(student_data, subject_code, subjects_df):
    #TODO
    return

def course_alignment(student_data, subject_code, outcomes_df):
    '''
    Calculate outcome alignment Score
    OAS = Similarity(User Desired Outcomes, Course Outcomes)
    __
    Use Jacquard Similarity: https://www.geeksforgeeks.org/how-to-calculate-jaccard-similarity-in-python/ 
    '''
    # TODO
    return

def calculate_utility():
    '''
    Calculating utility function
    '''
    #TODO 
    return

def calculate_burnout():
    #TODO
    return

def calculate_scores(nuid):
    '''
    Calculate burnout scores for all subjects for a given student
    '''
    #TODO
    return

if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_scores(nuid)