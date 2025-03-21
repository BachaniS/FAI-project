import pandas as pd
import random
from deap import base, creator, tools, algorithms
import json
import numpy as np
from burnout_calculator import calculate_burnout
from difflib import SequenceMatcher

def load_subject_data():
    df = pd.read_csv('subjects_df.csv')
    subjects_df = df[['Subject', 'Subject Names', 'Course Outcomes', 'Weekly Workload (hours)', 
                      'Assignments #', 'Hours per Assignment', 'Assignment Weight', 
                      'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade', 
                      'Exam #', 'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade', 
                      'Seats', 'Enrollments']].rename(columns={
        'Subject': 'subject_code',
        'Subject Names': 'name',
        'Course Outcomes': 'course_outcomes',
        'Weekly Workload (hours)': 'hours_per_week',
        'Assignments #': 'num_assignments',
        'Hours per Assignment': 'hours_per_assignment',
        'Assignment Weight': 'assignment_weight',
        'Avg Assignment Grade': 'avg_assignment_grade',
        'Project Weight': 'project_weight',
        'Avg Project Grade': 'avg_project_grade',
        'Exam #': 'exam_count',
        'Avg Exam Grade': 'avg_exam_grade',
        'Exam Weight': 'exam_weight',
        'Avg Final Grade': 'avg_final_grade',
        'Seats': 'Seats',
        'Enrollments': 'Enrollments'
    })
    for col in ['hours_per_week', 'num_assignments', 'hours_per_assignment', 'assignment_weight', 
                'avg_assignment_grade', 'project_weight', 'avg_project_grade', 'exam_count', 
                'avg_exam_grade', 'exam_weight', 'avg_final_grade', 'Seats', 'Enrollments']:
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

def load_burnout_scores(nuid):
    """Load burnout scores from CSV file"""
    try:
        scores_df = pd.read_csv(f'burnout_scores_{nuid}.csv')
        # Remove any duplicates if present
        scores_df = scores_df.drop_duplicates(subset=['subject_code'])
        return scores_df
    except FileNotFoundError:
        return None

def prerequisites_satisfied(course_code, student_data, prereqs_df):
    """Check if prerequisites for a course are satisfied"""
    prereqs = set(prereqs_df[prereqs_df['subject_code'] == course_code]['prereq_subject_code'])
    return all(p in student_data['completed_courses'] for p in prereqs)

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

def calculate_utility(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df, utility_weights=None):
    '''
    Calculate the overall utility function with prerequisite penalty
    U = α·OAS + β·(1-Pfinal) - δ·PrereqPenalty
    '''
    # Default utility weights
    if utility_weights is None:
        utility_weights = {
            'alpha': 0.5,  # Weight for outcome alignment
            'beta': 0.5,   # Weight for burnout avoidance
            'delta': 0.5   # Weight for prerequisite penalty
        }
    
    # Calculate burnout probability
    burnout_prob = calculate_burnout(student_data, subject_code, subjects_df, requirements_df, prereqs_df, outcomes_df)
    
    # Calculate outcome alignment score
    oas = calculate_outcome_alignment_score(student_data, subject_code, outcomes_df)
    
    # Check prerequisites
    prereq_courses = list(prereqs_df[prereqs_df['subject_code'] == subject_code]['prereq_subject_code'])
    prereq_penalty = 0
    
    if prereq_courses:
        prereqs_satisfied = all(prereq in student_data.get('completed_courses', {}) for prereq in prereq_courses)
        if not prereqs_satisfied:
            prereq_penalty = 1  # Apply full penalty if prerequisites are not satisfied
    
    # Calculate overall utility
    utility = (
        utility_weights['alpha'] * oas + 
        utility_weights['beta'] * (1 - burnout_prob) - 
        utility_weights['delta'] * prereq_penalty
    )
    
    return utility

def calculate_enrollment_likelihood(semester, is_core, seats, enrollments):
    # Base likelihood from seats availability
    seats_ratio = (seats - enrollments) / seats if seats > 0 else 0
    if seats_ratio <= 0:
        base_likelihood = 0.1  # Very low chance but not impossible due to potential drops
    else:
        base_likelihood = seats_ratio

    # Semester priority multiplier (higher semester = higher priority)
    semester_multiplier = min(semester / 4, 1.0)  # Caps at 1.0 after 4th semester
    
    # Core requirement multiplier
    core_multiplier = 1.5 if is_core else 1.0
    
    final_likelihood = base_likelihood * semester_multiplier * core_multiplier
    return min(final_likelihood, 1.0)  # Cap at 100%
    
