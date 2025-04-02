from ga_recommender import (
    genetic_algorithm, calculate_fitness, optimize_schedule, rerun_genetic_algorithm,
    calculate_total_burnout, display_plan, save_plan_to_db, SEMESTERS, COURSES_PER_SEMESTER
)
from burnout_calculator import calculate_scores, calculate_outcome_alignment_score, calculate_burnout
from utils import (
    load_course_data, load_student_data, save_schedules, get_subject_name, 
    get_unmet_prerequisites, get_student_completed_courses, get_student_core_subjects,
    update_knowledge_profile, save_knowledge_profile
)
import pandas as pd
import os
import time
import json
import random
from collections import Counter
from student_input import get_student_input

# Configuration constants
MAX_RECOMMENDATIONS = 5
LIKELIHOOD_THRESHOLD = 0.7  # Threshold for high likelihood
HIGHLY_COMPETITIVE_THRESHOLD = 0.9  # Threshold for highly competitive courses

def load_interest_categories():
    '''
    Load interest categories from JSON file
    Returns:
        Dictionary of interest categories and their related terms
    '''
    try:
        import json
        import os
        
        # Path to the interest categories JSON file
        # Adjust this path to where you store your JSON file
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interest_categories.json")
        
        with open(file_path, 'r') as f:
            interest_categories = json.load(f)
            
        return interest_categories
    except Exception as e:
        print(f"⚠️ Error loading interest categories: {e}")
        # Fallback to a minimal set of categories if file can't be loaded
        return {
            "artificial intelligence": ["Artificial Intelligence"],
            "machine learning": ["Machine Learning"],
            "web": ["JavaScript", "Web Development"],
            "data science": ["Data Science"],
            "computer vision": ["Computer Vision"]
        }

def get_enrollment_status(seats, enrollments):
    '''
    Get enrollment messages based on the given seats and enrollments
    Params:
        Seats: Number of seats for a class
        Enrollments: Number of enrollments
    Returns:
        Enrollment user friendly status
    '''
    if seats <= 0 or enrollments <= 0:
        return "⚠️ Enrollment data not available"
    
    enrollment_ratio = enrollments / seats
    
    if enrollment_ratio >= 1:
        return "🔴 This class is currently full. Very difficult to enroll - consider for future semesters"
    elif enrollment_ratio >= 0.9:
        return "🟠 Limited seats available (>90% full). Enroll immediately if interested"
    elif enrollment_ratio >= 0.75:
        return "🟡 Class is filling up quickly (>75% full). Enroll soon to secure your spot"
    else:
        return "🟢 Good availability. Enroll at your convenience but don't wait too long"

def get_burnout_status(burnout_score, utility_score):
    '''
    Get the burnout status based on utility and burnout
    Params:
        Burnout_Score: Computed burnout score
        utility_Score: Computed utility score
    Returns:
        User-friendly burnout status
    '''
    if burnout_score is None or utility_score is None:
        return "⚠️ Burnout data not available"
    
    if burnout_score > 0.8:
        return "🔴 High burnout risk. Consider careful time management if taking this course"
    elif burnout_score > 0.6:
        return "🟠 Moderate-high burnout risk. May require significant time commitment"
    elif burnout_score > 0.4:
        return "🟡 Moderate burnout risk. Typical workload for your program"
    else:
        return "🟢 Low burnout risk. Should be manageable with your current skills"

def get_difficulty_status(subject_code, subjects_df, student_data):
    '''
    Calculate difficulty rating based on prerequisite match and workload
    Params:
        subject_code: The course subject code
        subjects_df: DataFrame of all subjects
        student_data: Student profile data
    Returns:
        Difficulty status message
    '''
    # Get subject data
    subject_row = subjects_df[subjects_df['subject_id'] == subject_code].iloc[0]
    
    # Calculate burnout as a proxy for difficulty
    burnout = calculate_burnout(student_data, subject_code, subjects_df)
    
    # Get unmet prerequisites
    completed_courses = set(get_student_completed_courses(student_data))
    unmet_prereqs = get_unmet_prerequisites(subjects_df, subject_code, completed_courses)
    
    # Calculate difficulty rating
    if len(unmet_prereqs) > 0:
        return "🔴 High difficulty. Missing prerequisites may make this course challenging."
    elif burnout > 0.7:
        return "🟠 Moderate-high difficulty. Prepare to allocate significant study time."
    elif burnout > 0.4:
        return "🟡 Moderate difficulty. Should be manageable with regular study."
    else:
        return "🟢 Standard difficulty. Aligns well with your current knowledge level."

