import csv
import json

def convert_csv_to_json(input_file, output_file):
    """
    Convert a CSV file to a structured JSON format with specific transformations.
    
    :param input_file: Path to the input CSV file
    :param output_file: Path to the output JSON file
    """
    # List of fields that should be converted to arrays
    array_fields = [
        'Course Outcomes', 
        'Programming Knowledge Needed', 
        'Math Requirements', 
        'Other Requirements', 
        'Prerequisite', 
        'Corequisite'
    ]

    # Read the CSV file
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        # Use DictReader to read the CSV as dictionaries
        csvreader = csv.DictReader(csvfile)
        
        # Process each row
        processed_data = []
        for row in csvreader:
            # Create a new dictionary to store processed row
            processed_row = {
                "subject_id": row['Subject'],
                "subject_name": row['Subject Names'],
                "seats": int(row['Seats']),
                "enrollments": int(row['Enrollments']),
                "weekly_course_time": int(row['Weekly Workload (hours)']),
                "assignment_count": int(row['Assignments #']),
                "assignment_time": int(row['Hours per Assignment']),
                "assignment_weight": float(row['Assignment Weight']),
                "assignment_grade": float(row['Avg Assignment Grade']),
                "project_weight": float(row['Project Weight']),
                "project_grade": float(row['Avg Project Grade']),
                "exam_count": int(row['Exam #']),
                "exam_grade": float(row['Avg Exam Grade']),
                "exam_weight": float(row['Exam Weight']),
                "final_grade": float(row['Avg Final Grade']),
            }
            
            # Process array fields
            for field in array_fields:
                # Convert to lowercase and replace spaces with underscores for consistent processing
                key = field.lower().replace(' ', '_')
                
                # If the value is 'None' or empty, set to an empty list
                if not row[field] or row[field].lower() == 'none':
                    processed_row[key] = []
                else:
                    # Split by comma and strip whitespace
                    processed_row[key] = [item.strip() for item in row[field].split(',')]
            
            processed_data.append(processed_row)
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(processed_data, jsonfile, indent=2)
    
    print(f"Conversion complete. Output saved to {output_file}")

# Example usage
if __name__ == "__main__":
    convert_csv_to_json('data/courses/subject_analysis.csv', 'testing/output.json')

# Usage instructions
