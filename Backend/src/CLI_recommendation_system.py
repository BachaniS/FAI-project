from ga_recommender import (
    genetic_algorithm, calculate_fitness, optimize_schedule, rerun_genetic_algorithm, display_plan, save_plan_to_db, SEMESTERS, COURSES_PER_SEMESTER
)
from burnout_calculator import calculate_scores, calculate_outcome_alignment_score, calculate_burnout, calculate_utility
from utils import (
    load_course_data, load_student_data, get_subject_name, 
    get_unmet_prerequisites, get_student_completed_courses, get_student_core_subjects,
    update_knowledge_profile, save_knowledge_profile, load_scores, get_burnout_score, get_utility_score, get_student_desired_outcomes, save_desired_outcomes
)
import os
import time
import json
import random
from pymongo import MongoClient
import datetime

HIGHLY_COMPETITIVE_THRESHOLD = 0.9  # Threshold for highly competitive courses

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["user_details"]
collection = db["users"]

def get_user_interests(student_data=None, mode='new'):
    """Get user input for interests, either for a new user or adding to an existing profile."""

    desired_outcomes = []
    if student_data is not None:
        desired_outcomes = get_student_desired_outcomes(student_data)

    if mode == 'add':
        add_interests = input("Would you like to add interests to your profile? (yes/no): ").strip().lower()
        if add_interests not in ['yes', 'y']:
            print("No interests will be added.")
            return desired_outcomes  # Return existing desired outcomes if no new interests are added
        print_section_header("🔍 ADD TO YOUR INTERESTS")
        print("\nSelect additional areas of interest to add to your profile.")
    else:
        print_section_header("🔍 SELECT YOUR INTERESTS")
        print("\nYour interests help us recommend courses that align with your goals.")
    
    interest_categories = load_interest_categories()
    interests = {i: category for i, category in enumerate(interest_categories.keys(), 1)}
    
    col_width = max(len(interest) for interest in interests.values()) + 5
    chunk_size = 20
    total_pages = (len(interests) + chunk_size - 1) // chunk_size
    current_page = 1
    
    while True:
        start_idx = (current_page - 1) * chunk_size + 1
        end_idx = min(current_page * chunk_size, len(interests))
        
        print(f"\nPage {current_page}/{total_pages}:")
        for i in range(start_idx, end_idx + 1, 2):
            if i + 1 <= end_idx:
                print(f"{i:2}. {interests[i]:<{col_width}} {i+1:2}. {interests[i+1]}")
            else:
                print(f"{i:2}. {interests[i]}")
        
        if total_pages > 1:
            nav_choice = input("\nEnter numbers to select interests, 'n' for next page, 'p' for previous page, or 'done' when finished: ").strip()
            if nav_choice.lower() == 'n' and current_page < total_pages:
                current_page += 1
                continue
            elif nav_choice.lower() == 'p' and current_page > 1:
                current_page -= 1
                continue
            elif nav_choice.lower() in ['done', 'skip']:
                break
        else:
            nav_choice = input("\nEnter numbers (e.g., 1,3,5) or 'skip' to continue: ").strip()
            if nav_choice.lower() == 'skip':
                return desired_outcomes  # Return existing desired outcomes if skipped
    
        try:
            selected = []
            for num in nav_choice.split(','):
                num = int(num.strip())
                if num in interests:
                    selected.append(interests[num])
            if selected:
                print(f"\n✅ Selected interests: {', '.join(selected)}")
                for interest in selected:
                    topics = interest_categories.get(interest, [])
                    desired_outcomes.extend(topics)
                return list(set(desired_outcomes))  # Return unique desired outcomes
            else:
                print("\n⚠️ No valid interests selected.")
        except ValueError:
            print("❌ Invalid input. Please enter valid numbers.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}. Please try again.")
    
    return desired_outcomes


def load_interest_categories():
    '''
    Load interest categories from JSON file
    Return:
        Dictionary of interest categories and their related terms
    '''
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interest_categories.json")
        
        with open(file_path, 'r') as f:
            interest_categories = json.load(f)
            
        return interest_categories
    except Exception as e:
        print(f"⚠️ Error loading interest categories: {e}")
        return {
            "artificial intelligence": ["Artificial Intelligence"],
            "machine learning": ["Machine Learning"],
            "web": ["JavaScript", "Web Development"],
            "data science": ["Data Science"],
            "computer vision": ["Computer Vision"]
        }

def load_knowledge_tags():
    """Load knowledge tags from JSON file"""
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_tags.json")
        with open(path, "r") as file:
            tags = json.load(file)
        return tags
    except Exception as e:
        print(f"⚠️ Error loading knowledge tags: {e}")
        return {
            "programming_languages": ["Python", "Java", "C++", "JavaScript"],
            "math_tags": ["Linear Algebra", "Calculus", "Statistics", "Discrete Math"]
        }