def filter_courses_by_interests(available_subjects, interests, subjects_df):
    '''
    Filter available courses based on student interests
    Params:
        available_subjects: List of available subject IDs
        interests: List of interest categories
        subjects_df: DataFrame with all course data
    Returns:
        List of subject IDs sorted by relevance to interests
    '''
    if not interests:
        return available_subjects
    
    interest_categories = load_interest_categories()
    subject_scores = {subject_id: 0 for subject_id in available_subjects}
    
    for subject_id in available_subjects:
        # Get subject details
        subject_row = subjects_df[subjects_df['subject_id'] == subject_id]
        if subject_row.empty:
            continue
            
        subject_name = subject_row.iloc[0]['subject_name']
        description = str(subject_row.iloc[0].get('description', ''))
        programming_knowledge = str(subject_row.iloc[0].get('programming_knowledge_needed', ''))
        math_requirements = str(subject_row.iloc[0].get('math_requirements', ''))
        course_outcomes = str(subject_row.iloc[0].get('course_outcomes', ''))
        
        # Combine all text fields for matching
        subject_text = f"{subject_name} {description} {programming_knowledge} {math_requirements} {course_outcomes}".lower()
        
        # Check for each interest
        for interest in interests:
            # Direct match
            if interest.lower() in subject_text:
                subject_scores[subject_id] += 3
            
            # Check related terms from interest categories
            if interest in interest_categories:
                for term in interest_categories[interest]:
                    if term.lower() in subject_text:
                        subject_scores[subject_id] += 1
    
    # Sort by score and filter out zero scores
    scored_subjects = [(subject_id, score) for subject_id, score in subject_scores.items() if score > 0]
    scored_subjects.sort(key=lambda x: x[1], reverse=True)
    
    # Return filtered subjects, if no matches return original list
    if scored_subjects:
        return [subject_id for subject_id, _ in scored_subjects]
    else:
        return available_subjects
    
def prompt_for_student_info():
    '''
    Prompt for student information with options to login or create new account
    Returns:
        Student NUID
    '''
    print("\n" + "="*60)
    print("🎓 WELCOME TO YOUR PERSONALIZED COURSE RECOMMENDER")
    print("="*60)
    print("\nThis system will help you find courses that match your interests,")
    print("academic background, and provide insights on enrollment status and burnout risk.")
    
    # Ask if new or returning user
    print("\nPlease select an option:")
    print("1. Log in with existing NUID")
    print("2. Create a new student profile")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        # Existing user login
        nuid = input("\nPlease enter your NUid: ")
        
        # Validate NUID (simple validation for demonstration)
        while not nuid.strip():
            print("❌ Invalid NUid. Please try again.")
            nuid = input("Enter your NUid: ")
        
        # Try to load the student data
        try:
            student_data = load_student_data(nuid)
            name = student_data['name'].iloc[0]
            print(f"✅ Welcome back! Profile loaded for student {name}")
        except Exception as e:
            print(f"\n⚠️ We couldn't find your profile: {e}")
            create_profile = input("Would you like to create a new profile instead? (yes/no): ").lower().strip()
            
            if create_profile == 'yes':
                print("\nLet's create your profile to get personalized recommendations...")
                get_student_input()
            else:
                print("\n⚠️ A profile is required to use the recommender system.")
                print("Please create a profile next time or contact support.")
                exit()
    
    elif choice == "2":
        # New user - create profile
        print("\nLet's create a new student profile for you!")
        student_data = get_student_input()
        nuid = student_data["NUID"]
        print(f"✅ Profile created successfully for student {nuid}")
    
    else:
        print("❌ Invalid choice. Defaulting to login.")
        nuid = prompt_for_student_info()

    # Calculate burnout scores
    try:
        calculate_scores(nuid)
        print("✅ Burnout scores calculated successfully")
    except Exception as e:
        print(f"⚠️ Error calculating burnout scores: {e}")
    
    return nuid

def get_additional_interests():
    '''
    User input for users additional interests
    Returns:
        List of interests inputted by user
    '''
    print("\n" + "="*60)
    print("🔍 REFINE YOUR RECOMMENDATIONS")
    print("="*60)
    print("\nWhat other areas are you interested in? (Select one or more numbers, separated by commas)")
    
    # Load interest categories
    interest_categories = load_interest_categories()
    
    # Create a numbered dictionary of interest options
    interests = {}
    for i, category in enumerate(interest_categories.keys(), 1):
        interests[i] = category
    
    # Display interests in two columns for better readability
    col_width = max(len(interest) for interest in interests.values()) + 5
    
    # Split into chunks for better display
    chunk_size = 20  # Display 20 items per page
    total_pages = (len(interests) + chunk_size - 1) // chunk_size
    current_page = 1
    
    while True:
        # Calculate start and end indices for current page
        start_idx = (current_page - 1) * chunk_size + 1
        end_idx = min(current_page * chunk_size, len(interests))
        
        print(f"\nPage {current_page}/{total_pages}:")
        
        # Display interests in two columns
        for i in range(start_idx, end_idx + 1, 2):
            if i + 1 <= end_idx:
                print(f"{i:2}. {interests[i]:<{col_width}} {i+1:2}. {interests[i+1]}")
            else:
                print(f"{i:2}. {interests[i]}")
        
        # Navigation options
        if total_pages > 1:
            nav_choice = input("\nEnter numbers to select interests, 'n' for next page, 'p' for previous page, or 'done' when finished: ").strip()
            
            if nav_choice.lower() == 'n' and current_page < total_pages:
                current_page += 1
                continue
            elif nav_choice.lower() == 'p' and current_page > 1:
                current_page -= 1
                continue
            elif nav_choice.lower() == 'done' or nav_choice.lower() == 'skip':
                break
        else:
            nav_choice = input("\nEnter numbers (e.g., 1,3,5) or 'skip' to continue: ").strip()
            if nav_choice.lower() == 'skip':
                return []
    
        # Process selected interests
        try:
            # Skip if navigation command
            if nav_choice.lower() in ['n', 'p', 'done', 'skip']:
                if nav_choice.lower() in ['done', 'skip']:
                    return []
                continue
            
            selected = []
            for num in nav_choice.split(','):
                num = int(num.strip())
                if num in interests:
                    selected.append(interests[num])
            
            if selected:
                print(f"\n✅ Selected interests: {', '.join(selected)}")
                return selected
            else:
                print("\n⚠️ No valid interests selected.")
        except Exception as e:
            print(f"❌ Invalid input: {e}. Please try again.")
    
    return []

