import pandas as pd
import numpy as np
import json
from utils import load_course_data, prerequisites_satisfied, standardize_student_data

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

def jaccard_similarity(set1, set2):
    '''
    Calculate Jaccard similarity between two sets 
    '''
    # Handle empty sets
    if not set1 or not set2:
        return 0
        
    # Calculate intersection and union
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    # Prevent division by zero
    if union == 0:
        return 0
        
    return intersection / union


def calculate_outcome_alignment_score(student_data, subject_code, outcomes_df):
    '''
    Calculate outcome alignment score (OAS) using Jaccard similarity
    OAS = similarity(User Desired Outcomes, Course Outcomes)
    __
    Use Jacquard Similarity: https://www.geeksforgeeks.org/how-to-calculate-jaccard-similarity-in-python/ 
    '''
    # If no desired outcomes, return 0
    if not student_data.get('desired_outcomes') or not isinstance(student_data['desired_outcomes'], str):
        return 0
    
    # Get student's desired outcomes as a set
    student_outcomes = set([outcome.strip() for outcome in student_data['desired_outcomes'].split(',')])
    
    # Get subject outcomes as a set
    subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
    
    # Calculate Jaccard similarity
    return jaccard_similarity(student_outcomes, subject_outcomes)

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

    student_data = standardize_student_data(student_data, for_burnout=True)
    
    # Calculate individual factors
    W_prime = workload_factor(subject_code, subjects_df)
    M_prime = calculate_prerequisite_mismatch_factor(student_data, subject_code, requirements_df, prereqs_df)
    S_prime = calculate_stress_factor(student_data, subject_code, subjects_df)
    
    # Calculate combined burnout score
    P_prime = weights['w1'] * W_prime + weights['w2'] * M_prime + weights['w3'] * S_prime
    
    # Normalize to [0,1] using sigmoid function
    P_final = 1 / (1 + np.exp(-weights['k'] * (P_prime - weights['P0'])))
    
    return P_final


def calculate_utility(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df, utility_weights=None):
    '''
    Calculate the overall utility function with prerequisite penalty
    U = α·I + β·(1-Pfinal) + γ·OAS - δ·PrereqPenalty
    '''
    # Default utility weights
    if utility_weights is None:
        utility_weights = {
            'alpha': 0.4,  # Weight for interest/relevance
            'beta': 0.3,   # Weight for burnout avoidance
            'gamma': 0.3,  # Weight for outcome alignment
            'delta': 0.5   # Weight for prerequisite penalty
        }
    
    # Calculate burnout probability
    burnout_prob = calculate_burnout(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df)
    
    # Calculate outcome alignment score
    oas = calculate_outcome_alignment_score(student_data, subject_code, outcomes_df)
    
    # Use outcome alignment as proxy for interest score
    interest_score = oas
    
    # Check prerequisites
    prereq_courses = list(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
    prereq_penalty = 0
    
    if prereq_courses:
        prereqs_satisfied = all(prereq in student_data.get('completed_courses', {}) for prereq in prereq_courses)
        if not prereqs_satisfied:
            prereq_penalty = 1  # Apply full penalty if prerequisites are not satisfied
    
    # Calculate overall utility
    utility = (
        utility_weights['alpha'] * interest_score + 
        utility_weights['beta'] * (1 - burnout_prob) + 
        utility_weights['gamma'] * oas - 
        utility_weights['delta'] * prereq_penalty
    )
    
    return utility

def calculate_scores(nuid):
    '''
    Calculate burnout scores and utility for all subjects for a given student
    '''
    subjects_df, outcomes_df, prereqs_df, _, requirements_df = load_course_data()
    
    try:
        student_df = pd.read_csv(f'data/students/student_{nuid}.csv')
        
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
            utility = calculate_utility(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df)
            
            # Get prerequisite info for this subject
            prereqs = list(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
            
            # Check if prerequisites are satisfied
            prereqs_satisfied = prerequisites_satisfied(subject_code, student_data, prereqs_df)
            
            scores.append({
                'subject_code': subject_code,
                'subject_name': subjects_df[subjects_df['subject_code'] == subject_code]['name'].iloc[0],
                'burnout_score': round(burnout, 3),
                'utility': round(utility, 3),
                'prerequisites': prereqs,
                'prerequisites_satisfied': prereqs_satisfied
            })
        
        # Create DataFrame and sort by utility (descending)
        scores_df = pd.DataFrame(scores)
        scores_df = scores_df.sort_values(by='utility', ascending=False)
        
        # Save to CSV
        scores_df.to_csv(f'outputs/burnout_scores/burnout_scores_{nuid}.csv', index=False)
        print(f"Burnout scores and utility values saved to burnout_scores_{nuid}.csv")
        
        return scores_df
        
    except FileNotFoundError:
        print(f"Error: Student data file for NUid {nuid} not found.")
        return None
    
if __name__ == "__main__":
    nuid = input("Enter NUid to calculate burnout scores: ")
    calculate_scores(nuid)