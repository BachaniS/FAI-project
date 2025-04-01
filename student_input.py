import pandas as pd
import json

def save_student_data(nuid, prog_exp, math_exp, completed_courses, core_subjects, desired_outcomes):
    completed_courses_dict = {code: {"Avg Final Grade": 85} for code in completed_courses.split(",")} if completed_courses else {}
    student_data = {
        'NUid': nuid,
        'programming_experience': prog_exp,
        'math_experience': math_exp,
        'completed_courses_details': json.dumps(completed_courses_dict),
        'core_subjects': core_subjects,
        'desired_outcomes': desired_outcomes
    }
    df = pd.DataFrame([student_data])
    df.to_csv(f'student_{nuid}.csv', index=False)
    print(f"Student data saved to student_{nuid}.csv")

def main():
    nuid = input("Enter your NUid: ")
    prog_exp = input("Enter your programming experience (e.g., Python, Java): ")
    math_exp = input("Enter your math experience (e.g., Calculus, Algebra): ")
    completed_courses = input("Enter completed course codes (comma-separated, e.g., CS5001,CS5002) or leave blank: ")
    core_subjects = input("Enter core subjects (comma-separated, e.g., CS5010,CS5100): ")
    desired_outcomes = input("Enter desired outcomes (comma-separated, e.g., Python,Algorithms): ")
    save_student_data(nuid, prog_exp, math_exp, completed_courses, core_subjects, desired_outcomes)

if __name__ == "__main__":
    main()