def calculate_schedule_balance(recommended_courses, subjects_df):
    '''
    Calculate the balance of the recommended schedule
    Params:
        recommended_courses: List of recommended courses
        subjects_df: DataFrame containing all course data
    Returns:
        Dictionary with balance metrics
    '''
    if not recommended_courses:
        return {"balanced": False, "reason": "No courses selected"}
    
    # Extract course types
    course_types = []
    burnout_scores = []
    interest_areas = []
    
    for course in recommended_courses:
        subject_row = subjects_df[subjects_df['subject_id'] == course['subject_code']]
        if not subject_row.empty:
            # Get course type
            course_type = subject_row.iloc[0].get('course_type', 'Unknown')
            course_types.append(course_type)
            
            # Get burnout score
            burnout_scores.append(course['burnout_score'] if course['burnout_score'] is not None else 0.5)
            
            # Try to determine interest area
            subject_name = subject_row.iloc[0]['subject_name'].lower()
            description = str(subject_row.iloc[0].get('description', '')).lower()
            
            interest_categories = load_interest_categories()
            
            # Check which categories it falls into
            for category, terms in interest_categories.items():
                for term in terms:
                    if term.lower() in subject_name or term.lower() in description:
                        interest_areas.append(category)
                        break
    
    # Count types
    type_counts = Counter(course_types)
    interest_counts = Counter(interest_areas)
    
    # Calculate total burnout
    avg_burnout = sum(burnout_scores) / len(burnout_scores) if burnout_scores else 0
    
    # Determine if balanced
    type_balanced = len(type_counts) >= min(2, len(recommended_courses))
    interest_balanced = len(interest_counts) >= min(2, len(recommended_courses))
    high_burnout = avg_burnout > 0.7
    
    reason = []
    if not type_balanced:
        reason.append("All selected courses are of the same type")
    
    if not interest_balanced:
        reason.append("Courses focus on a limited set of interest areas")
    
    if high_burnout:
        reason.append("Overall burnout risk is high")
    
    if not reason:
        reason.append("Schedule appears balanced across course types, interests, and difficulty")
    
    return {
        "balanced": type_balanced and not high_burnout and interest_balanced,
        "type_diversity": len(type_counts),
        "interest_diversity": len(interest_counts),
        "avg_burnout": avg_burnout,
        "reason": ". ".join(reason) + "."
    }

def convert_ga_schedule_to_recommendations(schedule, student_data, subjects_df, interests):
    '''
    Convert genetic algorithm schedule to recommendation format
    Params:
        schedule: List of course IDs from genetic algorithm
        student_data: Student profile data
        subjects_df: DataFrame with all course data
        interests: List of student interests
    Returns:
        List of course recommendation objects
    '''
    recommended_courses = []
    interest_categories = load_interest_categories()
    
    for subject_id in schedule:
        # Get subject details
        subject_row = subjects_df[subjects_df['subject_id'] == subject_id]
        if subject_row.empty:
            continue
            
        subject_name = subject_row.iloc[0]['subject_name']
        
        # Calculate burnout and utility
        burnout_score = calculate_burnout(student_data, subject_id, subjects_df)
        utility_score = calculate_outcome_alignment_score(student_data, subject_id, subjects_df)
        
        # Generate realistic enrollment data
        seats = random.randint(20, 100)
        enrollments = random.randint(0, seats)
        
        # Calculate match score based on utility and burnout
        match_score = utility_score * (1 - burnout_score)
        
        # Calculate enrollment likelihood
        enrollment_ratio = enrollments / seats if seats > 0 else 0
        likelihood = 1 - (enrollment_ratio * 0.8)
        
        # Generate reasons for recommendation
        reasons = []
        
        # Add interest-based reason
        if interests:
            matching_interests = []
            for interest in interests:
                # Check direct match
                if interest.lower() in subject_name.lower():
                    matching_interests.append(interest)
                    continue
                
                # Check terms associated with the interest
                if interest in interest_categories:
                    for term in interest_categories[interest]:
                        if term.lower() in subject_name.lower():
                            matching_interests.append(interest)
                            break
            
            if matching_interests:
                reasons.append(f"Aligns with your interest in {', '.join(set(matching_interests)[:2])}")
        
        # Add GA-based reason
        reasons.append("Selected by genetic algorithm for optimal academic fit")
        
        # Add utility reason
        if utility_score > 0.7:
            reasons.append("High academic utility for your program")
        elif utility_score > 0.5:
            reasons.append("Good academic utility for your program")
        
        # Add burnout reason
        if burnout_score < 0.3:
            reasons.append("Low burnout risk with your background")
        
        # Ensure we have at least three reasons
        if len(reasons) < 3:
            completed_courses = set(get_student_completed_courses(student_data))
            prereqs = get_unmet_prerequisites(subjects_df, subject_id, completed_courses)
            if not prereqs:
                reasons.append("You meet all prerequisites for this course")
            
            if len(reasons) < 3:
                reasons.append("Fits well within your overall academic plan")
        
        # Create course recommendation object
        course_recommendation = {
            'subject_code': subject_id,
            'name': subject_name,
            'match_score': match_score,
            'burnout_score': burnout_score,
            'utility_score': utility_score,
            'seats': seats,
            'enrollments': enrollments,
            'likelihood': likelihood,
            'reasons': reasons[:3]  # Limit to 3 reasons
        }
        
        recommended_courses.append(course_recommendation)
    
    return recommended_courses

