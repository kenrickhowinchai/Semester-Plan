class Semester:
    def __init__(self):
        self.courses = []
        self.total_lp = 0
        self.max_lp = 30  # Maximum LP per semester

    def add_course(self, course):
        if self.total_lp + course.lp <= self.max_lp:
            self.courses.append(course)
            self.total_lp += course.lp
            return True
        return False

    def remove_course(self, course):
        if course in self.courses:
            self.courses.remove(course)
            self.total_lp -= course.lp
            return True
        return False

    def get_courses(self):
        return self.courses

    def get_total_lp(self):
        return self.total_lp

    def is_full(self):
        return self.total_lp >= self.max_lp

    def clear_courses(self):
        self.courses.clear()
        self.total_lp = 0