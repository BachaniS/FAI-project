from ga_recommender import generate_recommendations, save_schedule, load_burnout_scores
from utils import (
    load_subject_data, 
    prerequisites_satisfied, 
    standardize_student_data, 
    load_burnout_scores,
    get_enrollment_status
)
from utils import calculate_enrollment_priority

def get_burnout_status(burnout_score, utility_score):
    '''
    Get the burnout status based on utility and burnout
    Params:
        Burnout_Score: Computed burnout score
        utility_Score: Computed utility score
    Returns:
        User-friendly brunout status
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

def get_additional_interests():
    '''
    User input for users additional interests
    Returns:
        List of interests inputted by user
    '''
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

def display_recommendations(recommended_courses, highly_competitive_courses, round_num=1):
    print(f"\n=== Round {round_num} Recommendations ===")
    
    def display_course(course, is_competitive=False):
        print(f"\n{course['subject_code']}: {course['name']}")
        print(f"Match Score: {course['match_score']:.1%}")
        print(f"Enrollment Status: {course['enrollment_status']}")
        print(f"Current Availability: {course['seats'] - course['enrollments']} seats remaining")
        print(f"({course['enrollments']}/{course['seats']} enrolled)")
        
        if course['burnout_score'] is not None:
            print(f"Burnout Risk: {course['burnout_score']:.2f}")
        if course['utility_score'] is not None:
            print(f"Academic Utility: {course['utility_score']:.2f}")
        
        print("\nReasons for recommendation:")
        for reason in course['reasons']:
            print(f"• {reason}")
            
        if is_competitive:
            print("\n⚠️ Note: This is a highly competitive course.")
    
    print("\n🎯 Recommended Courses:")
    for i, course in enumerate(recommended_courses, 1):
        print(f"\n{i}.", end=" ")
        display_course(course)
    
    if highly_competitive_courses:
        print("\n⚠️ Highly Competitive Courses:")
        for i, course in enumerate(highly_competitive_courses, 1):
            print(f"\n{i}.", end=" ")
            display_course(course, is_competitive=True)

def recommend_schedule(nuid):
    '''
    Main function for recommending a schedule for a user
    Params:
        Nuid: Student id
    Returns:
        Reccomendation
    '''
    subjects_df, _, _, _, _ = load_subject_data()
    burnout_scores_df = load_burnout_scores(nuid)
    
    semester = int(input("Which semester are you in? "))
    
    # Keep track of recommended courses to avoid repetition
    recommended_history = set()
    
    # Initial recommendations
    round_num = 1
    recommended_courses, highly_competitive_courses = generate_recommendations(nuid, semester)
    
    if recommended_courses is None:
        print(f"Error: Could not generate recommendations for NUID: {nuid}")
        return None
    
    # Filter out previously recommended courses
    new_recommended = [course for course in recommended_courses 
                     if course['subject_code'] not in recommended_history][:5]
    new_competitive = [course for course in highly_competitive_courses 
                      if course['subject_code'] not in recommended_history][:5]
    
    # Add recommended courses to history
    for course in new_recommended + new_competitive:
        recommended_history.add(course['subject_code'])
    
    has_recommendations = display_recommendations(new_recommended, new_competitive, round_num)
    
    # Continue recommending until user is satisfied or no more courses
    while has_recommendations:
        choice = input("\nWould you like to see more recommendations? (yes/no): ").lower().strip()
        if choice != 'yes':
            break
            
        # Get additional interests
        print("\nLet's find more courses based on additional interests!")
        additional_interests = get_additional_interests()
        
        # Get new recommendations
        round_num += 1
        recommended_courses, highly_competitive_courses = generate_recommendations(
            nuid, semester, additional_interests
        )
        
        # Filter out previously recommended courses
        new_recommended = [course for course in recommended_courses 
                         if course['subject_code'] not in recommended_history][:5]
        new_competitive = [course for course in highly_competitive_courses 
                          if course['subject_code'] not in recommended_history][:5]
        
        # Add new recommendations to history
        for course in new_recommended + new_competitive:
            recommended_history.add(course['subject_code'])
        
        has_recommendations = display_recommendations(new_recommended, new_competitive, round_num)
        
        if not has_recommendations:
            print("\nNo more courses available matching your criteria.")
    
    # Save the final schedule
    schedule = save_schedule(nuid, recommended_history, subjects_df, burnout_scores_df)
    print(f"\nFinal schedule saved to schedule_{nuid}.csv")
    
    # Display final schedule summary
    print("\n=== Final Recommended Schedule ===")
    for subject_key, subject_value in schedule.items():
        print(f"{subject_key}: {subject_value}")
    
    return recommended_history

if __name__ == "__main__":
    nuid = input("Enter NUid to recommend schedule: ")
    recommend_schedule(nuid)