def find_matching_courses(student_data, subjects_df, outcomes_df, prereqs_df, coreqs_df, burnout_scores_df=None):
    """Find courses that match student interests and skills"""
    matching_courses = []
    student_interests = [interest.lower().strip() for interest in student_data['interests'].split(',')]
    
    # Add default interests if none provided
    if not student_interests or (len(student_interests) == 1 and not student_interests[0]):
        student_interests = ['computer science', 'data science', 'programming']
    
    for _, course in subjects_df.iterrows():
        score = 0
        reasons = []
        
        # Skip courses that have already been completed
        if course['subject_code'] in student_data['completed_courses']:
            continue
            
        # 1. Check course name and outcomes for interest matches
        course_name = str(course['name']).lower()
        course_outcomes = str(course['course_outcomes']).lower() if pd.notna(course['course_outcomes']) else ""
        
        for interest in student_interests:
            # Check if interest appears in course name
            if interest in course_name:
                score += 0.4
                reasons.append(f"Course title matches your interest in {interest}")
            
            # Check if interest appears in course outcomes
            if interest in course_outcomes:
                score += 0.3
                reasons.append(f"Course covers topics in {interest}")
        
        # 2. Check for specific keywords based on interests
        interest_keywords = {
            'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'neural', 'nlp'],
            'web': ['web', 'javascript', 'frontend', 'backend', 'full-stack', 'react', 'node'],
            'data': ['data', 'analytics', 'database', 'sql', 'big data', 'visualization'],
            'security': ['security', 'cryptography', 'cyber', 'network security'],
            'mobile': ['mobile', 'ios', 'android', 'app development'],
            'systems': ['operating system', 'distributed', 'parallel', 'architecture'],
            'programming': ['python', 'java', 'c++', 'algorithms', 'software engineering'],
            'computer science': ['algorithms', 'data structures', 'programming', 'software']
        }
        
        for interest in student_interests:
            if interest in interest_keywords:
                for keyword in interest_keywords[interest]:
                    if keyword in course_outcomes:
                        score += 0.2
                        reasons.append(f"Course includes {keyword} technologies")
        
        # 3. Calculate enrollment likelihood
        try:
            likelihood = calculate_enrollment_likelihood(
                student_data['semester'],
                course['subject_code'] in student_data['core_subjects'].split(','),
                course['Seats'] if pd.notna(course['Seats']) else 0,
                course['Enrollments'] if pd.notna(course['Enrollments']) else 0
            )
        except:
            likelihood = 0.5  # Default likelihood if calculation fails
        
        # 4. Check prerequisites
        if not prerequisites_satisfied(course['subject_code'], student_data, prereqs_df):
            score *= 0.5  # Reduce score if prerequisites not met
            reasons.append("⚠️ Prerequisites not completed")
        
        # 5. Add burnout utility score if available
        burnout_score = None
        utility_score = None
        if burnout_scores_df is not None:
            burnout_row = burnout_scores_df[burnout_scores_df['subject_code'] == course['subject_code']]
            if not burnout_row.empty:
                burnout_score = float(burnout_row['burnout_score'].iloc[0])
                utility_score = float(burnout_row['utility'].iloc[0])
                
                # Integrate utility score into the overall score
                if utility_score > 0:
                    score_boost = utility_score * 0.5  # Scale factor to balance with other scores
                    score += score_boost
                    if utility_score > 0.15:
                        reasons.append(f"✅ Low burnout risk (utility: {utility_score:.2f})")
                    else:
                        reasons.append(f"Low-moderate burnout risk (utility: {utility_score:.2f})")
                elif utility_score < 0:
                    # Negative utility reduces score
                    score *= (1 + utility_score)  # Multiplicative penalty
                    reasons.append(f"⚠️ High burnout risk (utility: {utility_score:.2f})")
        
        # If course has a reasonable match score or is a core subject
        is_core = course['subject_code'] in student_data['core_subjects'].split(',')
        if score > 0.3 or is_core:  # Include core subjects regardless of match score
            if is_core:
                score += 0.5  # Boost score for core subjects
                reasons.append("📚 This is a core subject requirement")
            
            matching_courses.append({
                'subject_code': course['subject_code'],
                'name': course['name'],
                'match_score': score,
                'likelihood': likelihood,
                'seats': course['Seats'] if pd.notna(course['Seats']) else 0,
                'enrollments': course['Enrollments'] if pd.notna(course['Enrollments']) else 0,
                'burnout_score': burnout_score,
                'utility_score': utility_score,
                'reasons': reasons,
                'is_core': is_core
            })
    
    # Sort by combination of match score, utility score, and enrollment likelihood
    matching_courses.sort(key=lambda x: (
        x['is_core'],  # Core subjects first
        x['match_score'] * 0.5 +  # 50% weight to interest match
        (x['utility_score'] if x['utility_score'] is not None else 0) * 0.3 +  # 30% weight to burnout utility
        x['likelihood'] * 0.2  # 20% weight to enrollment likelihood
    ), reverse=True)
    
    return matching_courses

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
    """Main function that generates and returns recommendations for UI to display"""
    subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
    burnout_scores_df = load_burnout_scores(nuid)
    
    try:
        student_df = pd.read_csv(f'student_{nuid}.csv')
    except FileNotFoundError:
        print(f"Error: Student data not found for NUID: {nuid}")
        return None, None, None
    
    semester = int(input("Which semester are you in? "))
    
    student_data = {
        'NUid': student_df['NUid'].iloc[0],
        'semester': semester,
        'completed_courses': set(str(course).upper() for course in 
            str(student_df['completed_courses'].iloc[0]).split(',') 
            if pd.notna(student_df['completed_courses'].iloc[0]) and str(student_df['completed_courses'].iloc[0]).strip()),
        'core_subjects': str(student_df['core_subjects'].iloc[0]).upper(),
        'interests': (
            str(student_df['desired_outcomes'].iloc[0]) if pd.notna(student_df['desired_outcomes'].iloc[0]) 
            else 'computer science'
        ),
        'desired_outcomes': (
            str(student_df['desired_outcomes'].iloc[0]) if pd.notna(student_df['desired_outcomes'].iloc[0]) 
            else 'computer science'
        )
    }
    
    # Get additional interests if needed
    additional_interests = []
    choice = input("\nWould you like to add specific interests to improve recommendations? (yes/no): ").lower().strip()
    if choice == 'yes':
        print("\nWhat areas are you interested in? (Select one or more numbers, separated by commas)")
        interests = {
            1: "artificial intelligence",
            2: "web development",
            3: "data science",
            4: "cybersecurity",
            5: "mobile development",
            6: "systems programming",
            7: "cloud computing",
            8: "software engineering",
            9: "database systems",
            10: "computer vision",
            11: "natural language processing",
            12: "algorithms",
            13: "networking",
            14: "robotics"
        }
        
        for num, interest in interests.items():
            print(f"{num}. {interest}")
        
        try:
            choices = input("\nEnter numbers (e.g., 1,3,5) or 'skip' to continue: ").strip()
            if choices.lower() != 'skip':
                additional_interests = [interests[int(num.strip())] for num in choices.split(',')]
                student_data['interests'] += ',' + ','.join(additional_interests)
        except:
            print("Invalid input. Continuing with default interests.")
    
    # Find matching courses
    matching_courses = find_matching_courses(
        student_data, subjects_df, outcomes_df, prereqs_df, coreqs_df, burnout_scores_df
    )
    
    # Separate into recommended and highly competitive
    recommended_courses = []
    highly_competitive_courses = []
    
    for course in matching_courses:
        if course['likelihood'] < 0.3:  # Very competitive
            if len(highly_competitive_courses) < 5:
                highly_competitive_courses.append(course)
        else:
            if len(recommended_courses) < 5:
                recommended_courses.append(course)
    
    # Save the final schedule (top 5 recommendations)
    top_recommendations = []
    for course in recommended_courses + highly_competitive_courses:
        if len(top_recommendations) >= 5:
            break
        
        top_recommendations.append(course['subject_code'])
    
    # Format schedule for saving
    subject_list = {}
    for i, course_code in enumerate(top_recommendations, 1):
        # Extract course details
        name = subjects_df[subjects_df['subject_code'] == course_code]['name'].iloc[0] if course_code in subjects_df['subject_code'].values else "Unknown course"
        utility = ""
        if burnout_scores_df is not None:
            utility_row = burnout_scores_df[burnout_scores_df['subject_code'] == course_code]
            if not utility_row.empty:
                utility = utility_row['utility'].iloc[0]
        
        subject_list[f"Subject {i}"] = f"{course_code}: {name} (Utility: {utility})"
    
    # Save schedule to CSV
    schedule_df = pd.DataFrame([{
        'NUid': nuid,
        'schedule': json.dumps(subject_list)
    }])
    
    schedule_df.to_csv(f'schedule_{nuid}.csv', index=False)
    
    return recommended_courses, highly_competitive_courses, subject_list