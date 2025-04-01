def load_courses_from_json(file_path):
    import json
    try:
        with open(file_path, 'r') as file:
            courses = json.load(file)
        return courses
    except Exception as e:
        print(f"Error loading courses: {e}")
        return []

def validate_course_data(course):
    required_fields = ['title', 'LP', 'exam_format', 'group']
    for field in required_fields:
        if field not in course:
            print(f"Missing field: {field} in course data.")
            return False
    return True

def calculate_total_lp(courses):
    return sum(course['LP'] for course in courses if validate_course_data(course))