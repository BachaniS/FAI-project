from ga_recommender import recommend_schedule

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

def get_burnout_status(burnout_score, utility_score):
    """Get burnout status message based on burnout and utility scores"""
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

def display_recommendations(recommended_courses, highly_competitive_courses):
    """Display the recommended courses to the user"""
    # Display recommendations
    print("\n🎯 Recommended Courses:")
    if recommended_courses:
        for i, course in enumerate(recommended_courses, 1):
            seats = course['seats']
            enrollments = course['enrollments']
            
            print(f"\n{i}. {course['subject_code']}: {course['name']}")
            print(f"   Match Score: {course['match_score']:.1%}")
            
            # Burnout information if available
            if course['burnout_score'] is not None and course['utility_score'] is not None:
                burnout_status = get_burnout_status(course['burnout_score'], course['utility_score'])
                print(f"   Burnout Risk: {course['burnout_score']:.2f}")
                print(f"   Academic Utility: {course['utility_score']:.2f}")
                print(f"   {burnout_status}")
            
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
        print("No courses found matching your criteria.")
    
    # Display highly competitive courses
    if highly_competitive_courses:
        print("\n⚠️ Highly Competitive Courses:")
        for i, course in enumerate(highly_competitive_courses, 1):
            seats = course['seats']
            enrollments = course['enrollments']
            
            print(f"\n{i}. {course['subject_code']}: {course['name']}")
            print(f"   Match Score: {course['match_score']:.1%}")
            
            # Burnout information if available
            if course['burnout_score'] is not None and course['utility_score'] is not None:
                burnout_status = get_burnout_status(course['burnout_score'], course['utility_score'])
                print(f"   Burnout Risk: {course['burnout_score']:.2f}")
                print(f"   Academic Utility: {course['utility_score']:.2f}")
                print(f"   {burnout_status}")
            
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

def display_final_schedule(schedule):
    """Display the final recommended schedule"""
    print("\n=== Final Recommended Schedule ===")
    for subject_key, subject_value in schedule.items():
        print(f"{subject_key}: {subject_value}")

if __name__ == "__main__":
    nuid = input("Enter NUid to recommend schedule: ")
    
    # Get recommendations from the GA recommender
    recommended_courses, competitive_courses, final_schedule = recommend_schedule(nuid)
    
    # Display the recommendations
    if recommended_courses is not None:
        display_recommendations(recommended_courses, competitive_courses)
        
        # Display the final schedule
        if final_schedule:
            display_final_schedule(final_schedule)
        
        print(f"\nFinal schedule saved to schedule_{nuid}.csv")
    else:
        print(f"Error: Could not generate recommendations for NUID: {nuid}")