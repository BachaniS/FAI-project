import pandas as pd
import json
from utils import load_course_data, load_scores, load_student_data, save_schedules

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
    
def find_matching_courses(student_data, subjects_df, scores_df):
    """Find courses that match student interests and skills"""
    matching_courses = []
    desired_outcomes = student_data.iloc[0]['desired_outcomes']
    student_interests = [interest.lower().strip() for interest in desired_outcomes]
    
    # Add default interests if none provided
    if not student_interests or (len(student_interests) == 1 and not student_interests[0]):
        student_interests = ['computer science', 'data science', 'programming']
    
    for _, course in subjects_df.iterrows():
        score = 0.0
        reasons = []
        
        # Skip courses that have already been completed
        if course['subject_id'] in student_data['completed_courses']:
            continue
            
        # 1. Check course name and outcomes for interest matches
        course_name = str(course['subject_name']).lower()
        course_outcomes = str(course.get('Course Outcomes', '')).lower() if pd.notna(course.get('Course Outcomes', '')) else ""
        
        for interest in student_interests:
            # Check if interest appears in course name
            if interest in course_name:
                score = score + 0.4
                reasons.append(f"Course title matches your interest in {interest}")
            
            # Check if interest appears in course outcomes
            if interest in course_outcomes:
                score = score + 0.3
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
                course['subject_id'] in student_data['core_subjects'].split(','),
                course['Seats'] if pd.notna(course['Seats']) else 0,
                course['Enrollments'] if pd.notna(course['Enrollments']) else 0
            )
        except:
            likelihood = 0.5  # Default likelihood if calculation fails
        
        # 4. Check prerequisites
        prereqs_satisfied = False
        if scores_df is not None:
            for _, score_row in scores_df.iterrows():
                if score_row['subject_id'] == course['subject_id']:
                    prereqs_satisfied = score_row['prerequisites_satisfied']
                    break

        if not prereqs_satisfied:
            score *= 0.5  # Reduce score if prerequisites not met
            reasons.append("⚠️ Prerequisites not completed")
        
        # 5. Add burnout utility score if available
        burnout_score = None
        utility_score = None
        if scores_df is not None:
            burnout_row = scores_df[scores_df['subject_id'] == course['subject_id']]
            if not burnout_row.empty:
                burnout_score = float(burnout_row['burnout_score'].iloc[0])
                utility_score = float(burnout_row['utility'].iloc[0])
                
                # Integrate utility score into the overall score
                if utility_score > 0:
                    score_boost = utility_score * 0.5  # Scale factor to balance with other scores
                    print(f"Score type: {type(score)}, Score: {score}")
                    print(f"Score_boost type: {type(score_boost)}, Value: {score_boost}")
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
        is_core = course['subject_id'] in student_data.iloc[0]['core_subjects']
        if score > 0.3 or is_core:  # Include core subjects regardless of match score
            if is_core:
                score += 0.5  # Boost score for core subjects
                reasons.append("📚 This is a core subject requirement")
            
            matching_courses.append({
                'subject_id': course['subject_id'],
                'subject_name': course['subject_name'],
                'match_score': score,
                'likelihood': likelihood,
                'seats': course['seats'] if pd.notna(course['seats']) else 0,
                'enrollments': course['enrollments'] if pd.notna(course['enrollments']) else 0,
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

def generate_recommendations(nuid, semester, additional_interests=None):
    # load data
    subjects_df = load_course_data()
    scores_df = load_scores(str(nuid))
    student_data = load_student_data(nuid)

    if student_data is None:
        return None, None
    
    # Add additional interests if provided
    if additional_interests:
        student_data['interests'] += ',' + ','.join(additional_interests)
    
    # Find matching courses
    matching_courses = find_matching_courses(student_data, subjects_df,scores_df)
    
    # Separate into recommended and highly competitive
    recommended_courses = []
    highly_competitive_courses = []
    
    for course in matching_courses:
        if course['likelihood'] < 0.3:  # Very competitive
            highly_competitive_courses.append(course)
        else:
            recommended_courses.append(course)
    
    return recommended_courses, highly_competitive_courses

def save_schedule(nuid, recommended_courses):
    # Format recommendations into final schedule format
    top_recommendations = []
    for course in recommended_courses[:5]:
        course_code = course if isinstance(course, str) else course['subject_id']
        
        course_info = {
            'subject_id': course_code,
            'subject_name': course.get('subject_name', 'Unknown course'),
            'utility': course.get('utility_score', 'Not calculated'),
            'burnout': course.get('burnout_score', 'Not calculated')
        }
        top_recommendations.append(course_info)

    save_schedules(nuid, top_recommendations)
    return top_recommendations

if __name__ == "__main__":
    nuid = input("Enter NUid to generate course recommendations: ")
    semester = int(input("Enter semester (1-8): "))
    
    recommended_courses, competitive_courses = generate_recommendations(nuid, semester)
    
    if recommended_courses:
        print(f"\nFound {len(recommended_courses)} recommended courses:")
        for i, course in enumerate(recommended_courses[:5], 1):
            print(f"{i}. {course['subject_id']}: {course['subject_name']}")
        
        # Save schedule
        schedule = save_schedule(nuid, recommended_courses)
        print("\nSchedule saved!")
    else:
        print("No recommended courses found.")