tags = load_knowledge_tags()
PROGRAMMING_LANGUAGES = set(tags.get('programming_languages', []))
MATH_AREAS = set(tags.get('math_tags', []))

def print_section_header(title, width=60, char="="):
    """Print a formatted section header"""
    print("\n" + char*width)
    print(title)
    print(char*width)

def display_tags_simple(tags, category_name):
    """Display tags in a simple numbered list format"""
    print(f"\nAvailable {category_name} ({len(tags)} total):")
    print("-" * 50)
    
    # Display in multiple columns for better readability
    tags_list = sorted(list(tags))
    col_width = max(len(tag) for tag in tags_list) + 5
    items_per_row = 2
    
    for i in range(0, len(tags_list), items_per_row):
        row_items = tags_list[i:i+items_per_row]
        row = ""
        for idx, tag in enumerate(row_items):
            row += f"{i+idx+1:2}. {tag:<{col_width}} "
        print(row)
    
    print("-" * 50)

def select_from_numbered_list(items, prompt):
    """Let the user select multiple items from a numbered list"""
    selected = []
    
    items = sorted(list(items))
    display_tags_simple(items, "Options")
    
    print("\nEnter numbers corresponding to your choices (comma-separated, e.g., 1,3,5)")
    print("Or type 'none' if you don't have any")
    
    choice = input(f"{prompt}: ").strip().lower()
    if choice == 'none':
        return []
    
    try:
        for num in choice.split(','):
            idx = int(num.strip()) - 1
            if 0 <= idx < len(items):
                selected.append(items[idx])
        
        if selected:
            print(f"✅ Selected: {', '.join(selected)}")
        
        return selected
    except ValueError:
        print("⚠️ Invalid input. Please enter numbers separated by commas.")
        return select_from_numbered_list(items, prompt)

def get_student_input():
    """
    Streamlined student input process that aligns with the recommendation system
    """
    print_section_header("🎓 STUDENT PROFILE CREATION")
    print("\nThis will create your student profile for personalized course recommendations.")
    
    # Basic information
    nuid = input("\nEnter your NUID: ")
    name = input("Enter your full name: ")
    
    # Programming experience
    print_section_header("💻 PROGRAMMING EXPERIENCE")
    print("\nSelect the programming languages you know, then rate your proficiency (1-5)")
    
    prog_languages = select_from_numbered_list(PROGRAMMING_LANGUAGES, "Select programming languages")
    prog_exp = {}
    for lang in prog_languages:
        while True:
            try:
                proficiency = int(input(f"Rate your proficiency in {lang} (1-5, where 5 is expert): "))
                if 1 <= proficiency <= 5:
                    prog_exp[lang] = proficiency
                    break
                else:
                    print("⚠️ Please enter a number between 1 and 5.")
            except ValueError:
                print("⚠️ Please enter a valid number.")
    
    # Math experience
    print_section_header("📐 MATHEMATICS EXPERIENCE")
    print("\nSelect the math areas you know, then rate your proficiency (1-5)")
    
    math_areas = select_from_numbered_list(sorted(list(MATH_AREAS)), 
                                          "Select math areas")
    math_exp = {}
    for area in math_areas:
        while True:
            try:
                proficiency = int(input(f"Rate your proficiency in {area} (1-5, where 5 is expert): "))
                if 1 <= proficiency <= 5:
                    math_exp[area] = proficiency
                    break
                else:
                    print("⚠️ Please enter a number between 1 and 5.")
            except ValueError:
                print("⚠️ Please enter a valid number.")
    
    # Completed courses - simplified to just the essential information
    completed_courses = {}
    print_section_header("📚 COMPLETED COURSES")
    print("\nEnter courses you've already completed (just the essential details)")
    
    if input("Have you completed any courses? (yes/no): ").strip().lower() in ["yes", "y"]:
        while True:
            subject_code = input("\nEnter subject code (or 'done' to finish): ").strip()
            if subject_code.lower() in ["done", "d"]:
                break
            
            # Simplified course details
            details = {
                "Subject Name": input(f"Enter name for {subject_code}: "),
                "Weekly Workload (hours)": float(input(f"Enter weekly workload (hours) for {subject_code}: ")),
                "Final Grade": float(input(f"Enter your final grade (0-100) for {subject_code}: ")),
                "Rating": int(input(f"Rate your experience with {subject_code} from 1-5: "))
            }
            completed_courses[subject_code] = details
    
    # Core subjects and interests - aligned with recommendation system
    print_section_header("🧩 CORE SUBJECTS")
    print("\nEnter required subjects for your program (e.g., CS5100, CS5200)")
    
    core_subjects_input = input("Core subjects (comma-separated): ")
    core_subjects = [subject.strip() for subject in core_subjects_input.split(',') if subject.strip()]
    
    # Interests using the same categories as the recommendation system
    print_section_header("🎯 LEARNING GOALS")
    print("\nSelect what you want to learn or focus on in your courses")
    
    desired_outcomes = get_user_interests(mode='new')
    
    # Build the student data structure
    student_data = {
        "NUID": nuid,
        "name": name,
        "programming_experience": prog_exp,
        "math_experience": math_exp,
        "completed_courses": completed_courses, 
        "core_subjects": core_subjects,
        "desired_outcomes": desired_outcomes
    }

    # Insert into MongoDB
    collection.update_one({"NUID": nuid}, {"$set": student_data}, upsert=True)

    print(f"\n✅ Student profile created successfully for NUID: {nuid}")
    return student_data

