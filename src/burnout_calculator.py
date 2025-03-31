import pandas as pd
import numpy as np
from utils import load_course_data, load_student_data, save_scores

def get_subject(subjects_df, subject_code):
    '''
    Get subject data
    '''
    subject_rows = subjects_df[subjects_df['subject_id'] == subject_code]
    return subject_rows.iloc[0] if not subject_rows.empty else None

def workload_factor(subject_code, subjects_df):
    '''
    Calculate workload factor W' with the following equation:
     W' = ln(1 + H/Hmax) + A/Amax + P/Pmax + E/Emax
    '''
    subject = get_subject(subjects_df, subject_code)

    # Calculate the max values
    Hmax = max(subjects_df['weekly_course_time'].max(), 1)
    Amax = max((subjects_df['assignment_count'] * subjects_df['assignment_time'] * subjects_df['assignment_weight']).max(), 1)
    Pmax = max(((100 - subjects_df['project_grade']) * subjects_df['project_weight']).max(), 1)
    Emax = max((subjects_df['exam_count'] * (100 - subjects_df['exam_grade']) * subjects_df['exam_weight']).max(), 1)

    # Calculate 
    H = subject['weekly_course_time']
    A = subject['assignment_count'] * subject['assignment_time'] * subject['assignment_weight']
    P = (100 - subject['project_grade']) * subject['project_weight']
    E = subject['exam_count'] * (100 - subject['exam_grade']) * subject['exam_weight']

    W_prime = np.log(1 + H/Hmax) + A/Amax + P/Pmax + E/Emax
    return W_prime

def calculate_prerequisite_mismatch_factor(student_data, subject_code, subjects_df):
    '''
    Calculate modified prerequisite mismatch factor M':
    M' = (1/T) * Σ(1 - proficiency(i))
    '''
    # Get subject requirements from the subjects DataFrame
    subject_row = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
    
    # Extract requirements
    programming_reqs = subject_row.get('Programming Knowledge Needed', '').split(', ') if pd.notna(subject_row.get('Programming Knowledge Needed')) else []
    math_reqs = subject_row.get('Math Requirements', '').split(', ') if pd.notna(subject_row.get('Math Requirements')) else []

    requirements = programming_reqs + math_reqs
    
    # If no prereqs / requirements, then no mismatch
    if len(requirements) == 0:
        return 0 
    
    total_mismatch = 0

    for req in requirements:
        # Check if student has proficiency in programming requirement
        if req in student_data.get('programming_experience', {}):
            proficiency = student_data['programming_experience'][req] / 3.0
            total_mismatch += (1 - proficiency)
        # Check if student has proficiency in math requirement
        elif req in student_data.get('math_experience', {}):
            proficiency = student_data['math_experience'][req] / 3.0
            total_mismatch += (1 - proficiency)
        else:
            # Is not proficient
            total_mismatch += 1

    M_prime = (total_mismatch) / (len(requirements))
    return M_prime

def calculate_stress_factor(student_data, subject_code, subjects_df):
    subject = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
    
    GA = subject['assignment_grade']
    GE = subject['exam_grade']
    GP = subject['project_grade']

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

def jaccard_similarity(set1, set2):
    '''
    Calculate Jaccard similarity between two sets 
    '''
    # Handle empty
    if not set1 or not set2:
        return 0
        
    # Calculate intersection and union
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0
        
    return intersection / union


def calculate_outcome_alignment_score(student_data, subject_code, subjects_df):
    '''
    Calculate outcome alignment score (OAS) using Jaccard similarity
    OAS = similarity(User Desired Outcomes, Course Outcomes)
    __
    Use Jacquard Similarity: https://www.geeksforgeeks.org/how-to-calculate-jaccard-similarity-in-python/ 
    '''
    # If no desired outcomes, return 0
    desired_outcomes = student_data.iloc[0]['desired_outcomes']
    if not desired_outcomes:
        return 0
    
    # Get student's desired outcomes as a set
    student_outcomes = set(outcome.strip() for outcome in desired_outcomes)
    
    # Get subject outcomes as a set
    subject_row = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
    subject_outcomes = set(outcome.strip() for outcome in subject_row.get('Course Outcomes', '').split(','))
    
    # Calculate Jaccard similarity
    return jaccard_similarity(student_outcomes, subject_outcomes)

