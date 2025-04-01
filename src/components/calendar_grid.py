from tkinter import Frame, Canvas, Scrollbar, Label
from tkinter import N, S, E, W

class CalendarGrid(Frame):
    def __init__(self, master, semesters):
        super().__init__(master)
        self.semesters = semesters
        self.canvas = Canvas(self)
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.create_semesters()

    def create_semesters(self):
        for semester in self.semesters:
            semester_frame = Label(self.scrollable_frame, text=f"Semester {semester.id}", font=("Arial", 16))
            semester_frame.grid(row=semester.id, column=0, sticky=N+S+E+W)
            self.create_course_blocks(semester_frame, semester.courses)

    def create_course_blocks(self, semester_frame, courses):
        for course in courses:
            course_block = Label(semester_frame, text=course.title, width=20, height=course.lp, bg="lightblue", relief="raised")
            course_block.pack(pady=5)