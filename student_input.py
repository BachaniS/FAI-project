import pandas as pd
import json

def get_student_input():
    nuid = input("Enter your NUid: ")
    prog_exp = input("Enter your programming experience (e.g., Python, Java): ")
    math_exp = input("Enter your math experience (e.g., Linear Algebra, Calculus): ")
    completed = input("Have you completed any courses? (yes/no): ").lower()
    
    completed_courses = {}
    if completed == "yes":
        while True:
            subject_code = input("Enter subject code (or 'done' to finish): ")
            if subject_code.lower() == "done":
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
                "rating": int(input(f"Rate {subject_code} from 1-5: "))
            }
            completed_courses[subject_code] = details
    
    core_subjects = input("Enter core subjects for your program (comma-separated, e.g., CS5100,CS5200): ")
    desired_outcomes = input("What do you want to learn? (comma-separated, e.g., AI, ML, Deep Learning): ")
    
    student_data = {
        "NUid": nuid,
        "programming_experience": prog_exp,
        "math_experience": math_exp,
        "completed_courses": completed_courses,
        "core_subjects": core_subjects,
        "desired_outcomes": desired_outcomes
    }
    
    # Save to CSV
    df = pd.DataFrame([{
        "NUid": nuid,
        "programming_experience": prog_exp,
        "math_experience": math_exp,
        "completed_courses": ",".join(completed_courses.keys()) if completed_courses else "",
        "core_subjects": core_subjects,
        "desired_outcomes": desired_outcomes,
        "completed_courses_details": json.dumps(completed_courses)  # Store details as JSON string
    }])
    df.to_csv(f"student_{nuid}.csv", index=False)
    
    return student_data

if __name__ == "__main__":
    student_data = get_student_input()
    print(f"Student data saved to student_{student_data['NUid']}.csv")