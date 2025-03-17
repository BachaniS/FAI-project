import pandas as pd
import random
from deap import base, creator, tools, algorithms
import json
import numpy as np
from difflib import SequenceMatcher

def load_subject_data():
    df = pd.read_csv('subjects.csv')
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

def calculate_alignment(student_data, subject_code, outcomes_df):
    desired = set(student_data['desired_outcomes'].split(','))
    subject_outcomes = set(outcomes_df[outcomes_df['subject_code'] == subject_code]['outcome'])
    overlap = len(desired & subject_outcomes) / len(desired) if desired else 0
    return overlap

def calculate_enrollment_likelihood(semester, is_core, seats, enrollments):
    # Base likelihood from seats availability
    seats_ratio = (seats - enrollments) / seats
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

def calculate_name_similarity(name1, name2):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

def calculate_skills_match(student_skills, course_outcomes):
    """Calculate how well student skills match course requirements"""
    student_skills_set = set(skill.strip().lower() for skill in student_skills.split(','))
    course_skills_set = set(outcome.strip().lower() for outcome in course_outcomes.split(','))
    if not student_skills_set:
        return 0
    return len(student_skills_set & course_skills_set) / len(course_skills_set)

def find_matching_courses(student_data, subjects_df, outcomes_df, prereqs_df, coreqs_df):
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
        prereqs = get_all_prereqs(course['subject_code'], prereqs_df, subjects_df)
        if prereqs and not all(p in student_data['completed_courses'] for p in prereqs):
            score *= 0.5  # Reduce score if prerequisites not met
            reasons.append("⚠️ Some prerequisites not completed")
        
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
                'reasons': reasons,
                'is_core': is_core
            })
    
    # Sort by combination of match score and enrollment likelihood
    matching_courses.sort(key=lambda x: (x['is_core'], x['match_score'] * 0.7 + x['likelihood'] * 0.3), reverse=True)
    return matching_courses

def get_additional_interests():
    """Get additional interests from the user"""
    print("\nWhat other areas are you interested in? (Select one or more numbers, separated by commas)")
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
        if choices.lower() == 'skip':
            return []
        
        selected = [interests[int(num.strip())] for num in choices.split(',')]
        return selected
    except:
        print("Invalid input. Continuing with current recommendations.")
        return []