# ========================== SHARED UTILITY FUNCTIONS ==========================

def clear_screen():
    """Clear the terminal screen for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_loading_animation(message, duration=3):
    """Show a loading animation with the specified message."""
    print(message, end="")
    for _ in range(duration):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print("\n")

def print_section_header(title, width=60, char="="):
    """Print a formatted section header."""
    print("\n" + char * width)
    print(title)
    print(char * width)

# ========================== STATUS REPORTING FUNCTIONS ==========================

def get_enrollment_status(seats, enrollments):
    """Get enrollment messages based on the given seats and enrollments."""
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

def get_burnout_status(burnout_score):
    """Get the burnout status based on the burnout score."""
    if burnout_score is None:
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
    """Calculate difficulty rating based on prerequisite match and workload."""
    burnout = calculate_burnout(student_data, subject_code, subjects_df)
    completed_courses = set(get_student_completed_courses(student_data))
    unmet_prereqs = get_unmet_prerequisites(subjects_df, subject_code, completed_courses)
    
    if unmet_prereqs:
        return "🔴 High difficulty. Missing prerequisites may make this course challenging."
    elif burnout > 0.7:
        return "🟠 Moderate-high difficulty. Prepare to allocate significant study time."
    elif burnout > 0.4:
        return "🟡 Moderate difficulty. Should be manageable with regular study."
    else:
        return "🟢 Standard difficulty. Aligns well with your current knowledge level."

# ========================== CORE RECOMMENDATION LOGIC ==========================

def get_additional_interests():
    """User  input for additional interests."""
    print_section_header("🔍 REFINE YOUR RECOMMENDATIONS")
    print("\nWhat other areas are you interested in? (Select one or more numbers, separated by commas)")
    
    interest_categories = load_interest_categories()
    interests = {i: category for i, category in enumerate(interest_categories.keys(), 1)}
    
    col_width = max(len(interest) for interest in interests.values()) + 5
    chunk_size = 20
    total_pages = (len(interests) + chunk_size - 1) // chunk_size
    current_page = 1
    
    while True:
        start_idx = (current_page - 1) * chunk_size + 1
        end_idx = min(current_page * chunk_size, len(interests))
        
        print(f"\nPage {current_page}/{total_pages}:")
        for i in range(start_idx, end_idx + 1, 2):
            if i + 1 <= end_idx:
                print(f"{i:2}. {interests[i]:<{col_width}} {i+1:2}. {interests[i+1]}")
            else:
                print(f"{i:2}. {interests[i]}")
        
        if total_pages > 1:
            nav_choice = input("\nEnter numbers to select interests, 'n' for next page, 'p' for previous page, or 'done' when finished: ").strip()
            if nav_choice.lower() == 'n' and current_page < total_pages:
                current_page += 1
                continue
            elif nav_choice.lower() == 'p' and current_page > 1:
                current_page -= 1
                continue
            elif nav_choice.lower() in ['done', 'skip']:
                break
        else:
            nav_choice = input("\nEnter numbers (e.g., 1,3,5) or 'skip' to continue: ").strip()
            if nav_choice.lower() == 'skip':
                return []
    
        try:
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

def filter_courses_by_interests(available_subjects, interests, subjects_df):
    """Filter available courses based on student interests."""
    if not interests:
        return available_subjects
    
    interest_categories = load_interest_categories()
    subject_scores = {subject_id: 0 for subject_id in available_subjects}
    
    for subject_id in available_subjects:
        subject_row = subjects_df[subjects_df['subject_id'] == subject_id]
        if subject_row.empty:
            continue
            
        subject_name = subject_row.iloc[0]['subject_name']
        subject_text = f"{subject_name} {subject_row.iloc[0].get('programming_knowledge_needed', '')} {subject_row.iloc[0].get('math_requirements', '')} {subject_row.iloc[0].get('course_outcomes', '')}".lower()
        
        for interest in interests:
            if interest.lower() in subject_text:
                subject_scores[subject_id] += 3
            if interest in interest_categories:
                for term in interest_categories[interest]:
                    if term.lower() in subject_text:
                        subject_scores[subject_id] += 1
    
    scored_subjects = [(subject_id, score) for subject_id, score in subject_scores.items() if score > 0]
    scored_subjects.sort(key=lambda x: x[1], reverse=True)
    
    return [subject_id for subject_id, _ in scored_subjects] if scored_subjects else available_subjects

def run_genetic_algorithm_with_animation(available_subjects, completed_courses, student_data, core_subjects, message="Running genetic algorithm"):
    """Run the genetic algorithm with a loading animation."""
    core_subjects = list(core_subjects)
    completed_courses = set(completed_courses)
    show_loading_animation(message)
    return genetic_algorithm(available_subjects, completed_courses, student_data, core_subjects)


def convert_ga_schedule_to_recommendations(schedule, student_data, subjects_df, interests):
    """Convert genetic algorithm schedule to recommendation format."""
    recommended_courses = []
    interest_categories = load_interest_categories()
    
    for subject_id in schedule:
        subject_row = subjects_df[subjects_df['subject_id'] == subject_id]
        if subject_row.empty:
            continue
            
        subject_name = subject_row.iloc[0]['subject_name']
        burnout_score = calculate_burnout(student_data, subject_id, subjects_df)
        utility_score = calculate_utility(student_data, subject_id, subjects_df)
        
        seats = random.randint(20, 100)
        enrollments = random.randint(0, seats)
        match_score = calculate_outcome_alignment_score(student_data, subject_id, subjects_df)
        
        enrollment_ratio = enrollments / seats if seats > 0 else 0
        likelihood = 1 - (enrollment_ratio * 0.8)
        
        reasons = generate_recommendation_reasons(subject_name, interests, burnout_score, utility_score, subject_id, student_data)
        
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

def generate_recommendation_reasons(subject_name, interests, burnout_score, utility_score, subject_id, student_data):
    """Generate reasons for course recommendations."""
    reasons = []
    subjects_df = load_course_data()
    
    if interests:
        matching_interests = [interest for interest in interests if interest.lower() in subject_name.lower()]
        if matching_interests:
            reasons.append(f"Aligns with your interest in {', '.join(set(matching_interests)[:2])}")
    
    reasons.append("Selected by genetic algorithm for optimal academic fit")
    
    if utility_score > 0.7:
        reasons.append("High academic utility for your program")
    elif utility_score > 0.5:
        reasons.append("Good academic utility for your program")
    
    if burnout_score < 0.3:
        reasons.append("Low burnout risk with your background")
    
    completed_courses = set(get_student_completed_courses(student_data))
    prereqs = get_unmet_prerequisites(subjects_df, subject_id, completed_courses)
    if not prereqs:
        reasons.append("You meet all prerequisites for this course")
    
    if len(reasons) < 3:
        reasons.append("Fits well within your overall academic plan")
    
    return reasons

def identify_competitive_courses(recommended_courses):
    """Identify highly competitive courses from recommendations."""
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
    
    regular.sort(key=lambda x: x['match_score'], reverse=True)
    competitive.sort(key=lambda x: x['match_score'], reverse=True)
    
    return regular, competitive

# ========================== DISPLAY FUNCTIONS ==========================

def display_recommendations(recommended_courses, highly_competitive_courses, subjects_df, student_data, round_num=1):
    """Format and display the recommendations for the user."""
    clear_screen()
    print_section_header(f"🎓 COURSE RECOMMENDATIONS (ROUND {round_num})")
    
    if recommended_courses:
        print("\n🎯 RECOMMENDED COURSES:")
        for i, course in enumerate(recommended_courses, 1):
            display_course_details(course, subjects_df, student_data, i)
    else:
        print("\n⚠️ No new courses found matching your immediate criteria.")
    
    if highly_competitive_courses:
        print("\n⚠️ HIGHLY COMPETITIVE COURSES:")
        for i, course in enumerate(highly_competitive_courses, 1):
            display_course_details(course, subjects_df, student_data, i, is_competitive=True)
    
    return len(recommended_courses) + len(highly_competitive_courses) > 0

def display_course_details(course, subjects_df, student_data, index, is_competitive=False):
    """Display details for a single course."""
    seats = course.get('seats', 0)
    enrollments = course.get('enrollments', 0)
    
    match_score = course.get('match_score', 0)
    match_emoji = "🏆" if is_competitive else "🌟" if match_score > 0.8 else "✨" if match_score > 0.6 else "👍" if match_score > 0.4 else "👌"
    
    print(f"\n{index}. {match_emoji} {course['subject_code']}: {course['name']}")
    print(f"   Match Score: {course['match_score']:.1%}")
    
    if course.get('burnout_score') is not None and course.get('utility_score') is not None:
        burnout_status = get_burnout_status(course['burnout_score'])
        print(f"   Burnout Risk: {course['burnout_score']:.2f}")
        print(f"   Academic Utility: {course['utility_score']:.2f}")
        print(f"   {burnout_status}")
        
        difficulty_status = get_difficulty_status(course['subject_code'], subjects_df, student_data)
        print(f"   {difficulty_status}")
    
    completed_courses = set(get_student_completed_courses(student_data))
    unmet_prereqs = get_unmet_prerequisites(subjects_df, course['subject_code'], completed_courses)
    if unmet_prereqs:
        print(f"   ⚠️ Missing prerequisites: {', '.join(unmet_prereqs)}")
    
    print(f"   Reasons for recommendation:")
    for reason in course.get('reasons', []):
        print(f"   • {reason}")
    
    if seats > 0 and enrollments > 0:
        print(f"   Current Status: {seats - enrollments} seats remaining ({enrollments}/{seats} filled)")
        enrollment_status = get_enrollment_status(seats, enrollments)
        print(f"   {enrollment_status}")
    else:
        print("   ⚠️ Enrollment data not available")
    
    if seats > enrollments:
        likelihood_percent = course.get('likelihood', 0) * 100
        likelihood_emoji = "🔥" if likelihood_percent > 80 else "✅" if likelihood_percent > 50 else "⚠️"
        print(f"   Enrollment Likelihood: {likelihood_emoji} {likelihood_percent:.1f}%")
    
    if is_competitive:
        print("   ⚠️ Note: This is a highly competitive course due to high demand")
        if seats <= enrollments:
            print("   💡 Tip: Consider registering for this course in a future semester when you'll have higher priority")
        else:
            print("   💡 Tip: If interested, prepare to register immediately when registration opens")

def display_final_schedule(recommended_history, subjects_df, scores_df, nuid):
    """Display the final schedule with summary statistics and save to database."""
    print_section_header("🏁 FINAL RECOMMENDED SCHEDULE")
    
    total_burnout = 0
    total_utility = 0
    course_count = 0
    
    courses_per_semester = 2
    semesters = []
    current_semester = []
    
    for i, subject_code in enumerate(recommended_history, 1):
        current_semester.append(subject_code)
        if i % courses_per_semester == 0:
            semesters.append(current_semester)
            current_semester = []
    
    if current_semester:
        semesters.append(current_semester)
    
    for i, semester_courses in enumerate(semesters, 1):
        print(f"\nSemester {i}:")
        for subject_code in semester_courses:
            subject_name = get_subject_name(subjects_df, subject_code)
            burnout_score = get_burnout_score(subject_code, scores_df)
            utility_score = get_utility_score(subject_code, scores_df)

            print(f"  • {subject_code}: {subject_name}")
            if burnout_score is not None and utility_score is not None:
                burnout_status = get_burnout_status(burnout_score)
                print(f"    Burnout Risk: {burnout_score:.2f}")
                print(f"    Academic Utility: {utility_score:.2f}")
                print(f"    {burnout_status}")
                
                total_burnout += burnout_score
                total_utility += utility_score
                course_count += 1
    
    avg_burnout = total_burnout / course_count if course_count > 0 else 0
    avg_utility = total_utility / course_count if course_count > 0 else 0
    
    print("\n" + "-" * 60)
    print("📊 Schedule Summary:")
    print(f"  • Total Courses: {course_count}")
    print(f"  • Average Burnout Risk: {avg_burnout:.2f}")
    print(f"  • Average Academic Utility: {avg_utility:.2f}")
    
    if avg_burnout > 0.7:
        print("  • ⚠️ Warning: This schedule has a high overall burnout risk.")
        print("    Consider spreading high-intensity courses across multiple semesters.")
    elif avg_burnout > 0.5:
        print("  • 🟡 Note: This schedule has a moderate overall burnout risk.")
        print("    Be prepared for a challenging but manageable workload.")
    else:
        print("  • 🟢 Good news: This schedule has a balanced overall burnout risk.")
        print("    The workload should be manageable with good time management.")
    
    try:
        save_final_schedule_to_db(recommended_history, subjects_df, scores_df, nuid)
    except Exception as e:
        print(f"\n⚠️ Could not save final schedule to database: {e}")

# ========================== MAIN RECOMMENDATION FUNCTIONS ==========================

def prompt_for_student_info():
    """Prompt for student information with options to login or create new account."""
    print_section_header("🎓 WELCOME TO YOUR PERSONALIZED COURSE RECOMMENDER")
    print("\nThis system will help you find courses that match your interests,")
    print("academic background, and provide insights on enrollment status and burnout risk.")
    
    print("\nPlease select an option:")
    print("1. Log in with existing NUID")
    print("2. Create a new student profile")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        nuid = input("\nPlease enter your NUid: ")
        while not nuid.strip():
            print("❌ Invalid NUid. Please try again.")
            nuid = input("Enter your NUid: ")
        
        try:
            student_data = load_student_data(nuid)
            name = student_data['name'].iloc[0]
            print(f"✅ Welcome back, {name}!")
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
        print("\nLet's create a new student profile for you!")
        student_data = get_student_input()
        nuid = student_data["NUID"]
        print(f"✅ Profile created successfully for student {nuid}")
    
    else:
        print("❌ Invalid choice. Defaulting to login.")
        nuid = prompt_for_student_info()

    try:
        calculate_scores(nuid)
        print("✅ Burnout scores calculated successfully")
    except Exception as e:
        print(f"⚠️ Error calculating burnout scores: {e}")
    
    return nuid

def process_blacklist_choice(choice, best_semester):
    """Process the user's choice for blacklisting a course."""
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(best_semester):
            return best_semester[idx]
    except ValueError:
        if choice in best_semester:
            return choice
    return None

