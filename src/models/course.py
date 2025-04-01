class Course:
    def __init__(self, title, credits, description="", module_code="", group="", semester=None, exam_type=None, grading=None):
        self.title = title
        self.credits = credits
        self.description = description
        self.module_code = module_code
        self.group = group
        self.semester = semester  # When it's offered (SoSe, WiSe, or both)
        self.assigned_semester = None  # Which semester frame it's assigned to
        self.exam_type = exam_type
        self.grading = grading
        self.favorite = False  # Initialize favorite status

    def __str__(self):
        return f"{self.title} ({self.credits} LP)"