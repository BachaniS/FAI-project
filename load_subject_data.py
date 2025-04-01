import pandas as pd

def load_subject_data():
    """Load and process subject data from CSV file."""
    try:
        df = pd.read_csv('subject_analysis.csv')
        
        # Basic validation
        required_columns = [
            'Subject', 'Subject Names', 'Weekly Workload (hours)', 
            'Assignments #', 'Hours per Assignment', 'Assignment Weight',
            'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade',
            'Exam #', 'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade',
            'Course Outcomes', 'Prerequisite', 'Corequisite'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean and process subjects data
        subjects_df = df[['Subject', 'Subject Names', 'Weekly Workload (hours)', 
                         'Assignments #', 'Hours per Assignment', 'Assignment Weight',
                         'Avg Assignment Grade', 'Project Weight', 'Avg Project Grade',
                         'Exam #', 'Avg Exam Grade', 'Exam Weight', 'Avg Final Grade']]
        
        subjects_df = subjects_df.rename(columns={
            'Subject': 'subject_code',
            'Subject Names': 'name',
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
            'Avg Final Grade': 'avg_final_grade'
        })
        
        # Process outcomes
        outcomes = []
        for _, row in df.iterrows():
            if pd.notna(row['Course Outcomes']) and isinstance(row['Course Outcomes'], str):
                for outcome in row['Course Outcomes'].split(','):
                    outcomes.append({
                        'subject_code': row['Subject'],
                        'outcome': outcome.strip()
                    })
        outcomes_df = pd.DataFrame(outcomes)
        
        # Process prerequisites
        prereqs = df[df['Prerequisite'].notna() & (df['Prerequisite'] != 'None')]
        prereqs = prereqs[['Subject', 'Prerequisite']].rename(columns={
            'Subject': 'subject_code',
            'Prerequisite': 'prereq_subject_code'
        })
        
        # Process corequisites
        coreqs = df[df['Corequisite'].notna() & (df['Corequisite'] != 'None')]
        coreqs = coreqs[['Subject', 'Corequisite']].rename(columns={
            'Subject': 'subject_code',
            'Corequisite': 'coreq_subject_code'
        })
        
        return subjects_df, outcomes_df, prereqs, coreqs
    
    except FileNotFoundError:
        raise FileNotFoundError("subject_analysis.csv not found. Please ensure the file exists in the current directory.")
    except Exception as e:
        raise Exception(f"Error loading subject data: {str(e)}")

if __name__ == "__main__":
    try:
        subjects_df, outcomes_df, prereqs, coreqs = load_subject_data()
        print("Subject data loaded successfully!")
        
        # Save processed data for verification
        subjects_df.to_csv('processed_subjects.csv', index=False)
        outcomes_df.to_csv('processed_outcomes.csv', index=False)
        prereqs.to_csv('processed_prereqs.csv', index=False)
        coreqs.to_csv('processed_coreqs.csv', index=False)
        
        print("Processed data saved to CSV files for verification.")
    except Exception as e:
        print(f"Error: {str(e)}")