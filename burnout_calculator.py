import pandas as pd
import numpy as np
from utils import load_course_data, load_student_data, prerequisites_satisfied, standardize_student_data

def get_subject(subjects_df, subject_code):
    '''
    Get subject data
    '''
    subject_rows = subjects_df[subjects_df['subject_id'] == subject_code]
    return subject_rows.iloc[0] if not subject_rows.empty else None

def workload_factor(subject_code, subjects_df, max_values):
    '''
    Calculate workload factor W' with the following equation:
     W' = ln(1 + H/Hmax) + A/Amax + P/Pmax + E/Emax
    '''
    subject_rows = get_subject(subjects_df, subject_code)
        
    subject = subject_rows.iloc[0]
    
    # Handle missing values with defaults
    H = subject['weekly_course_time'] if pd.notna(subject['weekly_course_time']) else 0
    num_assignments = subject['assignment_count'] if pd.notna(subject['assignment_count']) else 0
    hours_per_assignment = subject['assignment_time'] if pd.notna(subject['assignment_time']) else 0
    assignment_weight = subject['assignment_weight'] if pd.notna(subject['assignment_weight']) else 0
    avg_project_grade = subject['project_grade'] if pd.notna(subject['project_grade']) else 0
    project_weight = subject['project_weight'] if pd.notna(subject['project_weight']) else 0
    exam_count = subject['exam_count'] if pd.notna(subject['exam_count']) else 0
    avg_exam_grade = subject['exam_grade'] if pd.notna(subject['exam_grade']) else 0
    exam_weight = subject['exam_weight'] if pd.notna(subject['exam_weight']) else 0
    
    # Calculate components
    A = num_assignments * hours_per_assignment * assignment_weight
    P = (100 - avg_project_grade) * project_weight
    E = exam_count * (100 - avg_exam_grade) * exam_weight

    # Calculate workload factor
    W_prime = np.log(1 + H/max_values['Hmax']) + A/max_values['Amax'] + P/max_values['Pmax'] + E/max_values['Emax']
    
    return W_prime
        
def calculate_prerequisite_mismatch_factor(student_data, subject_reqs):
    '''
    Calculate modified prerequisite mismatch factor M':
    M' = (1/T) * Σ(1 - proficiency(i))
    '''    
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
            proficiency = min(max(student_data['programming_experience'][req_name] / 3.0, 0), 1)
            total_mismatch += (1 - proficiency)
        # Check if student has proficiency in math requirement
        elif req_type == 'math' and req_name in student_data.get('math_experience', {}):
            proficiency = min(max(student_data['math_experience'][req_name] / 3.0, 0), 1)
            total_mismatch += (1 - proficiency)
        else:
            # Is not proficient
            total_mismatch += 1

    M_prime = (1/T) * (total_mismatch)
    return M_prime

def calculate_stress_factor(student_data, subject_code, subjects_df):
    '''
    Calculate modified stress factor S':
    S' = ((100-GA)/100)² * Aw + ((100-GE)/100)² * Ew + ((100-GP)/100)² * Pw) / (Aw + Ew + Pw)
    '''
    subject_rows = get_subject(subjects_df, subject_code)

    subject = subject_rows.iloc[0]
    
    # Default values from subject data (with safety checks)
    default_GA = subject['avg_assignment_grade'] if pd.notna(subject['avg_assignment_grade']) else 70
    default_GE = subject['avg_exam_grade'] if pd.notna(subject['avg_exam_grade']) else 70
    default_GP = subject['avg_project_grade'] if pd.notna(subject['avg_project_grade']) else 70
    
    # Get weights with defaults
    Aw = subject['assignment_weight'] if pd.notna(subject['assignment_weight']) else 0
    Ew = subject['exam_weight'] if pd.notna(subject['exam_weight']) else 0
    Pw = subject['project_weight'] if pd.notna(subject['project_weight']) else 0
    
    # Use student's actual performance if available, with proper validation
    if subject_code in student_data.get('completed_courses', {}):
        completed_course = student_data['completed_courses'][subject_code]
        if isinstance(completed_course, dict):
            GA = completed_course.get('Avg Assignment Grade', default_GA)
            GE = completed_course.get('Avg Exam Grade', default_GE)
            GP = completed_course.get('Avg Project Grade', default_GP)
        else:
            # If completed course entry isn't a dict, use defaults
            GA, GE, GP = default_GA, default_GE, default_GP
    else:
        # Use average grades from subject data
        GA, GE, GP = default_GA, default_GE, default_GP

    # Handle division by zero
    total_weight = Aw + Ew + Pw
    if total_weight == 0:
        return 0
    
    # Calculate stress components with bounds checking (ensure values between 0-100)
    GA = max(0, min(100, GA))
    GE = max(0, min(100, GE))
    GP = max(0, min(100, GP))
    
    stress_assignments = ((100 - GA) / 100) ** 2 * Aw
    stress_exams = ((100 - GE) / 100) ** 2 * Ew
    stress_projects = ((100 - GP) / 100) ** 2 * Pw
    
    S_prime = (stress_assignments + stress_exams + stress_projects) / total_weight
    
    return S_prime

