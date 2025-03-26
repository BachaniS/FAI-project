import pandas as pd
import json
from burnout_calculator import calculate_scores, calculate_burnout
from utils import load_course_data, load_student_data, prerequisites_satisfied, standardize_student_data

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

def get_student_data(nuid, semester):
    try:
        student_df = load_student_data(nuid)
        
        # Create basic structure with raw data
        raw_student_data = {
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
        
        return standardize_student_data(raw_student_data, for_burnout=False)
    except FileNotFoundError:
        return None

def generate_recommendations(nuid, semester, additional_interests=None):
    subjects_df, outcomes_df, prereqs_df, coreqs_df, _ = load_subject_data()
    burnout_scores_df = load_burnout_scores(nuid)
    
    student_data = get_student_data(nuid, semester)
    if student_data is None:
        return None, None
    
    # Add additional interests if provided
    if additional_interests:
        student_data['interests'] += ',' + ','.join(additional_interests)
    
    # Find matching courses
    matching_courses = find_matching_courses(
        student_data, subjects_df, outcomes_df, prereqs_df, coreqs_df, burnout_scores_df
    )
    
    # Separate into recommended and highly competitive
    recommended_courses = []
    highly_competitive_courses = []
    
    for course in matching_courses:
        if course['likelihood'] < 0.3:  # Very competitive
            highly_competitive_courses.append(course)
        else:
            recommended_courses.append(course)
    
    return recommended_courses, highly_competitive_courses

def save_schedule(nuid, recommended_courses, subjects_df, burnout_scores_df):
    # Format recommendations into final schedule format
    top_recommendations = []
    for course in recommended_courses:
        course_code = course if isinstance(course, str) else course['subject_code']
        
        # Extract course details
        name = subjects_df[subjects_df['subject_code'] == course_code]['name'].iloc[0] if course_code in subjects_df['subject_code'].values else "Unknown course"
        utility = ""
        if burnout_scores_df is not None:
            utility_row = burnout_scores_df[burnout_scores_df['subject_code'] == course_code]
            if not utility_row.empty:
                utility = utility_row['utility'].iloc[0]
        
        top_recommendations.append({
            'subject_code': course_code,
            'name': name,
            'utility': utility
        })
    
    # Save final selections in schedule format
    subject_list = {}
    for i, course in enumerate(top_recommendations[:5], 1):
        subject_list[f"Subject {i}"] = f"{course['subject_code']}: {course['name']} (Utility: {course['utility']})"
    
    schedule_df = pd.DataFrame([{
        'NUid': nuid,
        'schedule': json.dumps(subject_list)
    }])
    
    return subject_list