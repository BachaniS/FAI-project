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
    """Display tags in a numbered list"""
    print(f"\nAvailable {category_name} ({len(tags)} total):")
    print("-" * 50)
    
    for i, tag in enumerate(tags):
        print(f"{i+1:2}. {tag}")
    
    print("-" * 50)

def get_student_input():
    """Fill out student profile and store under NUID"""
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
    
    completed_courses = input("Enter any completed courses (comma-separated, e.g., CS5100, CS5200, CS6130): ").split(',')
    core_subjects = input("Enter core subjects for your program (comma-separated, e.g., CS5100, CS5200): ").split(',')
    desired_outcomes = input("What do you want to learn? (comma-separated, e.g., AI, ML, Deep Learning): ").split(',')

    student_data = {
        "NUID": nuid,
        "programming_experience": prog_exp,
        "math_experience": math_exp,
        "completed_courses": [course.strip() for course in completed_courses if course.strip()],
        "core_subjects": [subject.strip() for subject in core_subjects if subject.strip()],
        "desired_outcomes": [outcome.strip() for outcome in desired_outcomes if outcome.strip()]
    }

    # Insert into MongoDB, overwrites if NUID already exists
    collection.update_one({"NUID": nuid}, {"$set": student_data}, upsert=True)

    print(f"Student data saved under id: {nuid}")
    return student_data

if __name__ == "__main__":
    student_data = get_student_input()