def calculate_burnout(student_data, subject_code, subjects_df):
    '''
    Calculate the normalized burnout probability
    P' = w1*W' + w2*M' + w3*S'
    Pfinal = 1 / (1 + e^-k(P'-P0))
    '''
    # weights
    weights = {
        'w1': 0.4,  # Weight for workload factor
        'w2': 0.3,  # Weight for prerequisite mismatch
        'w3': 0.3,  # Weight for stress factor
        'k': 4.0,   # Scaling factor for sigmoid
        'P0': 0.5   # Baseline burnout level
    }
    
    # Calculate individual factors
    W_prime = workload_factor(subject_code, subjects_df)
    M_prime = calculate_prerequisite_mismatch_factor(student_data, subject_code, subjects_df)
    S_prime = calculate_stress_factor(student_data, subject_code, subjects_df)
    
    # Calculate combined burnout score
    P_prime = weights['w1'] * W_prime + weights['w2'] * M_prime + weights['w3'] * S_prime
    
    # Normalize to [0,1] using sigmoid function
    P_final = 1 / (1 + np.exp(-weights['k'] * (P_prime - weights['P0'])))
    
    return P_final

def prereq_satisfied(student_data, prereqs):
    '''
    Check if a student has satisfied all prerequisites for a subject.
    Params:
        student_data: student info
        prereqs: list of prereq courses
    Returns:
        Boolean
    '''
    if student_data is None or student_data.empty:
        return False
    
    completed_courses = student_data.iloc[0]['completed_courses']

    # No prerqs, bool is True
    if not prereqs or len(prereqs) == 0:
        return True    
        
    # Check if all prerequisites are in completed courses
    return all(prereq in completed_courses for prereq in prereqs)

def calculate_utility(student_data, subject_code, subjects_df):
    '''
    Calculate the overall utility function with prerequisite penalty
    U = α·I + β·(1-Pfinal) + γ·OAS - δ·PrereqPenalty
    '''
    # Default utility weights
    utility_weights = {
        'alpha': 0.4,  # Weight for interest/relevance
        'beta': 0.3,   # Weight for burnout avoidance
        'gamma': 0.3,  # Weight for outcome alignment
        'delta': 0.5   # Weight for prerequisite penalty
    }
    
    # Calculate burnout probability
    burnout_prob = calculate_burnout(student_data, subject_code, subjects_df)
    
    # Calculate outcome alignment score
    oas = calculate_outcome_alignment_score(student_data, subject_code, subjects_df)
    
    # Check prerequisites
    subject_row = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
    prereq_courses = subject_row.get('Prerequisite', '').split(', ') if pd.notna(subject_row.get('Prerequisite')) else []

    prereq_penalty = 0
    if not prereq_satisfied(student_data, prereq_courses):
        prereq_penalty = 1  # Apply full penalty if prerequisites are not satisfied
    
    # Calculate overall utility
    utility = (
        utility_weights['alpha'] * oas + 
        utility_weights['beta'] * (1 - burnout_prob) + 
        utility_weights['delta'] * prereq_penalty
    )
    
    return utility

def calculate_scores(nuid):
    '''
    Calculate burnout scores and utility for all subjects for a given student
    ''' 
    try:
        subjects_df = load_course_data()
        student_data = load_student_data(str(nuid))
        
        # Calculate scores for each subject
        scores = []
        for subject_code in subjects_df['subject_id']:
            burnout = calculate_burnout(student_data, subject_code, subjects_df)
            utility = calculate_utility(student_data, subject_code, subjects_df)
            
            # Get prerequisite info for this subject
            subject_row = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
            prereqs = subject_row.get('Prerequisite', '').split(', ') if pd.notna(subject_row.get('Prerequisite')) else []
            
            # Check if prerequisites are satisfied
            prereqs_satisfied = prereq_satisfied(student_data, prereqs)
            
            score_entry = {
                'subject_id': subject_code,
                'subject_name': subject_row['subject_name'],
                'burnout_score': round(burnout, 3),
                'utility': round(utility, 3),
                'prerequisites_satisfied': prereqs_satisfied
            }
        
            scores.append(score_entry)

        # Save burnout scores to MongoDB
        save_scores(nuid, scores)
        
        return scores
        
    except Exception as e:
        print(f"Error calculating burnout scores: {e}")
        return None

if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_burnout(nuid)