from pymongo import MongoClient
import os 
import json

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["user_details"]
collection = db["users"]

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

def select_interests():
    """Let the user select interests from the same categories used in recommendations"""
    print_section_header("🔍 SELECT YOUR INTERESTS")
    print("\nYour interests help us recommend courses that align with your goals.")
    
    interest_categories = load_interest_categories()
    
    # Create a numbered list of all categories
    interests = list(interest_categories.keys())
    
    # Display interests in a readable format
    print(f"\nAvailable Interest Categories ({len(interests)} total):")
    print("-" * 50)
    
    col_width = max(len(interest) for interest in interests) + 5
    items_per_row = 2
    
    for i in range(0, len(interests), items_per_row):
        row_items = interests[i:i+items_per_row]
        row = ""
        for idx, interest in enumerate(row_items):
            row += f"{i+idx+1:2}. {interest:<{col_width}} "
        print(row)
    
    print("-" * 50)

    selected_interests = select_from_numbered_list(interests, "Select your interests")
    # Collect all topics related to the selected interests
    desired_outcomes = []
    for interest in selected_interests:
        topics = interest_categories.get(interest, [])
        desired_outcomes.extend(topics)
    
    # Remove duplicates if necessary
    desired_outcomes = list(set(desired_outcomes))
    
    # Get user selection
    return 

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
    
    desired_outcomes = select_interests()
    
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

if __name__ == "__main__":
    student_data = get_student_input()