def identify_competitive_courses(recommended_courses):
    '''
    Identify highly competitive courses from recommendations
    Params:
        recommended_courses: List of recommendation objects
    Returns:
        Tuple of (regular courses, highly competitive courses)
    '''
    regular = []
    competitive = []
    
    for course in recommended_courses:
        seats = course.get('seats', 0)
        enrollments = course.get('enrollments', 0)
        
        if seats > 0 and enrollments > 0:
            enrollment_ratio = enrollments / seats
            if enrollment_ratio > HIGHLY_COMPETITIVE_THRESHOLD:
                competitive.append(course)
            else:
                regular.append(course)
        else:
            regular.append(course)
    
    # Sort by match score
    regular.sort(key=lambda x: x['match_score'], reverse=True)
    competitive.sort(key=lambda x: x['match_score'], reverse=True)
    
    return regular, competitive

def display_recommendations(recommended_courses, highly_competitive_courses, subjects_df, student_data, round_num=1):
    '''
    Formatting the recommendations for the user
    Params:
        recommended_courses: Filtered out courses for a given user.
        highly_competitive_courses: Courses that are highly competitive
        subjects_df: DataFrame containing all subject data
        student_data: Student profile data
        round_num: Integer
    Returns:
        User friendly recommended courses
    '''
    # Clear terminal for better readability
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display header with round information
    print("\n" + "="*60)
    print(f"🎓 COURSE RECOMMENDATIONS (ROUND {round_num})")
    print("="*60)
    
    # Display recommendations
    if recommended_courses:
        print("\n🎯 RECOMMENDED COURSES:")
        for i, course in enumerate(recommended_courses, 1):
            seats = course.get('seats', 0)
            enrollments = course.get('enrollments', 0)
            
            # Course header with emoji based on match score
            match_score = course.get('match_score', 0)
            if match_score > 0.8:
                match_emoji = "🌟"  # Excellent match
            elif match_score > 0.6:
                match_emoji = "✨"  # Very good match
            elif match_score > 0.4:
                match_emoji = "👍"  # Good match
            else:
                match_emoji = "👌"  # Acceptable match
                
            print(f"\n{i}. {match_emoji} {course['subject_code']}: {course['name']}")
            print(f"   Match Score: {course['match_score']:.1%}")
            
            # Burnout information if available
            if course.get('burnout_score') is not None and course.get('utility_score') is not None:
                burnout_status = get_burnout_status(course['burnout_score'], course['utility_score'])
                print(f"   Burnout Risk: {course['burnout_score']:.2f}")
                print(f"   Academic Utility: {course['utility_score']:.2f}")
                print(f"   {burnout_status}")
                
                # Add difficulty rating
                difficulty_status = get_difficulty_status(course['subject_code'], subjects_df, student_data)
                print(f"   {difficulty_status}")
            
            # Check prerequisite status
            completed_courses = set(get_student_completed_courses(student_data))
            unmet_prereqs = get_unmet_prerequisites(subjects_df, course['subject_code'], completed_courses)
            if unmet_prereqs:
                print(f"   ⚠️ Missing prerequisites: {', '.join(unmet_prereqs)}")
            
            # Display reasons for recommendation
            print(f"   Reasons for recommendation:")
            for reason in course.get('reasons', []):
                print(f"   • {reason}")
            
            # Enrollment status
            if seats > 0 and enrollments > 0:
                print(f"   Current Status: {seats - enrollments} seats remaining ({enrollments}/{seats} filled)")
                enrollment_status = get_enrollment_status(seats, enrollments)
                print(f"   {enrollment_status}")
            else:
                print("   ⚠️ Enrollment data not available")
            
            # Show likelihood only if relevant
            if seats > enrollments:
                likelihood_percent = course.get('likelihood', 0) * 100
                likelihood_emoji = "🔥" if likelihood_percent > 80 else "✅" if likelihood_percent > 50 else "⚠️"
                print(f"   Enrollment Likelihood: {likelihood_emoji} {likelihood_percent:.1f}%")
    else:
        print("\n⚠️ No new courses found matching your immediate criteria.")
    
    # Display highly competitive courses
    if highly_competitive_courses:
        print("\n⚠️ HIGHLY COMPETITIVE COURSES:")
        for i, course in enumerate(highly_competitive_courses, 1):
            seats = course.get('seats', 0)
            enrollments = course.get('enrollments', 0)
            
            print(f"\n{i}. 🏆 {course['subject_code']}: {course['name']}")
            print(f"   Match Score: {course['match_score']:.1%}")
            
            # Burnout information if available
            if course.get('burnout_score') is not None and course.get('utility_score') is not None:
                burnout_status = get_burnout_status(course['burnout_score'], course['utility_score'])
                print(f"   Burnout Risk: {course['burnout_score']:.2f}")
                print(f"   Academic Utility: {course['utility_score']:.2f}")
                print(f"   {burnout_status}")
                
                # Add difficulty rating
                difficulty_status = get_difficulty_status(course['subject_code'], subjects_df, student_data)
                print(f"   {difficulty_status}")
            
            # Check prerequisite status
            completed_courses = set(get_student_completed_courses(student_data))
            unmet_prereqs = get_unmet_prerequisites(subjects_df, course['subject_code'], completed_courses)
            if unmet_prereqs:
                print(f"   ⚠️ Missing prerequisites: {', '.join(unmet_prereqs)}")
            
            # Display reasons for recommendation
            print(f"   Reasons for recommendation:")
            for reason in course.get('reasons', []):
                print(f"   • {reason}")
            
            # Enrollment status
            if seats > 0 and enrollments > 0:
                print(f"   Current Status: {seats - enrollments} seats remaining ({enrollments}/{seats} filled)")
                enrollment_status = get_enrollment_status(seats, enrollments)
                print(f"   {enrollment_status}")
            else:
                print("   ⚠️ Enrollment data not available")
            
            # Additional warning for highly competitive courses
            print("   ⚠️ Note: This is a highly competitive course due to high demand")
            if seats <= enrollments:
                print("   💡 Tip: Consider registering for this course in a future semester when you'll have higher priority")
            else:
                print("   💡 Tip: If interested, prepare to register immediately when registration opens")
    
    return len(recommended_courses) + len(highly_competitive_courses) > 0

