import tkinter as tk
from tkinter import messagebox

class DragDropManager:
    def __init__(self, app):
        self.app = app
        self.dragging = False
        self.dragged_item = None
        self.temp_window = None
        self.start_x = 0
        self.start_y = 0
        self.target_container = None
        self.potential_targets = []
        self.original_colors = {}
        
    def register_drop_target(self, target):
        """Register a frame as a potential drop target"""
        self.potential_targets.append(target)
        self.original_colors[target] = target.cget("background")
        print(f"Registered drop target: {target}")
        
    def start_drag(self, event, item):
        """Start dragging an item"""
        # Safety check - make sure the item has a course
        if not hasattr(item, 'course'):
            print(f"Warning: Item {item} has no course attribute")
            return
        
        self.dragging = True
        self.dragged_item = item
        self.dragged_widget = event.widget
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        # Create a temp window with the item's representation
        self.temp_window = tk.Toplevel(event.widget)
        self.temp_window.overrideredirect(True)  # No window decorations
        
        # Create a label with the course title
        course = item.course
        title_label = tk.Label(self.temp_window, 
                               text=course.title,
                               font=("Helvetica", 10),
                               bg="#E0E0E0", 
                               bd=1, 
                               relief=tk.RAISED,
                               padx=5, 
                               pady=2)
        title_label.pack()
        
        # Position the window at the cursor
        self.temp_window.geometry(f"+{event.x_root-10}+{event.y_root-10}")
        
        # Bind motion and button release events
        self.app.root.bind("<B1-Motion>", self.drag)
        self.app.root.bind("<ButtonRelease-1>", lambda e: self.end_drag())
        
        print(f"Start drag: {item.course.title}")
        
    def drag(self, event):
        """Update drag position and highlight potential drop targets"""
        if not self.dragging or not self.temp_window:
            return
        
        # Move the drag representation with cursor
        x = event.x_root
        y = event.y_root
        self.temp_window.geometry(f"+{x-10}+{y-10}")  # Offset slightly for better visibility
        
        # Reset highlight on all targets
        for target in self.potential_targets:
            if target in self.original_colors:
                target.configure(background=self.original_colors[target])
        
        # Find which target we're over
        old_target = self.target_container
        self.target_container = None
        
        for target in self.potential_targets:
            # Get screen coordinates of the target
            x1 = target.winfo_rootx()
            y1 = target.winfo_rooty()
            x2 = x1 + target.winfo_width()
            y2 = y1 + target.winfo_height()
            
            # Check if cursor is over target
            if x >= x1 and x <= x2 and y >= y1 and y <= y2:
                self.target_container = target
                
                # Check if course is compatible with this semester
                if self.dragged_item and hasattr(self.dragged_item, 'course'):
                    course = self.dragged_item.course
                    if hasattr(course, 'semester') and hasattr(target, 'title'):
                        compatible = is_compatible_semester(course.semester, target.title)
                        
                        # Highlight target accordingly - green if compatible, red if not
                        if compatible:
                            target.configure(background="#D5F5E3")  # Light green
                        else:
                            target.configure(background="#FADBD8")  # Light red
                            
                        print(f"Course {course.title} compatibility with {target.title}: {compatible}")
                    else:
                        # Default highlight if we can't determine compatibility
                        target.configure(background="#CCE5FF")  # Light blue
                else:
                    # Default highlight
                    target.configure(background="#CCE5FF")  # Light blue
                    
                break
        
        if old_target != self.target_container:
            print(f"Target changed: {self.target_container}")
            
        return "break"  # Prevent further event processing
        
    def end_drag(self):
        """End dragging and process the drop"""
        print(f"End drag, target: {self.target_container}")
        
        # Reset highlights
        for target in self.potential_targets:
            if target in self.original_colors:
                target.configure(background=self.original_colors[target])
                
        if not self.dragging:
            if self.temp_window:
                self.temp_window.destroy()
                self.temp_window = None
            return
        
        if self.dragged_item:
            course = self.dragged_item.course
            
            # If the course was already in a semester, we'll always remove it first
            if hasattr(course, 'assigned_semester') and course.assigned_semester:
                try:
                    current_semester = course.assigned_semester
                    current_semester.remove_course(course)
                    print(f"Removed {course.title} from {current_semester.title}")
                except Exception as e:
                    print(f"Error removing course: {e}")
            
            # If dropped onto a valid target, add it to the new semester
            if self.target_container:
                # Check if course is compatible with this semester
                is_compatible = True
                if hasattr(course, 'semester') and hasattr(self.target_container, 'title'):
                    is_compatible = is_compatible_semester(course.semester, self.target_container.title)
                
                # If compatible, proceed with drop
                if is_compatible:
                    # Add the course to the target semester
                    self.target_container.add_course(course)
                    print(f"Added {course.title} to {self.target_container.title}")
                else:
                    messagebox.showwarning("Incompatible Semester", 
                                       f"This course ({course.title}) is only offered in {course.semester} semesters.")
            else:
                # If not dropped on a valid target, the course remains removed (dragged away)
                print(f"Course {course.title} was dragged away and removed from its semester")
                    
        # Clean up
        if self.temp_window:
            self.temp_window.destroy()
            self.temp_window = None
            
        # Reset drag state
        self.dragging = False
        self.dragged_item = None
        self.target_container = None

# Add this helper function at the module level (outside any class)
def is_compatible_semester(course_semester, target_semester_title):
    """Check if a course can be placed in a given semester"""
    # If course has no semester restriction, it can go anywhere
    if not course_semester:
        return True
    
    # Extract semester type from target title (e.g., "SoSe 2025" -> "SoSe")
    target_semester_type = "SoSe" if "SoSe" in target_semester_title else "WiSe"
    
    # Check compatibility
    if "SoSe/WiSe" in course_semester or "WiSe/SoSe" in course_semester:
        # Course is offered in both semesters
        return True
    elif course_semester == "SoSe" and target_semester_type == "SoSe":
        # Summer course in summer semester
        return True
    elif course_semester == "WiSe" and target_semester_type == "WiSe":
        # Winter course in winter semester
        return True
    else:
        # Incompatible
        return False