def recommend_schedule(nuid):
    subjects_df, outcomes_df, prereqs_df, coreqs_df = load_subject_data()
    try:
        scores_df = pd.read_csv(f'burnout_scores_{nuid}.csv')
        student_df = pd.read_csv(f'student_{nuid}.csv')
    except FileNotFoundError:
        print(f"Error: Student data not found for NUID: {nuid}")
        return None
    
    semester = int(input("Which semester are you in? "))
    
    # Keep track of recommended courses to avoid repetition
    recommended_history = set()
    
    def get_recommendations(additional_interests=None):
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
            )
        }
        
        # Add additional interests if provided
        if additional_interests:
            student_data['interests'] += ',' + ','.join(additional_interests)
        
        # Find matching courses
        matching_courses = find_matching_courses(student_data, subjects_df, outcomes_df, prereqs_df, coreqs_df)
        
        # Filter out previously recommended courses
        new_matches = [course for course in matching_courses 
                      if course['subject_code'] not in recommended_history]
        
        # Separate into recommended and highly competitive
        recommended_courses = []
        highly_competitive_courses = []
        
        for course in new_matches:
            if course['likelihood'] < 0.3:  # Very competitive
                if len(highly_competitive_courses) < 5:
                    highly_competitive_courses.append(course)
                    recommended_history.add(course['subject_code'])
            else:
                if len(recommended_courses) < 5:
                    recommended_courses.append(course)
                    recommended_history.add(course['subject_code'])
        
        return recommended_courses, highly_competitive_courses

    def get_enrollment_status(seats, enrollments):
        """Get enrollment status message based on seats and enrollments"""
        if seats <= 0 or enrollments <= 0:
            return "⚠️ Enrollment data not available"
        
        seats_remaining = seats - enrollments
        enrollment_ratio = enrollments / seats
        
        if enrollment_ratio >= 1:
            return "🔴 This class is currently full. Very difficult to enroll - consider for future semesters"
        elif enrollment_ratio >= 0.9:
            return "🟠 Limited seats available (>90% full). Enroll immediately if interested"
        elif enrollment_ratio >= 0.75:
            return "🟡 Class is filling up quickly (>75% full). Enroll soon to secure your spot"
        else:
            return "🟢 Good availability. Enroll at your convenience but don't wait too long"

    def display_recommendations(recommended_courses, highly_competitive_courses, round_num=1):
        print(f"\n=== Round {round_num} Recommendations ===")
        
        # Display recommendations
        print("\n🎯 Recommended Courses:")
        if recommended_courses:
            for i, course in enumerate(recommended_courses, 1):
                seats = course['seats']
                enrollments = course['enrollments']
                
                print(f"\n{i}. {course['subject_code']}: {course['name']}")
                print(f"   Match Score: {course['match_score']:.1%}")
                print(f"   Reasons for recommendation:")
                for reason in course['reasons']:
                    print(f"   • {reason}")
                
                # Enrollment status
                print(f"   Current Status: {seats - enrollments} seats remaining ({enrollments}/{seats} filled)")
                enrollment_status = get_enrollment_status(seats, enrollments)
                print(f"   {enrollment_status}")
                
                # Show likelihood only if relevant
                if seats > enrollments:
                    likelihood_percent = course['likelihood'] * 100
                    print(f"   Enrollment Likelihood: {likelihood_percent:.1f}%")
        else:
            print("No new courses found matching your immediate criteria.")
        
        # Display highly competitive courses
        if highly_competitive_courses:
            print("\n⚠️ Highly Competitive Courses:")
            for i, course in enumerate(highly_competitive_courses, 1):
                seats = course['seats']
                enrollments = course['enrollments']
                
                print(f"\n{i}. {course['subject_code']}: {course['name']}")
                print(f"   Match Score: {course['match_score']:.1%}")
                print(f"   Reasons for recommendation:")
                for reason in course['reasons']:
                    print(f"   • {reason}")
                
                # Enrollment status
                print(f"   Current Status: {seats - enrollments} seats remaining ({enrollments}/{seats} filled)")
                enrollment_status = get_enrollment_status(seats, enrollments)
                print(f"   {enrollment_status}")
                
                # Additional warning for highly competitive courses
                print("   ⚠️ Note: This is a highly competitive course due to high demand")
                if seats <= enrollments:
                    print("   💡 Tip: Consider registering for this course in a future semester when you'll have higher priority")
                else:
                    print("   💡 Tip: If interested, prepare to register immediately when registration opens")

    # Initial recommendations
    round_num = 1
    recommended_courses, highly_competitive_courses = get_recommendations()
    display_recommendations(recommended_courses, highly_competitive_courses, round_num)
    
    # Continue recommending until user is satisfied or no more courses
    while True:
        if not (recommended_courses or highly_competitive_courses):
            print("\nNo more courses available matching your criteria.")
            break
            
        choice = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
        if choice != 'yes':
            break
            
        # Get additional interests
        print("\nLet's find more courses based on additional interests!")
        additional_interests = get_additional_interests()
        
        # Get new recommendations
        round_num += 1
        recommended_courses, highly_competitive_courses = get_recommendations(additional_interests)
        display_recommendations(recommended_courses, highly_competitive_courses, round_num)

    return recommended_history

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

def recommend_schedule_with_feedback(nuid):
    recommend_schedule(nuid)

if __name__ == "__main__":
    nuid = input("Enter NUid to recommend schedule: ")
    recommend_schedule_with_feedback(nuid)