def display_final_schedule(recommended_history, subjects_df, burnout_scores_df, nuid):
    '''
    Display the final schedule with summary statistics
    Params:
        recommended_history: Set of recommended course codes
        subjects_df: DataFrame with all course data
        burnout_scores_df: DataFrame with burnout scores
        nuid: Student ID
    '''
    print("\n" + "="*60)
    print("🏁 FINAL RECOMMENDED SCHEDULE")
    print("="*60)
    
    # Calculate total burnout
    total_burnout = 0
    total_utility = 0
    course_count = 0
    
    # Group courses by semester (assuming 2 courses per semester)
    courses_per_semester = 2
    semesters = []
    current_semester = []
    
    for i, subject_code in enumerate(recommended_history, 1):
        current_semester.append(subject_code)
        if i % courses_per_semester == 0:
            semesters.append(current_semester)
            current_semester = []
    
    # Add any remaining courses
    if current_semester:
        semesters.append(current_semester)
    
    # Display courses by semester
    for i, semester_courses in enumerate(semesters, 1):
        print(f"\nSemester {i}:")
        for subject_code in semester_courses:
            # Get subject details
            subject_name = get_subject_name(subjects_df, subject_code)
            
            # Get burnout score
            burnout_score = None
            utility_score = None
            if burnout_scores_df is not None:
                subject_scores = burnout_scores_df[burnout_scores_df['subject_id'] == subject_code]
                if not subject_scores.empty:
                    burnout_score = subject_scores.iloc[0].get('burnout_score')
                    utility_score = subject_scores.iloc[0].get('utility')
            
            # Display course info
            print(f"  • {subject_code}: {subject_name}")
            if burnout_score is not None and utility_score is not None:
                burnout_status = get_burnout_status(burnout_score, utility_score)
                print(f"    Burnout Risk: {burnout_score:.2f}")
                print(f"    Academic Utility: {utility_score:.2f}")
                print(f"    {burnout_status}")
                
                # Update totals
                total_burnout += burnout_score
                total_utility += utility_score
                course_count += 1
    
    # Calculate averages
    avg_burnout = total_burnout / course_count if course_count > 0 else 0
    avg_utility = total_utility / course_count if course_count > 0 else 0
    
    # Display summary statistics
    print("\n" + "-"*60)
    print("📊 Schedule Summary:")
    print(f"  • Total Courses: {course_count}")
    print(f"  • Average Burnout Risk: {avg_burnout:.2f}")
    print(f"  • Average Academic Utility: {avg_utility:.2f}")
    
    # Overall assessment
    if avg_burnout > 0.7:
        print("  • ⚠️ Warning: This schedule has a high overall burnout risk.")
        print("    Consider spreading high-intensity courses across multiple semesters.")
    elif avg_burnout > 0.5:
        print("  • 🟡 Note: This schedule has a moderate overall burnout risk.")
        print("    Be prepared for a challenging but manageable workload.")
    else:
        print("  • 🟢 Good news: This schedule has a balanced overall burnout risk.")
        print("    The workload should be manageable with good time management.")
    
    print("\n✅ Final schedule saved to the database.")
    print(f"   You can access your schedule details anytime using your NUID: {nuid}")