def recommend_schedule(nuid):
    """Main function for recommending a schedule for a user."""
    blacklist = set()
    final_list = []
    scores_df = load_scores(nuid)
    
    print_section_header("🎓 COURSE RECOMMENDATION SYSTEM")
    
    try:
        student_data = load_student_data(nuid)
        subjects_df = load_course_data()
        completed_courses = get_student_completed_courses(student_data)
        core_subjects = list(get_student_core_subjects(student_data))
        core_remaining = [c for c in core_subjects if c not in completed_courses]
        
        plan = [[] for _ in range(SEMESTERS)]
        taken = set(completed_courses.copy())
        all_subjects = subjects_df['subject_id'].tolist()
        initial_interests = get_user_interests(student_data, mode='add')

        save_desired_outcomes(nuid, initial_interests)
        
        print_section_header("🔮 INTERACTIVE SCHEDULE PLANNER")
        print(f"For each of the {SEMESTERS} semesters, our genetic algorithm will suggest the best combination of courses.")
        print("You can accept or reject the suggestions, and we'll optimize the final schedule.")
        
        for sem_idx in range(SEMESTERS):
            available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
            if initial_interests:
                available_subjects = filter_courses_by_interests(available_subjects, initial_interests, subjects_df)
            
            if len(available_subjects) < COURSES_PER_SEMESTER:
                print(f"⚠️ Not enough subjects left for Semester {sem_idx + 1}. Stopping.")
                break
            
            print("\n" + "-" * 60)
            print(f"🗓️ PLANNING SEMESTER {sem_idx + 1}")
            print("-" * 60)
            
            while True:
                best_semester = run_genetic_algorithm_with_animation(
                    available_subjects, taken, student_data, core_remaining
                )
                
                plan[sem_idx] = best_semester
                display_plan(plan, student_data, taken)
                
                fitness = calculate_fitness(best_semester, taken, student_data, core_remaining)
                print(f"\nSemester Fitness Score: {fitness:.2f}")
                
                core_in_semester = [c for c in best_semester if c in core_remaining]
                if core_in_semester:
                    print(f"Core courses included: {', '.join(core_in_semester)}")
                
                if len(core_in_semester) < min(len(core_remaining), COURSES_PER_SEMESTER):
                    print(f"Note: {len(core_remaining) - len(core_in_semester)} core courses still need to be scheduled.")
                
                satisfied = input(f"\nAre you satisfied with Semester {sem_idx + 1}? (yes/no): ").lower()
                
                if satisfied == "yes":
                    final_list.extend(best_semester)
                    taken.update(best_semester)
                    print("Updating your knowledge profile based on these courses...")
                    programming_skills, math_skills = update_knowledge_profile(student_data, taken)
                    save_knowledge_profile(nuid, programming_skills, math_skills)
                    core_remaining = [c for c in core_remaining if c not in best_semester]
                    print(f"✅ Semester {sem_idx + 1} confirmed!")
                    break
                elif satisfied == "no":
                    print("\nWhich course would you like to remove from consideration?")
                    for i, course in enumerate(best_semester, 1):
                        course_name = get_subject_name(subjects_df, course)
                        print(f"{i}. {course} - {course_name}")
                    
                    choice = input("\nEnter the number or the subject code to remove: ")
                    remove_code = process_blacklist_choice(choice, best_semester)
                    
                    if remove_code:
                        blacklist.add(remove_code)
                        print(f"🚫 {remove_code} added to blacklist. Re-planning Semester {sem_idx + 1}...")
                        available_subjects = [s for s in all_subjects if s not in blacklist and s not in final_list]
                        if initial_interests:
                            available_subjects = filter_courses_by_interests(available_subjects, initial_interests, subjects_df)
                    else:
                        print("❌ Invalid selection. Please try again.")
                else:
                    print("❌ Please enter 'yes' or 'no'.")
        
        if core_remaining:
            print(f"\n⚠️ Warning: Core subjects {', '.join(core_remaining)} were not scheduled!")
        
        print_section_header("🔄 OPTIMIZING YOUR SCHEDULE")
        print("\nNow optimizing the initial schedule to minimize burnout...")
        show_loading_animation("Running optimization", 5)
        
        optimized_plan, total_burnout = optimize_schedule(plan, student_data, taken)
        plan = optimized_plan
        print(f"Initial Optimized Total Burnout: {total_burnout:.3f}")
        print("\n" + "-" * 60)
        print("📋 INITIAL OPTIMIZED PLAN")
        print("-" * 60)
        display_plan(plan, student_data, taken)
        
        print_section_header("🧬 FINAL GENETIC ALGORITHM OPTIMIZATION")
        print("\nRunning advanced genetic algorithm to find the optimal course order...")
        show_loading_animation("Running final optimization", 5)
        
        final_subjects = final_list.copy()
        initial_taken = set(student_data.iloc[0].get("completed_courses", {}))
        
        best_plan, best_burnout = rerun_genetic_algorithm(final_subjects, student_data, initial_taken)
        
        print(f"\nFinal Optimized Total Burnout: {best_burnout:.3f}")
        print(f"Improvement: {(total_burnout - best_burnout) / total_burnout:.1%} burnout reduction")
        
        print_section_header("🏆 FINAL OPTIMIZED SCHEDULE")
        display_plan(best_plan, student_data, initial_taken)
        
        try:
            save_plan_to_db(best_plan, nuid, -best_burnout, student_data, initial_taken)
            print("\n✅ Your optimized schedule has been saved to the database.")
            print(f"   You can access it anytime using your NUID: {nuid}")
            display_final_schedule(final_list, subjects_df, scores_df, nuid)
        except Exception as e:
            print(f"\n❌ Error saving schedule to database: {e}")
        
        return final_list
    except Exception as e:
        print(f"\n❌ Error in schedule planning: {e}")
        print("Please create a profile first using the profile creation tool.")
        return None

