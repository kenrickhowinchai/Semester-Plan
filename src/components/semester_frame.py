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
        
        # Create scrollable container for courses
        # Make the canvas match the expected semester height better
        frame_height = 500  # Reduced height to fit typical screen
        self.canvas = tk.Canvas(self, width=220, height=frame_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame inside the canvas to hold the courses
        self.course_container = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.course_container, 
            anchor='nw', 
            width=200,  # Slightly smaller to avoid horizontal scrollbar
            tags="course_container"
        )
        
        # Update scrollregion when the size of the frame changes
        self.course_container.bind("<Configure>", self.update_scroll_region)
        
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
        """Handle mousewheel events"""
        # Get the scroll direction based on event type
        if hasattr(event, 'delta'):
            # Windows style mouse wheel event
            # When scrolling down, delta is negative
            # When we scroll down, we want content to move UP (positive scroll)
            delta = -1 if event.delta < 0 else 1  # -1 for scroll down, 1 for scroll up
        else:
            # Unix style mouse wheel event (Button-4 is scroll up, Button-5 is scroll down)
            delta = -1 if event.num == 5 else 1  # -1 for scroll down, 1 for scroll up
        
        # For moving content UP when scrolling DOWN (and vice versa), we negate the delta
        # This gives the natural scrolling feel where content moves opposite to the scroll direction
        self.canvas.yview_scroll(-delta, "units")
        
        return "break"  # Prevent the event from propagating

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
        
        # Force update of the scroll region to include the new course
        self.course_container.update_idletasks()
        self.update_scroll_region()
        
        # Use after_idle to make sure the scroll happens after everything is updated
        self.after_idle(self.scroll_to_bottom)
        
        # Update the course list to gray out this course
        if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app') and hasattr(self.drag_drop_manager.app, 'course_list'):
            self.drag_drop_manager.app.course_list.display_courses()
        
        # Update graduation requirements
        if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
            self.drag_drop_manager.app.update_graduation_requirements()
        
        return True  # Successfully added

    def remove_course(self, course):
        """Remove a course from this semester"""
        if course in self.courses:
            self.courses.remove(course)
            course.assigned_semester = None
            
            # Remove the corresponding visual block
            if course in self.course_blocks:
                self.course_blocks[course].destroy()
                del self.course_blocks[course]
                
            # Update the total credits display
            self.update_total_credits()
            
            # Update the course list to un-gray this course
            if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app') and hasattr(self.drag_drop_manager.app, 'course_list'):
                self.drag_drop_manager.app.course_list.display_courses()
            
            # Update graduation requirements
            if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
                self.drag_drop_manager.app.update_graduation_requirements()
                
            return True
        return False

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

    def update_scroll_region(self, event=None):
        """Update the scroll region to encompass all content"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def scroll_to_bottom(self):
        """Scroll to the bottom of the course container"""
        # Calculate the total height of all course blocks
        total_height = sum(block.winfo_height() for block in self.course_blocks.values())
        
        # If the total height is greater than the visible area, scroll to bottom
        if total_height > self.canvas.winfo_height():
            # This should scroll to the bottom - using fraction instead of units
            self.canvas.yview_moveto(1.0)
            print(f"Scrolled to bottom - total height: {total_height}px, visible: {self.canvas.winfo_height()}px")