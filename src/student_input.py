from pymongo import MongoClient

MONGO_URI = "mongodb+srv://cliftaus:US1vE3LSIWq379L9@burnout.lpo5x.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["user_details"]
collection = db["users"]

PROGRAMMING_LANGUAGES = [
    "Python", "Java", "C++", "JavaScript", "C#", "R", "MATLAB", 
    "Go", "Rust", "Swift", "Kotlin", "PHP", "Ruby", "TypeScript",
    "SQL", "Scala", "Julia", "Haskell", "Perl", "Assembly"
]

MATH_AREAS = [
    "Calculus", "Linear Algebra", "Statistics", "Probability", 
    "Discrete Mathematics", "Number Theory", "Graph Theory", 
    "Differential Equations", "Numerical Analysis", "Real Analysis",
    "Complex Analysis", "Topology", "Abstract Algebra", "Optimization",
    "Game Theory", "Set Theory", "Logic", "Geometry", "Trigonometry",
    "Combinatorics"
]

def display_tags_simple(tags, category_name):
    """Display tags in a simple numbered list format"""
    print(f"\nAvailable {category_name} ({len(tags)} total):")
    print("-" * 50)
    
    for i, tag in enumerate(tags):
        print(f"{i+1:2}. {tag}")
    
    print("-" * 50)

def get_student_input():
    nuid = input("Enter your NUID: ")
    
    display_tags_simple(PROGRAMMING_LANGUAGES, "Programming Languages")
    prog_languages = input("Enter your programming languages (comma-separated, e.g., Python, Java, C++): ").split(',')
    prog_exp = {}
    for lang in map(str.strip, prog_languages):
        if lang:
            proficiency = int(input(f"Rate your proficiency in {lang} (1-5, where 5 is expert): "))
            prog_exp[lang] = proficiency

    display_tags_simple(MATH_AREAS, "Math Areas")
    math_areas = input("Enter your math areas (comma-separated, e.g., Linear Algebra, Calculus, Statistics): ").split(',')
    math_exp = {}
    for area in map(str.strip, math_areas):
        if area:
            proficiency = int(input(f"Rate your proficiency in {area} (1-5, where 5 is expert): "))
            math_exp[area] = proficiency
    '''
    completed_courses = {}
    if input("Have you completed any courses? (yes/no): ").strip().lower() in ["yes", "y"]:
        while True:
            subject_code = input("Enter subject code (or 'done' to finish): ").strip()
            if subject_code.lower() in ["done", "d"]:
                break
            details = {
                "Subject Names": input(f"Enter name for {subject_code}: "),
                "Course Outcomes": input(f"Enter course outcomes for {subject_code} (comma-separated): "),
                "Programming Knowledge Needed": input(f"Enter programming knowledge needed for {subject_code}: "),
                "Math Requirements": input(f"Enter math requirements for {subject_code}: "),
                "Other Requirements": input(f"Enter other requirements for {subject_code}: "),
                "Weekly Workload (hours)": float(input(f"Enter weekly workload (hours) for {subject_code}: ")),
                "Assignments #": int(input(f"Enter number of assignments for {subject_code}: ")),
                "Hours per Assignment": float(input(f"Enter hours per assignment for {subject_code}: ")),
                "Assignment Weight": float(input(f"Enter assignment weight (0-1) for {subject_code}: ")),
                "Avg Assignment Grade": float(input(f"Enter your average assignment grade for {subject_code}: ")),
                "Project Weight": float(input(f"Enter project weight (0-1) for {subject_code}: ")),
                "Avg Project Grade": float(input(f"Enter your average project grade for {subject_code}: ")),
                "Exam #": int(input(f"Enter number of exams for {subject_code}: ")),
                "Avg Exam Grade": float(input(f"Enter your average exam grade for {subject_code}: ")),
                "Exam Weight": float(input(f"Enter exam weight (0-1) for {subject_code}: ")),
                "Avg Final Grade": float(input(f"Enter your final grade for {subject_code}: ")),
                "Prerequisite": input(f"Enter prerequisite for {subject_code}: "),
                "Corequisite": input(f"Enter corequisite for {subject_code}: "),
                "Rating": int(input(f"Rate {subject_code} from 1-5: "))
            }
            completed_courses[subject_code] = details
    '''
    core_subjects = input("Enter core subjects for your program (comma-separated, e.g., CS5100, CS5200): ").split(',')
    desired_outcomes = input("What do you want to learn? (comma-separated, e.g., AI, ML, Deep Learning): ").split(',')

    student_data = {
        "NUid": nuid,
        "programming_experience": prog_exp,
        "math_experience": math_exp,
        #"completed_courses": completed_courses,
        "core_subjects": [subject.strip() for subject in core_subjects if subject.strip()],
        "desired_outcomes": [outcome.strip() for outcome in desired_outcomes if outcome.strip()]
    }

    # Insert into MongoDB
    collection.update_one({"NUid": nuid}, {"$set": student_data}, upsert=True)

    print(f"Student data saved under id: {nuid}")
    return student_data

if __name__ == "__main__":
    student_data = get_student_input()