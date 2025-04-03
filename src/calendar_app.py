import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import shutil

from components.semester_frame import SemesterFrame
from components.course_list import CourseList
from components.drag_drop_manager import DragDropManager
from models.course import Course
from components.graduation_requirements import GraduationRequirementsFrame

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Semester Calendar Planner")
        self.root.geometry("1600x900")
        
        # Create resources directory if it doesn't exist
        self.resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
        self.save_dir = os.path.join(self.resources_dir, 'saves')
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Initialize slot system
        self.current_slot = "Default"
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Get available save slots - do this BEFORE creating widgets
        self.available_slots = self.get_available_slots()
        
        # Initialize drag-drop manager
        self.drag_drop_manager = DragDropManager(self)
        
        # Initialize courses
        self.courses = []
        self.semester_frames = []  # Keep track of all semester frames
        self.load_courses()
        
        # Create UI with save slots
        self.create_widgets()
        
        # Load saved state if it exists
        self.load_state()
        
        # Bind save state to window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        """Create the UI elements"""
        # Create a menu bar
        menu_bar = tk.Menu(self.root)
        # Add menus to the menu bar
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_state)
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)
        
        # Add status/save bar at the TOP instead of the bottom
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.TOP, pady=(5, 10))  # TOP instead of BOTTOM
        
        # Create a left section for save slots
        left_section = ttk.Frame(status_frame)
        left_section.pack(side=tk.LEFT, fill=tk.X)
        
        # Add save slot selector to status bar
        ttk.Label(left_section, text="Save Slot:").pack(side=tk.LEFT, padx=5)
        self.slot_var = tk.StringVar(value=self.current_slot)
        self.slot_combo = ttk.Combobox(
            left_section, 
            textvariable=self.slot_var,
            values=self.available_slots,
            width=15
        )
        self.slot_combo.pack(side=tk.LEFT, padx=5)
        self.slot_combo.bind("<<ComboboxSelected>>", self.on_slot_selected)
        
        # Add slot management buttons
        slot_buttons_frame = ttk.Frame(left_section)
        slot_buttons_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create buttons with appropriate icons or text
        ttk.Button(slot_buttons_frame, text="New", width=6, 
                   command=self.create_new_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Rename", width=6, 
                   command=self.rename_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Copy", width=6, 
                   command=self.duplicate_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Delete", width=6, 
                   command=self.delete_slot).pack(side=tk.LEFT, padx=2)
        
        # Add save button on the right
        ttk.Button(status_frame, text="Save", command=self.save_state).pack(side=tk.RIGHT, padx=5)
        
        # Create main container as a PanedWindow for resizable sections
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left panel for course list
        left_panel = ttk.Frame(main_container)
        
        # Create course list
        self.course_list = CourseList(left_panel, self.courses, self.drag_drop_manager)
        self.course_list.pack(fill=tk.BOTH, expand=True)
        
        # Create right panel for semesters and requirements as a vertical PanedWindow
        # This allows the user to resize the graduation requirements section
        right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        
        # Add semester panel to right panel
        semester_panel = ttk.Frame(right_panel)
        
        # Create horizontal scrollable frame for semesters
        semester_scroll_frame = ttk.Frame(semester_panel)
        semester_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for horizontal scrolling of semesters
        self.semester_canvas = tk.Canvas(semester_scroll_frame)
        h_scrollbar = ttk.Scrollbar(semester_scroll_frame, orient="horizontal", command=self.semester_canvas.xview)
        
        # Configure the canvas
        self.semester_canvas.configure(xscrollcommand=h_scrollbar.set)
        self.semester_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create frame to hold semester frames
        self.semesters_frame = ttk.Frame(self.semester_canvas)
        self.canvas_window = self.semester_canvas.create_window(
            (0, 0), 
            window=self.semesters_frame,
            anchor="nw",
            tags="semester_frames"
        )
        
        # Update scroll region when the size changes
        self.semesters_frame.bind("<Configure>", 
                             lambda e: self.semester_canvas.configure(scrollregion=self.semester_canvas.bbox("all")))
        self.semester_canvas.bind("<Configure>", 
                              lambda e: self.semester_canvas.itemconfig(self.canvas_window, height=e.height))
        
        # Bind mousewheel to horizontal scroll
        self.semester_canvas.bind("<MouseWheel>", self._on_horizontal_mousewheel)
        self.semesters_frame.bind("<MouseWheel>", self._on_horizontal_mousewheel)
        
        # Create semester frames
        self.create_semesters()
        
        # Add requirements panel as a resizable section
        self.requirements_panel = ttk.LabelFrame(right_panel, text="Graduation Requirements")
        
        # Create graduation requirements display
        self.graduation_requirements = GraduationRequirementsFrame(self.requirements_panel, self)
        self.graduation_requirements.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add both panels to the vertical PanedWindow
        right_panel.add(semester_panel, weight=3)  # 75% initial height for semesters
        right_panel.add(self.requirements_panel, weight=1)  # 25% initial height for requirements
        
        # Add both main panels to the horizontal PanedWindow
        main_container.add(left_panel, weight=1)
        main_container.add(right_panel, weight=3)
        
        # Set initial sash positions after a short delay to ensure widgets are fully created
        self.root.update_idletasks()
        self.root.after(100, lambda: main_container.sashpos(0, 280))  # Position horizontal sash
    
    def _on_horizontal_mousewheel(self, event):
        """Handle mousewheel events for horizontal scrolling"""
        delta = 0
        if hasattr(event, 'num') and event.num == 5 or event.delta < 0:  # Scroll down/right
            delta = 1
        elif hasattr(event, 'num') and event.num == 4 or event.delta > 0:  # Scroll up/left
            delta = -1
            
        self.semester_canvas.xview_scroll(delta, "units")
        return "break"  # Prevent propagation to parent widget
    
    def get_available_slots(self):
        """Get a list of available save slots"""
        slots = ["Default"]  # Always include Default
        
        try:
            # Get all JSON files in the saves directory
            if os.path.exists(self.save_dir):
                for filename in os.listdir(self.save_dir):
                    if filename.endswith(".json"):
                        slot_name = filename[:-5]  # Remove .json extension
                        if slot_name != "Default":  # Already included
                            slots.append(slot_name)
        except Exception as e:
            print(f"Error getting save slots: {e}")
            
        return sorted(slots)
    
    def update_slot_selector(self):
        """Update the save slot dropdown with current available slots"""
        self.available_slots = self.get_available_slots()
        self.slot_selector['values'] = self.available_slots
    
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
            else:
                # Revert combobox to previous value
                self.slot_var.set(self.current_slot)
    
    def create_new_slot(self):
        """Create a new save slot"""
        slot_name = simpledialog.askstring("New Save Slot", 
                                         "Enter a name for the new save slot:",
                                         parent=self.root)
        
        if not slot_name:  # User canceled
            return
            
        # Clean the name (remove special characters, spaces)
        slot_name = "".join(c for c in slot_name if c.isalnum() or c in [' ', '_', '-'])
        
        # Check if name already exists
        if slot_name in self.available_slots:
            messagebox.showerror("Error", f"Save slot '{slot_name}' already exists!")
            return
            
        # Create a new slot file
        self.current_slot = slot_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Clear current semesters
        self.clear_semesters()
        
        # Save current state to new slot
        self.save_state()
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Created new save slot: {slot_name}")
    
    def rename_slot(self):
        """Rename the current save slot"""
        if self.current_slot == "Default":
            messagebox.showerror("Error", "Cannot rename the Default save slot!")
            return
            
        new_name = simpledialog.askstring("Rename Save Slot", 
                                        "Enter a new name for this save slot:",
                                        parent=self.root,
                                        initialvalue=self.current_slot)
        
        if not new_name:  # User canceled
            return
            
        # Clean the name
        new_name = "".join(c for c in new_name if c.isalnum() or c in [' ', '_', '-'])
        
        # Check if name already exists and isn't the current name
        if new_name in self.available_slots and new_name != self.current_slot:
            messagebox.showerror("Error", f"Save slot '{new_name}' already exists!")
            return
            
        old_file = self.state_file
        self.current_slot = new_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # If the old file exists, rename it
        if os.path.exists(old_file):
            try:
                os.rename(old_file, self.state_file)
            except Exception as e:
                print(f"Error renaming save file: {e}")
                # If rename fails, save to the new location
                self.save_state()
        else:
            # Save to the new location
            self.save_state()
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Renamed save slot to: {new_name}")
    
    def delete_slot(self):
        """Delete the current save slot"""
        if self.current_slot == "Default":
            messagebox.showerror("Error", "Cannot delete the Default save slot!")
            return
            
        if messagebox.askyesno("Delete Save Slot", 
                             f"Are you sure you want to delete the save slot '{self.current_slot}'?\n"
                             "This action cannot be undone."):
            
            # Delete the file
            try:
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
            except Exception as e:
                print(f"Error deleting save file: {e}")
            
            # Switch to Default slot
            self.current_slot = "Default"
            self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
            
            # Clear current semesters
            self.clear_semesters()
            
            # Load the default state
            self.load_state()
            
            # Update UI
            self.update_slot_selector()
            self.slot_var.set(self.current_slot)
            
            messagebox.showinfo("Success", "Save slot deleted successfully")
    
    def duplicate_slot(self):
        """Duplicate the current save slot"""
        # Get base name for copy
        base_name = f"{self.current_slot}_copy"
        
        # Find a unique name
        counter = 1
        new_name = base_name
        while new_name in self.available_slots:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        # Save current state
        self.save_state()
        
        # Create copy with new name
        old_file = self.state_file
        
        if os.path.exists(old_file):
            new_file = os.path.join(self.save_dir, f"{new_name}.json")
            try:
                shutil.copy2(old_file, new_file)
            except Exception as e:
                print(f"Error duplicating save file: {e}")
                return
        
        # Switch to the new slot
        self.current_slot = new_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Duplicated save slot: {new_name}")
    
    def clear_semesters(self):
        """Clear all courses from semesters"""
        for semester_frame in self.semester_frames:
            # Create a copy of the list to avoid modification during iteration
            courses_copy = semester_frame.courses.copy()
            for course in courses_copy:
                semester_frame.remove_course(course)
    
    def on_close(self):
        """Handler for window close event"""
        self.save_state()
        self.root.destroy()
    
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
                # Each semester gets an array of course codes
                course_codes = []
                for course in semester_frame.courses:
                    if hasattr(course, 'module_code') and course.module_code:
                        course_codes.append(course.module_code)
                        
                state["semester_assignments"][str(i)] = course_codes
            
            # Save favorite courses
            for course in self.courses:
                if hasattr(course, 'favorite') and course.favorite and hasattr(course, 'module_code'):
                    state["favorites"].append(course.module_code)
            
            # Write to file
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            print(f"State saved to {self.state_file}")
            
            # Update window title to show current slot
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
                
        except Exception as e:
            print(f"Error saving state: {e}")
            messagebox.showerror("Error", f"Failed to save state: {e}")
    
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
            
            # Create a lookup dictionary for faster course retrieval by code
            course_by_code = {course.module_code: course for course in self.courses if hasattr(course, 'module_code')}
                
            # Load favorite courses - IMPORTANT: Do this BEFORE creating the course list UI
            if "favorites" in state:
                favorites_count = 0
                for module_code in state["favorites"]:
                    if module_code in course_by_code:
                        course_by_code[module_code].favorite = True
                        favorites_count += 1
                
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
                for semester_idx, course_codes in state["semester_assignments"].items():
                    semester_idx = int(semester_idx)
                    if semester_idx < len(self.semester_frames):
                        semester = self.semester_frames[semester_idx]
                        for code in course_codes:
                            if code in course_by_code:
                                course = course_by_code[code]
                                semester.add_course(course)
            
            # Update window title to show current slot
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
                
            print(f"State loaded from {self.state_file}")
                
        except Exception as e:
            print(f"Error loading state: {e}")
            messagebox.showerror("Error", f"Failed to load state: {e}")
    
    def create_semesters(self):
        """Create the semester frames in a 1x6 horizontal layout"""
        # Clear any existing frames
        self.semester_frames = []
        
        # Set up a row with 6 columns
        for j in range(6):  # 6 columns for 6 semesters
            self.semesters_frame.grid_columnconfigure(j, weight=1, minsize=250)  # Minimum width of 250 pixels
            
            # Generate semester name based on index
            if j % 2 == 0:  # Even indexes (0, 2, 4) are now Summer semesters
                semester_type = "SoSe"
                year = 2025 + (j // 2)
                semester_title = f"{semester_type} {year}"
            else:  # Odd indexes (1, 3, 5) are now Winter semesters
                semester_type = "WiSe"
                year = 2025 + (j // 2)
                semester_title = f"{semester_type} {year}/{year+1}"
            
            semester_frame = SemesterFrame(self.semesters_frame, semester_title, 30, self.drag_drop_manager)
            semester_frame.grid(row=0, column=j, sticky="nsew", padx=5, pady=5)  # All in row 0
            
            # Store reference to semester frame
            self.semester_frames.append(semester_frame)
    
    def load_courses(self):
        """Load courses from the JSON file"""
        try:
            # Get the absolute path to the resources directory
            courses_file = os.path.join(self.resources_dir, 'courses.json')
            
            with open(courses_file, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
                
            for course_data in courses_data:
                # Check if the course has a title - if not, it's a placeholder entry
                if 'title' in course_data:
                    # Create a Course object from the data
                    course = Course(
                        title=course_data.get('title', 'Unnamed Course'),
                        credits=course_data.get('credits', 0),
                        exam_type=course_data.get('exam_type', ''),
                        group=course_data.get('group', ''),
                        module_code=course_data.get('module_code', ''),
                        grading=course_data.get('grading', ''),
                        semester=course_data.get('semester', '')
                    )
                    self.courses.append(course)
                    
        except Exception as e:
            print(f"Error loading courses: {e}")
    
    def update_graduation_requirements(self):
        """Update the graduation requirements display"""
        if hasattr(self, 'graduation_requirements'):
            self.graduation_requirements.update_requirements()
