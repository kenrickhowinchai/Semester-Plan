import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from components.course_block import CourseBlock

class SemesterFrame(tk.Frame):
    def __init__(self, parent, title, max_credits=30, drag_drop_manager=None):
        super().__init__(parent, padx=10, pady=10, relief=tk.RAISED, borderwidth=2)
        self.title = title
        self.max_credits = max_credits
        self.courses = []
        self.total_credits = 0
        self.drag_drop_manager = drag_drop_manager
        self.course_blocks = {}  # Keep track of course blocks
        
        # Register as a drop target
        if self.drag_drop_manager:
            self.drag_drop_manager.register_drop_target(self)
        
        # Create title label
        title_label = tk.Label(self, text=title, font=("Helvetica", 12, "bold"))
        title_label.pack(fill=tk.X, pady=(0, 5))
        
        # Create credits display
        self.credits_label = tk.Label(self, text=f"Credits: 0/{max_credits} LP")
        self.credits_label.pack(fill=tk.X, pady=(0, 5))
        
        # Create scrollable container for courses - make it much taller
        self.canvas = tk.Canvas(self, width=220, height=700)  # Keep width reasonable but increase height significantly
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame inside the canvas to hold the courses
        self.course_container = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.course_container, anchor='nw', width=210)
        
        # Update scrollregion when the size of the frame changes
        self.course_container.bind("<Configure>", 
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Bind mousewheel events
        self.bind_mousewheel_to_canvas()

    def bind_mousewheel_to_canvas(self):
        """Bind mousewheel events to scroll the canvas"""
        # Bind to the canvas itself
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        
        # Bind to the frame containing the canvas
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)
        
        # Bind to the course container
        self.course_container.bind("<MouseWheel>", self._on_mousewheel)
        self.course_container.bind("<Button-4>", self._on_mousewheel)
        self.course_container.bind("<Button-5>", self._on_mousewheel)
        
        # We'll also need to bind mousewheel events to any course blocks as they're added
        # This will be done in the add_course method

    def _on_mousewheel(self, event):
        """Handle mousewheel events for scrolling"""
        # Different OSes send different events
        delta = 0
        if hasattr(event, 'num') and event.num == 5 or event.delta < 0:  # Scroll down
            delta = 1
        elif hasattr(event, 'num') and event.num == 4 or event.delta > 0:  # Scroll up
            delta = -1
        
        self.canvas.yview_scroll(delta, "units")
        return "break"  # Prevent propagation to parent widget

    def on_drop(self, event):
        """Handle drop events from the drag manager"""
        # The drag manager already knows where the drop occurred
        # so we don't need to do anything here
        pass
    
    def add_course(self, course):
        """Add a course to this semester"""
        # Check semester compatibility
        if hasattr(course, 'semester') and course.semester:
            from components.drag_drop_manager import is_compatible_semester
            if not is_compatible_semester(course.semester, self.title):
                messagebox.showwarning("Incompatible Semester", 
                                   f"This course ({course.title}) is only offered in {course.semester} semesters.")
                return False
        
        # If the course is already in a semester, remove it
        if hasattr(course, 'assigned_semester') and course.assigned_semester is not None:
            try:
                print(f"Removing course {course.title} from previous semester")
                course.assigned_semester.remove_course(course)
            except Exception as e:
                print(f"Error removing course: {e}")
        
        # Add the course to this semester
        self.courses.append(course)
        course.assigned_semester = self
        
        # Create a visual block for the course
        course_block = CourseBlock(self.course_container, course, self.drag_drop_manager)
        course_block.pack(fill=tk.X, pady=3, padx=2)
        
        # Store a reference to the block for removal
        self.course_blocks[course] = course_block
        
        # Bind mousewheel events to this course block
        course_block.bind("<MouseWheel>", self._on_mousewheel)
        course_block.bind("<Button-4>", self._on_mousewheel)
        course_block.bind("<Button-5>", self._on_mousewheel)
        
        # Bind to all child widgets of the course block too
        for child in course_block.winfo_children():
            child.bind("<MouseWheel>", self._on_mousewheel)
            child.bind("<Button-4>", self._on_mousewheel)
            child.bind("<Button-5>", self._on_mousewheel)
        
        # Update the total credits display
        self.update_total_credits()
        
        # Update graduation requirements
        self.drag_drop_manager.app.update_graduation_requirements()
        
        return True

    def remove_course(self, course):
        """Remove a course from this semester"""
        if course in self.courses:
            print(f"Removing course {course.title} from {self.title}")
            self.courses.remove(course)
            
            # Destroy the visual representation if it exists
            if course in self.course_blocks:
                self.course_blocks[course].destroy()
                del self.course_blocks[course]
            
            # Reset the course's assigned_semester
            course.assigned_semester = None
            
            # Update the total credits display
            self.update_total_credits()
            
            # Update graduation requirements
            self.drag_drop_manager.app.update_graduation_requirements()
        else:
            print(f"Course {course.title} not found in {self.title}")

    def update_total_credits(self):
        """Update the total credits display"""
        self.total_credits = sum(course.credits for course in self.courses)
        self.credits_label.config(text=f"Credits: {self.total_credits}/{self.max_credits} LP")
        
        # Change color if over credit limit
        if self.total_credits > self.max_credits:
            self.credits_label.config(foreground="red")
        else:
            self.credits_label.config(foreground="black")
    
    def update_credits_display(self):
        if self.total_credits > self.max_credits:
            # Over the limit - red with warning icon
            color = 'red'
            self.credits_label.config(text=f"⚠️ {self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10, "bold"))
            self.credits_label.config(bg='#ffe0e0')  # Light red background
        elif self.total_credits == self.max_credits:
            # Exactly at limit - green
            color = 'green'
            self.credits_label.config(text=f"✓ {self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10))
            self.credits_label.config(bg='#e0ffe0')  # Light green background
        else:
            # Under limit - black
            color = '#333'
            self.credits_label.config(text=f"{self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10))
            self.credits_label.config(bg='#d0e0ff')  # Default background