def browse_recommendations(nuid, semester=None, interests=None):
    """Browse recommendations without using the full GA planning process."""
    print_section_header("🔍 COURSE RECOMMENDATION BROWSER")
    print("\nThis will show you course recommendations based on your profile and interests")
    print("without going through the full schedule planning process.")
    
    student_data = load_student_data(nuid)
    subjects_df = load_course_data()
    completed_courses = get_student_completed_courses(student_data)
    core_subjects = get_student_core_subjects(student_data)
    all_subjects = [s for s in subjects_df['subject_id'].tolist() if s not in completed_courses]
    
    if not interests:
        interests = get_user_interests()
    
    available_subjects = filter_courses_by_interests(all_subjects, interests, subjects_df) if interests else all_subjects
    available_subjects = available_subjects[:50] if len(available_subjects) > 50 else available_subjects
    
    print("\nGenerating recommendations based on your profile and interests...")
    best_semester = run_genetic_algorithm_with_animation(available_subjects, completed_courses, student_data, core_subjects)
    
    recommendations = convert_ga_schedule_to_recommendations(best_semester, student_data, subjects_df, interests)
    regular_courses, competitive_courses = identify_competitive_courses(recommendations)
    
    display_recommendations(regular_courses, competitive_courses, subjects_df, student_data)
    
    more = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
    round_num = 2
    
    while more == 'yes':
        print("\nLet's refine your recommendations with more specific interests.")
        additional_interests = get_additional_interests()
        
        if additional_interests:
            interests = list(set(interests + additional_interests)) if interests else additional_interests
        
        shown_courses = [course['subject_code'] for course in regular_courses + competitive_courses]
        available_subjects = [s for s in available_subjects if s not in shown_courses]
        
        if not available_subjects:
            print("\n⚠️ No more courses available matching your criteria.")
            break
        
        available_subjects = available_subjects[:50] if len(available_subjects) > 50 else available_subjects
        
        print(f"\nGenerating new recommendations for round {round_num}...")
        best_semester = run_genetic_algorithm_with_animation(available_subjects, completed_courses, student_data, core_subjects, f"Running genetic algorithm for round {round_num}")
        
        recommendations = convert_ga_schedule_to_recommendations(best_semester, student_data, subjects_df, interests)
        regular_courses, competitive_courses = identify_competitive_courses(recommendations)
        
        # Display recommendations
        has_more = display_recommendations(regular_courses, competitive_courses, subjects_df, student_data, round_num)
        
        if not has_more:
            print("\n⚠️ No more courses available matching your criteria.")
            break
        
        # Ask if user wants to continue
        more = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
        round_num += 1
    
    return None

