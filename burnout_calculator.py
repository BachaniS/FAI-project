import pandas as pd
import numpy as np
import json

def load_subject_data():
    df = pd.read_csv('subject_analysis.csv')
    subjects_df = df[['Subject', 'Subject Names', 'Weekly Workload (hours)', 'Assignments #', 'Hours per Assignment', 
                      'Assignment Weight', 'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade', 'Exam #', 
                      'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade', 'Seats', "Enrollments"]].rename(columns={
        'Subject': 'subject_code', 'Subject Names': 'name', 'Weekly Workload (hours)': 'hours_per_week', 
        'Assignments #': 'num_assignments', 'Hours per Assignment': 'hours_per_assignment', 
        'Assignment Weight': 'assignment_weight', 'Avg Assignment Grade': 'avg_assignment_grade', 
        'Project Weight': 'project_weight', 'Avg Project Grade': 'avg_project_grade', 'Exam #': 'exam_count', 
        'Avg Exam Grade': 'avg_exam_grade', 'Exam Weight': 'exam_weight', 'Avg Final Grade': 'avg_final_grade',
        'Seats': 'Seats', 'Enrollments': 'Enrollments',
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
    
    total_mismatch = 0

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
    return M_prime

    
def calculate_stress_factor(student_data, subject_code, subjects_df):
    subject = subjects_df[subjects_df['subject_code'] == subject_code].iloc[0]
    if subject_code in student_data['completed_courses']:
        # Use student's actual performance if available
        completed_course = student_data['completed_courses'][subject_code]
        GA = completed_course.get('Avg Assignment Grade', subject['avg_assignment_grade'])
        GE = completed_course.get('Avg Exam Grade', subject['avg_exam_grade'])
        GP = completed_course.get('Avg Project Grade', subject['avg_project_grade'])
    else:
        # Use average grades from subject data
        GA = subject['avg_assignment_grade']
        GE = subject['avg_exam_grade']
        GP = subject['avg_project_grade']

    # Get weights
    Aw = subject['assignment_weight']
    Ew = subject['exam_weight']
    Pw = subject['project_weight']

    # Calculate stress components
    total_weight = Aw + Ew + Pw
    if total_weight == 0:
        return 0
    
    stress_assignments = ((100 - GA) / 100) ** 2 * Aw
    stress_exams = ((100 - GE) / 100) ** 2 * Ew
    stress_projects = ((100 - GP) / 100) ** 2 * Pw
    
    S_prime = (stress_assignments + stress_exams + stress_projects) / total_weight
    
    return S_prime

def calculate_burnout(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df, weights=None):
    '''
    Calculate the normalized burnout probability
    P' = w1*W' + w2*M' + w3*S'
    Pfinal = 1 / (1 + e^-k(P'-P0))
    '''
    # Default weights if not provided
    if weights is None:
        weights = {
            'w1': 0.4,  # Weight for workload factor
            'w2': 0.3,  # Weight for prerequisite mismatch
            'w3': 0.3,  # Weight for stress factor
            'k': 4.0,   # Scaling factor for sigmoid
            'P0': 0.5   # Baseline burnout level
        }
    
    # Calculate individual factors
    W_prime = workload_factor(subject_code, subjects_df)
    M_prime = calculate_prerequisite_mismatch_factor(student_data, subject_code, requirements_df, prereqs_df)
    S_prime = calculate_stress_factor(student_data, subject_code, subjects_df)
    
    # Calculate combined burnout score
    P_prime = weights['w1'] * W_prime + weights['w2'] * M_prime + weights['w3'] * S_prime
    
    # Normalize to [0,1] using sigmoid function
    P_final = 1 / (1 + np.exp(-weights['k'] * (P_prime - weights['P0'])))
    
    return P_final

def calculate_scores(nuid):
    '''
    Calculate burnout scores and utility for all subjects for a given student
    '''
    subjects_df, outcomes_df, prereqs_df, coreqs_df, requirements_df = load_subject_data()
    
    try:
        student_df = pd.read_csv(f'student_{nuid}.csv')
        
        # Parse student data
        student_data = {
            'NUid': student_df['NUid'].iloc[0],
            'programming_experience': json.loads(student_df['programming_experience'].iloc[0]),
            'math_experience': json.loads(student_df['math_experience'].iloc[0]),
            'completed_courses': json.loads(student_df['completed_courses_details'].iloc[0]),
            'core_subjects': student_df['core_subjects'].iloc[0],
            'desired_outcomes': student_df['desired_outcomes'].iloc[0]
        }
        
        # Calculate scores for each subject
        scores = []
        for subject_code in subjects_df['subject_code']:
            burnout = calculate_burnout(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df)
            
            # Get prerequisite info for this subject
            prereqs = list(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
            
            # Check if prerequisites are satisfied
            prereqs_satisfied = all(prereq in student_data.get('completed_courses', {}) for prereq in prereqs)
            
            scores.append({
                'subject_code': subject_code,
                'subject_name': subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0],
                'burnout_score': round(burnout, 3),
                'prerequisites': prereqs,
                'prerequisites_satisfied': prereqs_satisfied
            })
        
        # Create DataFrame and sort by utility (descending)
        scores_df = pd.DataFrame(scores)
        scores_df = scores_df.sort_values(by='utility', ascending=False)
        
        # Save to CSV
        scores_df.to_csv(f'burnout_scores_{nuid}.csv', index=False)
        print(f"Burnout scores and utility values saved to burnout_scores_{nuid}.csv")
        
        return scores_df
        
    except FileNotFoundError:
        print(f"Error: Student data file for NUid {nuid} not found.")
        return None
    
if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_scores(nuid)