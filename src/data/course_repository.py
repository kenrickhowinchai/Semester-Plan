from typing import List
import json
import os

class CourseRepository:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.courses = []

    def load_courses(self) -> List[dict]:
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as file:
                self.courses = json.load(file)
        return self.courses

    def save_courses(self) -> None:
        with open(self.filepath, 'w') as file:
            json.dump(self.courses, file, indent=4)

    def add_course(self, course: dict) -> None:
        self.courses.append(course)
        self.save_courses()

    def remove_course(self, course_title: str) -> None:
        self.courses = [course for course in self.courses if course['title'] != course_title]
        self.save_courses()

    def get_courses(self) -> List[dict]:
        return self.courses