def save_final_schedule_to_db(recommended_history, subjects_df, scores_df, nuid):
    """
    Save the final displayed schedule to the database.
    
    Args:
        recommended_history (list): List of recommended courses
        subjects_df (DataFrame): DataFrame containing subject information
        scores_df (DataFrame): DataFrame containing burnout and utility scores
        nuid (str): Student NUID
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        # MongoDB connection
        MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"
        client = MongoClient(MONGO_URI)
        db = client["user_details"]
        final_schedules_collection = db["user_schedules"]
        users_collection = db["users"]
        
        # Get student information
        student_info = users_collection.find_one({"NUID": nuid})
        student_name = student_info.get("name", "Unknown") if student_info else "Unknown"
        
        # Calculate schedule structure
        courses_per_semester = 2
        semesters = []
        current_semester = []
        
        for i, subject_code in enumerate(recommended_history, 1):
            current_semester.append(subject_code)
            if i % courses_per_semester == 0:
                semesters.append(current_semester)
                current_semester = []
        
        if current_semester:
            semesters.append(current_semester)
        
        # Build detailed schedule with course information
        detailed_schedule = []
        total_burnout = 0
        total_utility = 0
        course_count = 0
        
        for sem_idx, semester_courses in enumerate(semesters, 1):
            semester_data = {
                "semester_number": sem_idx,
                "courses": []
            }
            
            for subject_code in semester_courses:
                subject_name = get_subject_name(subjects_df, subject_code)
                burnout_score = get_burnout_score(subject_code, scores_df)
                utility_score = get_utility_score(subject_code, scores_df)
                
                course_data = {
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "burnout_risk": burnout_score,
                    "academic_utility": utility_score,
                    "burnout_status": get_burnout_status(burnout_score)
                }
                
                semester_data["courses"].append(course_data)
                
                if burnout_score is not None and utility_score is not None:
                    total_burnout += burnout_score
                    total_utility += utility_score
                    course_count += 1
        
            detailed_schedule.append(semester_data)
        
        # Calculate averages and overall status
        avg_burnout = total_burnout / course_count if course_count > 0 else 0
        avg_utility = total_utility / course_count if course_count > 0 else 0
        
        if avg_burnout > 0.7:
            burnout_warning = "⚠️ Warning: This schedule has a high overall burnout risk. Consider spreading high-intensity courses across multiple semesters."
        elif avg_burnout > 0.5:
            burnout_warning = "🟡 Note: This schedule has a moderate overall burnout risk. Be prepared for a challenging but manageable workload."
        else:
            burnout_warning = "🟢 Good news: This schedule has a balanced overall burnout risk. The workload should be manageable with good time management."
        
        # Create the schedule document
        schedule_doc = {
            "nuid": nuid,
            "student_name": student_name,
            "created_at": datetime.datetime.now(),
            "schedule_type": "final_display",
            "detailed_schedule": detailed_schedule,
            "flat_courses": recommended_history,
            "summary": {
                "total_courses": course_count,
                "average_burnout_risk": avg_burnout,
                "average_academic_utility": avg_utility,
                "burnout_assessment": burnout_warning,
                "semesters": len(semesters),
                "courses_per_semester": courses_per_semester
            }
        }
        
        # Check for existing final schedule for this student
        existing_schedule = final_schedules_collection.find_one({"nuid": nuid})
        
        if existing_schedule:
            # Update existing schedule
            schedule_doc["_id"] = existing_schedule["_id"]
            schedule_doc["version"] = existing_schedule.get("version", 1) + 1
            schedule_doc["previous_versions"] = existing_schedule.get("previous_versions", [])
            
            # Add the current version to previous_versions
            prev_version = {k: v for k, v in existing_schedule.items() if k != "previous_versions"}
            schedule_doc["previous_versions"].append(prev_version)
            
            final_schedules_collection.replace_one({"_id": existing_schedule["_id"]}, schedule_doc)
            print(f"\n✅ Updated existing final schedule for NUID {nuid} (version {schedule_doc['version']})")
        else:
            # Create new schedule
            schedule_doc["version"] = 1
            schedule_doc["previous_versions"] = []
            final_schedules_collection.insert_one(schedule_doc)
            print(f"\n✅ Saved final schedule to database for NUID {nuid}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error saving final schedule to database: {e}")
        return False

if __name__ == "__main__":
    try:
        # Start the recommendation process
        nuid = prompt_for_student_info()
        
        # Ask what mode user wants
        print_section_header("SELECT RECOMMENDATION MODE")
        print("Please select an option:")
        print("1. Full Schedule Planning - Create an optimized multi-semester plan")
        print("2. Recommendation Browser - Just browse recommended courses")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()

        student_data = load_student_data(nuid)
        interests = get_student_desired_outcomes(student_data)
        
        if choice == "1":
            recommend_schedule(nuid)
        elif choice == "2":
            try:
                semester = int(input("\nWhich semester are you in? "))
                browse_recommendations(nuid, semester, interests)
            except ValueError:
                print("⚠️ Invalid semester number. Continuing without semester information.")
                browse_recommendations(nuid, None, interests)
        else:
            print("Invalid option. Defaulting to full schedule planning.")
            recommend_schedule(nuid)
        
        # Final message
        print_section_header("🎉 RECOMMENDATION PROCESS COMPLETE")
        print("\nThank you for using the Course Recommendation System!")
        print("We hope these recommendations help you plan your academic journey.")
        print("\nGood luck with your studies! 📚")
        
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please try again later.")