def recommend_schedule(nuid):
    '''
    Main function for recommending a schedule for a user
    Params:
        nuid: Student id
    Returns:
        Recommendation
    '''
    # Global variables for blacklist and final course list
    blacklist = set()
    final_list = []
    
    print("\n" + "="*60)
    print("🎓 COURSE RECOMMENDATION SYSTEM")
    print("="*60)
    print("\nLoading data and calculating scores...")
    
    try:
        subjects_df = load_course_data()
        student_data = load_student_data(nuid)
        
        # Ensure student_data contains the expected keys
        if 'core_subjects' not in student_data.iloc[0] or 'completed_courses' not in student_data.iloc[0]:
            print("❌ Error: Student data is missing required fields.")
            return None

        # Parse core subjects
        core_subjects = get_student_core_subjects(student_data)
        core_subjects = [s.strip() for s in core_subjects if s.strip()]  # Clean up any empty entries
        core_remaining = core_subjects.copy()
        
        # Initialize plan and student state
        plan = [[] for _ in range(SEMESTERS)]
        taken = set(get_student_completed_courses(student_data))
        
        # Load all available subjects
        all_subjects = subjects_df['subject_id'].tolist()
        
        # Get student's initial interests
        print("\nLet's start by understanding your interests!")
        initial_interests = get_additional_interests()
        
        # Track final fitness for reporting
        final_fitness = 0
        
        print("\n" + "="*60)
        print("🔮 INTERACTIVE SCHEDULE PLANNER")
        print("="*60)
        print("\nWe'll build your schedule semester by semester.")
        print(f"For each of the {SEMESTERS} semesters, our genetic algorithm will suggest the best combination of courses.")
        print("You can accept or reject the suggestions, and we'll optimize the final schedule.")
        
        # Plan each semester interactively
        for sem_idx in range(SEMESTERS):
            # Get available subjects that aren't blacklisted or already selected
            available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
            
            # Filter by interests if specified
            if initial_interests:
                available_subjects = filter_courses_by_interests(available_subjects, initial_interests, subjects_df)
            
            # Check if we have enough subjects to continue
            if len(available_subjects) < COURSES_PER_SEMESTER:
                print(f"⚠️ Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
                break
            
            # Plan this semester
            print("\n" + "-"*60)
            print(f"🗓️ PLANNING SEMESTER {sem_idx + 1}")
            print("-"*60)
            
            # Interactive loop until user is satisfied with this semester
            while True:
                # Show loading animation
                print("Running genetic algorithm", end="")
                for _ in range(3):
                    time.sleep(0.5)
                    print(".", end="", flush=True)
                print("\n")
                
                # Run GA to get the best schedule for this semester
                best_semester = genetic_algorithm(available_subjects, taken, student_data, core_remaining)
                
                # Update the plan
                plan[sem_idx] = best_semester
                
                # Display the current plan
                display_plan(plan, student_data, taken)
                
                # Calculate fitness score
                fitness = calculate_fitness(best_semester, taken, student_data, core_remaining)
                print(f"\nSemester Fitness Score: {fitness:.2f}")
                
                # Analyze semester content
                core_in_semester = [c for c in best_semester if c in core_remaining]
                if core_in_semester:
                    print(f"Core courses included: {', '.join(core_in_semester)}")
                
                if len(core_in_semester) < min(len(core_remaining), COURSES_PER_SEMESTER):
                    print(f"Note: {len(core_remaining) - len(core_in_semester)} core courses still need to be scheduled.")
                
                # Interest alignment check
                if initial_interests:
                    interest_matches = []
                    for course in best_semester:
                        subject_row = subjects_df[subjects_df['subject_id'] == course]
                        if not subject_row.empty:
                            subject_name = subject_row.iloc[0]['subject_name'].lower()
                            
                            # Check if course matches any interests
                            for interest in initial_interests:
                                if interest.lower() in subject_name:
                                    interest_matches.append(f"{course} ({interest})")
                                    break
                                
                                # Check related terms
                                interest_categories = load_interest_categories()
                                if interest in interest_categories:
                                    for term in interest_categories[interest]:
                                        if term.lower() in subject_name:
                                            interest_matches.append(f"{course} ({interest})")
                                            break
                    
                    if interest_matches:
                        print(f"Interest alignment: {', '.join(interest_matches)}")
                    else:
                        print("Note: No direct interest matches in this semester's courses")
                
                # Ask user if they're satisfied or want to blacklist courses
                satisfied = input(f"\nAre you satisfied with Semester {sem_idx + 1}? (yes/no): ").lower()
                
                if satisfied == "yes":
                    # Accept this semester and move on
                    final_list.extend(best_semester)
                    taken.update(best_semester)
                    
                    # Update knowledge profile
                    print("Updating your knowledge profile based on these courses...")
                    programming_skills, math_skills = update_knowledge_profile(student_data, taken)
                    save_knowledge_profile(nuid, programming_skills, math_skills)
                    
                    # Update core_remaining
                    core_remaining = [c for c in core_remaining if c not in best_semester]
                    final_fitness += fitness
                    
                    print(f"✅ Semester {sem_idx + 1} confirmed!")
                    break
                elif satisfied == "no":
                    # Ask which course to blacklist
                    print("\nWhich course would you like to remove from consideration?")
                    for i, course in enumerate(best_semester, 1):
                        course_name = get_subject_name(subjects_df, course)
                        print(f"{i}. {course} - {course_name}")
                    
                    choice = input("\nEnter the number or the subject code to remove: ")
                    
                    # Process the choice
                    remove_code = None
                    try:
                        # If they entered a number
                        idx = int(choice) - 1
                        if 0 <= idx < len(best_semester):
                            remove_code = best_semester[idx]
                    except ValueError:
                        # If they entered a subject code
                        if choice in best_semester:
                            remove_code = choice
                    
                    if remove_code:
                        blacklist.add(remove_code)
                        print(f"🚫 {remove_code} added to blacklist. Re-planning Semester {sem_idx + 1}...")
                        
                        # Update available subjects
                        available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
                        
                        # Re-filter by interests if specified
                        if initial_interests:
                            available_subjects = filter_courses_by_interests(available_subjects, initial_interests, subjects_df)
                    else:
                        print("❌ Invalid selection. Please try again.")
                else:
                    print("❌ Please enter 'yes' or 'no'.")
        
        # Check if any core subjects weren't scheduled
        if core_remaining:
            print(f"\n⚠️ Warning: Core subjects {', '.join(core_remaining)} were not scheduled!")
        
        # Optimize the initial schedule
        print("\n" + "="*60)
        print("🔄 OPTIMIZING YOUR SCHEDULE")
        print("="*60)
        print("\nNow optimizing the initial schedule to minimize burnout...")
        
        # Show loading animation
        print("Running optimization", end="")
        for _ in range(5):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print("\n")
        
        optimized_plan, total_burnout = optimize_schedule(plan, student_data, taken)
        plan = optimized_plan
        print(f"Initial Optimized Total Burnout: {total_burnout:.3f}")
        
        # Show the initial optimized plan
        print("\n" + "-"*60)
        print("📋 INITIAL OPTIMIZED PLAN")
        print("-"*60)
        display_plan(plan, student_data, taken)
        
        # Run the GA again on the entire list of selected courses to optimize ordering
        print("\n" + "="*60)
        print("🧬 FINAL GENETIC ALGORITHM OPTIMIZATION")
        print("="*60)
        print("\nRunning advanced genetic algorithm to find the optimal course order...")
        
        # Show loading animation
        print("Running final optimization", end="")
        for _ in range(5):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print("\n")
        
        final_subjects = final_list.copy()
        initial_taken = set(student_data.iloc[0].get("completed_courses", {}).keys())
        
        best_plan, best_burnout = rerun_genetic_algorithm(
            final_subjects, 
            student_data, 
            initial_taken
        )
        
        # Display the final optimized plan
        print(f"\nFinal Optimized Total Burnout: {best_burnout:.3f}")
        print(f"Improvement: {(total_burnout - best_burnout) / total_burnout:.1%} burnout reduction")
        
        print("\n" + "="*60)
        print("🏆 FINAL OPTIMIZED SCHEDULE")
        print("="*60)
        display_plan(best_plan, student_data, initial_taken)
        
        # Save the plan to the database
        try:
            save_plan_to_db(best_plan, nuid, -best_burnout, student_data, initial_taken)
            print("\n✅ Your optimized schedule has been saved to the database.")
            print(f"   You can access it anytime using your NUID: {nuid}")
        except Exception as e:
            print(f"\n❌ Error saving schedule to database: {e}")
        
        # Display schedule balance assessment
        course_recommendations = []
        for semester in best_plan:
            for course in semester:
                # Create recommendation objects for assessment
                course_info = {
                    'subject_code': course,
                    'name': get_subject_name(subjects_df, course),
                    'burnout_score': calculate_burnout(student_data, course, subjects_df),
                    'utility_score': calculate_outcome_alignment_score(student_data, course, subjects_df)
                }
                course_recommendations.append(course_info)
        
        balance = calculate_schedule_balance(course_recommendations, subjects_df)
        
        print("\n" + "-"*60)
        print("📊 SCHEDULE BALANCE ASSESSMENT")
        print("-"*60)
        print(f"• Overall balance: {'✅ Good' if balance['balanced'] else '⚠️ Could be improved'}")
        print(f"• Course type diversity: {balance['type_diversity']} different types")
        if 'interest_diversity' in balance:
            print(f"• Interest area diversity: {balance['interest_diversity']} different areas")
        print(f"• Average burnout risk: {balance['avg_burnout']:.2f}")
        print(f"• Assessment: {balance['reason']}")
        
        # Return final schedule
        return final_list
    except Exception as e:
        print(f"\n❌ Error loading student data: {e}")
        print("Please create a profile first using the profile creation tool.")
        return None

def browse_recommendations(nuid, semester, interests=None):
    '''
    Browse recommendations without using the full GA planning process
    This is an alternative entry point that shows courses without committing to a schedule
    
    Params:
        nuid: Student ID
        semester: Current semester number
        interests: Optional list of interests
    '''
    print("\n" + "="*60)
    print("🔍 COURSE RECOMMENDATION BROWSER")
    print("="*60)
    print("\nThis will show you course recommendations based on your profile and interests")
    print("without going through the full schedule planning process.")
    
    # Load necessary data
    subjects_df = load_course_data()
    student_data = load_student_data(nuid)
    
    # Get completed courses and all available subjects
    completed_courses = set(get_student_completed_courses(student_data))
    all_subjects = [s for s in subjects_df['subject_id'].tolist() if s not in completed_courses]
    
    # Get interests if not provided
    if not interests:
        interests = get_additional_interests()
    
    # Filter by interests if specified
    if interests:
        available_subjects = filter_courses_by_interests(all_subjects, interests, subjects_df)
    else:
        available_subjects = all_subjects
    
    # Limit to a reasonable number of subjects for the GA
    available_subjects = available_subjects[:50] if len(available_subjects) > 50 else available_subjects
    
    # Get core subjects for this student
    core_subjects = get_student_core_subjects(student_data)
    core_subjects = [s.strip() for s in core_subjects if s.strip()]
    
    # Run GA to get a suggested schedule
    print("\nGenerating recommendations based on your profile and interests...")
    
    # Show loading animation
    print("Running genetic algorithm", end="")
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print("\n")
    
    # Run the GA for a single semester
    best_semester = genetic_algorithm(available_subjects, completed_courses, student_data, core_subjects)
    
    # Convert to recommendation objects
    recommendations = convert_ga_schedule_to_recommendations(best_semester, student_data, subjects_df, interests)
    
    # Identify competitive courses
    regular_courses, competitive_courses = identify_competitive_courses(recommendations)
    
    # Display recommendations
    display_recommendations(regular_courses, competitive_courses, subjects_df, student_data)
    
    # Ask if user wants to see more recommendations
    more = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
    round_num = 2
    
    while more == 'yes':
        # Get additional interests
        print("\nLet's refine your recommendations with more specific interests.")
        additional_interests = get_additional_interests()
        
        # If user provided interests, update the full list
        if additional_interests:
            if interests:
                interests = list(set(interests + additional_interests))
            else:
                interests = additional_interests
        
        # Filter available subjects again
        if interests:
            available_subjects = filter_courses_by_interests(all_subjects, interests, subjects_df)
        else:
            available_subjects = all_subjects
        
        # Remove previously shown courses
        shown_courses = [course['subject_code'] for course in regular_courses + competitive_courses]
        available_subjects = [s for s in available_subjects if s not in shown_courses]
        
        if not available_subjects:
            print("\n⚠️ No more courses available matching your criteria.")
            break
        
        # Limit to a reasonable number
        available_subjects = available_subjects[:50] if len(available_subjects) > 50 else available_subjects
        
        print(f"\nGenerating new recommendations for round {round_num}...")
        
        # Show loading animation
        print("Running genetic algorithm", end="")
        for _ in range(3):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print("\n")
        
        # Run the GA for a single semester
        best_semester = genetic_algorithm(available_subjects, completed_courses, student_data, core_subjects)
        
        # Convert to recommendation objects
        recommendations = convert_ga_schedule_to_recommendations(best_semester, student_data, subjects_df, interests)
        
        # Identify competitive courses
        regular_courses, competitive_courses = identify_competitive_courses(recommendations)
        
        # Display recommendations
        has_more = display_recommendations(regular_courses, competitive_courses, subjects_df, student_data, round_num)
        
        if not has_more:
            print("\n⚠️ No more courses available matching your criteria.")
            break
        
        # Ask if user wants to continue
        more = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
        round_num += 1
    
    print("\nThank you for browsing course recommendations!")
    return None

if __name__ == "__main__":
    try:
        # Start the recommendation process
        nuid = prompt_for_student_info()
        
        # Ask what mode user wants
        print("\n" + "="*60)
        print("Please select an option:")
        print("1. Full Schedule Planning - Create an optimized multi-semester plan")
        print("2. Recommendation Browser - Just browse recommended courses")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            recommend_schedule(nuid)
        elif choice == "2":
            semester = int(input("\nWhich semester are you in? "))
            browse_recommendations(nuid, semester)
        else:
            print("Invalid option. Defaulting to full schedule planning.")
            recommend_schedule(nuid)
        
        # Final message
        print("\n" + "="*60)
        print("🎉 RECOMMENDATION PROCESS COMPLETE")
        print("="*60)
        print("\nThank you for using the Course Recommendation System!")
        print("We hope these recommendations help you plan your academic journey.")
        print("\nGood luck with your studies! 📚")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please try again later or contact support with the error message above.")