def precalculate_max_values(subjects_df):
    '''
    Calculate maximum values for workload normalization
    Params:
        Subjects_df: Subject data information
    Returns: Max values for 
    '''
    max_values = {
        'Hmax': max(subjects_df['weekly_course_time'].max(), 1),
        'Amax': max((subjects_df['assignment_count'] * subjects_df['assignment_time'] * subjects_df['assignment_weight']).max(), 1),
        'Pmax': max(((100 - subjects_df['project_grade']) * subjects_df['project_weight']).max(), 1),
        'Emax': max((subjects_df['exam_count'] * (100 - subjects_df['exam_grade']) * subjects_df['exam_weight']).max(), 1)
    }
    return max_values

def calculate_burnout(subject_code, subjects_df, student_df, max_values=None, weights=None):
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
    
    # Ensure student data is in correct format
    student_data = standardize_student_data(student_df, for_burnout=True)

    # Extract the subject row
    subject = subjects_df.loc[subjects_df['subject_id'] == subject_code]

    # Extract required fields safely
    requirements = (subject['required_programming'].iloc[0] if not subject['required_programming'].isna().all() else [])
    requirements += (subject['required_math'].iloc[0] if not subject['required_math'].isna().all() else [])
        
    # Calculate or use provided max values
    if max_values is None:
        max_values = precalculate_max_values(subjects_df)
    
    # Calculate individual factors
    W_prime = workload_factor(subject_code, subjects_df, max_values)
    M_prime = calculate_prerequisite_mismatch_factor(student_data, subject_code, requirements)
    S_prime = calculate_stress_factor(student_data, subject_code, subjects_df)
        
    # Calculate combined burnout score
    P_prime = weights['w1'] * W_prime + weights['w2'] * M_prime + weights['w3'] * S_prime
    
    # Normalize to [0,1] using sigmoid function
    P_final = 1 / (1 + np.exp(-weights['k'] * (P_prime - weights['P0'])))
    
    return P_final

def calculate_scores(nuid):
    '''
    Calculate burnout scores for all subjects for a given student
    '''
    # Load all necessary data
    subjects_df = load_course_data()
    
    # Precalculate max values once for efficiency
    max_values = precalculate_max_values(subjects_df)
    
    # Load student data
    student_df = load_student_data(nuid)

    
    # Calculate scores for each subject
    scores = []
    for subject_code in subjects_df['subject_id']:
        # Skip subjects the student has already completed
        if subject_code in student_df['completed_courses']:
            continue
            
        # Extract prerequisites from subjects_df
        prereqs = subjects_df.loc[subjects_df['subject_id'] == subject_code, 'prerequisites']
        prereqs = prereqs.iloc[0] if not prereqs.empty and pd.notna(prereqs.iloc[0]) else []
        if isinstance(prereqs, str):
            prereqs = prereqs.split(',')  # Assuming prerequisites are stored as comma-separated strings
        
        # Calculate burnout probability
        burnout = calculate_burnout(subject_code, subjects_df, student_df, max_values)
        
        # Check if prerequisites are satisfied
        prereqs_satisfied_val = prerequisites_satisfied(subject_code, student_df, subjects_df)
        
        # Get subject name safely
        subject_row = subjects_df[subjects_df['subject_id'] == subject_code]
        subject_name = subject_row['subject_name'].iloc[0] if not subject_row.empty else "Unknown course"
        
        # Append score
        scores.append({
            'subject_id': subject_code,
            'subject_name': subject_name,
            'burnout_score': round(burnout, 3),
            'prerequisites': prereqs,
            'prerequisites_satisfied': prereqs_satisfied_val,
            'utility': 0  # Placeholder - will be calculated in ga_recommender
        })

    # Create DataFrame and sort by burnout (ascending - lower burnout is better)
    scores_df = pd.DataFrame(scores)
    scores_df = scores_df.sort_values(by='burnout_score', ascending=True)
        
    return scores_df
    
if __name__ == "__main__":
    nuid = input("Enter NUID to calculate burnout scores: ")
    result = calculate_scores(nuid)
    
    if result is not None:
        print(f"Calculated burnout scores for {len(result)} subjects.")
        print("Top 5 subjects with lowest burnout risk:")
        for i, (_, row) in enumerate(result.head(5).iterrows()):
            print(f"{i+1}. {row['subject_code']}: {row['subject_name']} (Burnout: {row['burnout_score']})")
    else:
        print("Failed to calculate burnout scores. Check logs for details.")