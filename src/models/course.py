import os
import json
from tkinter import messagebox

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

    def load_state(self):
        """Load saved state if it exists"""
        if not os.path.exists(self.state_file):
            print(f"No saved state found for slot '{self.current_slot}'.")
            # Create empty state file for this slot
            self.save_state()
            return
            
        try:
            # Load state from file
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Set window size if specified
            if "window" in state:
                width = state["window"].get("width", 1600)
                height = state["window"].get("height", 900)
                self.root.geometry(f"{width}x{height}")
            
            # Create two lookup dictionaries - one by module code, one by title (as fallback)
            course_by_code = {course.module_code: course for course in self.courses if hasattr(course, 'module_code') and course.module_code}
            course_by_title = {course.title: course for course in self.courses if hasattr(course, 'title')}
            
            # Load favorite courses - IMPORTANT: Do this BEFORE creating the course list UI
            if "favorites" in state:
                favorites_count = 0
                for identifier in state["favorites"]:
                    # Try to find the course by module code first, then by title
                    if identifier in course_by_code:
                        course_by_code[identifier].favorite = True
                        favorites_count += 1
                    elif identifier in course_by_title:
                        course_by_title[identifier].favorite = True
                        favorites_count += 1
                    else:
                        print(f"Warning: Could not find course with identifier: {identifier}")
                
                print(f"Loaded {favorites_count} favorites")
            
            # Now that favorites are loaded, update course list display
            if hasattr(self, "course_list"):
                # Refresh course list to show favorites properly
                self.course_list.display_courses()
                
            # Set expanded groups state for course list
            if "expanded_groups" in state and hasattr(self, "course_list"):
                self.course_list.expanded_groups = state["expanded_groups"]
                self.course_list.display_courses()  # Refresh display with new expansion state
                    
            # Restore courses to semesters
            if "semester_assignments" in state:
                # Assign courses to semesters
                for semester_idx, course_identifiers in state["semester_assignments"].items():
                    semester_idx = int(semester_idx)
                    if semester_idx < len(self.semester_frames):
                        semester = self.semester_frames[semester_idx]
                        for identifier in course_identifiers:
                            # Try to find the course by module code first, then by title
                            course = None
                            if identifier in course_by_code:
                                course = course_by_code[identifier]
                            elif identifier in course_by_title:
                                course = course_by_title[identifier]
                                
                            if course:
                                semester.add_course(course)
                            else:
                                print(f"Warning: Could not find course: {identifier}")
            
            # Update window title to show current slot
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
            
            # Make sure all scrollable elements work correctly after loading
            self.refresh_scrolling()
                
            print(f"State loaded from {self.state_file}")
                
        except Exception as e:
            print(f"Error loading state: {e}")
            messagebox.showerror("Error", f"Failed to load state: {e}")

    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                "semester_assignments": {},
                "expanded_groups": self.course_list.expanded_groups,
                "favorites": [],  # Add an array to store favorite courses
                "window": {
                    "width": self.root.winfo_width(),
                    "height": self.root.winfo_height(),
                }
            }
            
            # Save course assignments to semesters
            for i, semester_frame in enumerate(self.semester_frames):
                # Each semester gets an array of course identifiers
                course_identifiers = []
                for course in semester_frame.courses:
                    identifier = None
                    # Use module code if available, otherwise use title
                    if hasattr(course, 'module_code') and course.module_code:
                        identifier = course.module_code
                    elif hasattr(course, 'title'):
                        identifier = course.title
                        
                    if identifier:
                        course_identifiers.append(identifier)
                        
                state["semester_assignments"][str(i)] = course_identifiers
            
            # Save favorite courses
            for course in self.courses:
                if hasattr(course, 'favorite') and course.favorite:
                    identifier = None
                    # Use module code if available, otherwise use title
                    if hasattr(course, 'module_code') and course.module_code:
                        identifier = course.module_code
                    elif hasattr(course, 'title'):
                        identifier = course.title
                        
                    if identifier:
                        state["favorites"].append(identifier)
            
            # Write to file
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            print(f"State saved to {self.state_file}")
            
            # Update window title to show current slot
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
                
        except Exception as e:
            print(f"Error saving state: {e}")
            messagebox.showerror("Error", f"Failed to save state: {e}")

    def refresh_scrolling(self):
        """Refresh all scrolling mechanisms after loading state"""
        # First, update scroll regions for all semester frames
        for semester in self.semester_frames:
            # Force update of scroll regions
            semester.course_container.update_idletasks()
            semester._configure_scroll_region()
            
            # Re-bind mousewheel events to all courses
            for course in semester.courses:
                if course in semester.course_blocks:
                    block = semester.course_blocks[course]
                    
                    # Define scroll function
                    def _on_mousewheel(event, sem=semester):
                        if hasattr(event, 'delta'):
                            sem.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                        elif hasattr(event, 'num'):
                            if event.num == 4:
                                sem.canvas.yview_scroll(-1, "units")
                            elif event.num == 5:
                                sem.canvas.yview_scroll(1, "units")
                        return "break"
                    
                    # Bind mousewheel events to the block and its children
                    block.bind("<MouseWheel>", _on_mousewheel)
                    block.bind("<Button-4>", _on_mousewheel)
                    block.bind("<Button-5>", _on_mousewheel)
                    
                    for child in block.winfo_children():
                        child.bind("<MouseWheel>", _on_mousewheel)
                        child.bind("<Button-4>", _on_mousewheel)
                        child.bind("<Button-5>", _on_mousewheel)

    def on_slot_selected(self, event):
        """Handle selection of a different save slot"""
        selected_slot = self.slot_var.get()
        
        if selected_slot != self.current_slot:
            # Ask for confirmation if there are unsaved changes
            if messagebox.askyesno("Switch Save Slot", 
                                "Are you sure you want to switch to another save slot?\n"
                                "Any unsaved changes will be lost."):
                # Save current state to new slot
                self.current_slot = selected_slot
                self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
                
                # Clear current semester layouts
                self.clear_semesters()
                
                # Load the new state
                self.load_state()
                
                # Ensure scrolling works after loading
                self.refresh_scrolling()
            else:
                # Revert combobox to previous value
                self.slot_var.set(self.current_slot)