import tkinter as tk
from tkinter import ttk

from components.course_block import CourseBlock

class CourseList(ttk.Frame):
    def __init__(self, parent, courses, drag_drop_manager):
        super().__init__(parent)
        
        self.courses = courses
        self.drag_drop_manager = drag_drop_manager
        self.filtered_courses = courses
        self._expanded_groups = {}  # Track which groups are expanded
        
        # Create UI elements
        self.create_widgets()
        
    @property
    def expanded_groups(self):
        return self._expanded_groups

    @expanded_groups.setter
    def expanded_groups(self, value):
        self._expanded_groups = value

    def create_widgets(self):
        """Create the UI elements"""
        # Create search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search field
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Add clear button
        ttk.Button(search_frame, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=5)
        
        # Filter frame for group and semester filtering
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Group filter
        ttk.Label(filter_frame, text="Group:").grid(row=0, column=0, padx=(0, 5))
        self.group_var = tk.StringVar(value="All")
        self.group_combo = ttk.Combobox(filter_frame, textvariable=self.group_var, state="readonly")
        self.group_combo.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Semester filter
        ttk.Label(filter_frame, text="Semester:").grid(row=0, column=2, padx=(10, 5))
        self.semester_var = tk.StringVar(value="All")
        self.semester_combo = ttk.Combobox(filter_frame, textvariable=self.semester_var, state="readonly")
        self.semester_combo.grid(row=0, column=3, padx=5, sticky="ew")
        
        # Favorites filter
        self.show_favorites_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filter_frame, 
            text="Favorites Only", 
            variable=self.show_favorites_var,
            command=self.on_filter_changed
        ).grid(row=0, column=4, padx=(10, 0))
        
        # Configure grid weights
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)
        
        # Populate combo boxes
        self.update_filter_combos()
        
        # Bind events
        self.search_var.trace("w", self.on_search_changed)
        self.group_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        self.semester_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Create scrollable canvas for courses
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create a frame inside the canvas to hold the courses
        self.courses_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.courses_frame, anchor="nw")
        
        # Update scrollregion when the size of the frame changes
        self.courses_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Bind mousewheel for scrolling
        self.bind_mousewheel()
        
        # Set initial expanded groups state
        self._expanded_groups = {}
        
        # Show initial courses
        self.filtered_courses = self.courses.copy()
        self.display_courses()

    def on_frame_configure(self, event=None):
        """Update the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """Resize the inner frame to match the canvas width"""
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def bind_mousewheel(self):
        """Bind mousewheel events to scroll the canvas"""
        # Bind to the canvas itself
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        
        # Bind to the frame containing the courses
        self.courses_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.courses_frame.bind("<Button-4>", self._on_mousewheel)
        self.courses_frame.bind("<Button-5>", self._on_mousewheel)
        
        # Bind to all child widgets recursively
        self._bind_mousewheel_recursive(self.courses_frame)
    
    def _bind_mousewheel_recursive(self, widget):
        """Recursively bind mousewheel events to all children of a widget"""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        
        # Apply to all children recursively
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_mousewheel(self, event):
        """Handle mousewheel events for scrolling"""
        # Different OSes send different events
        delta = 0
        if hasattr(event, 'num') and event.num == 5 or hasattr(event, 'delta') and event.delta < 0:
            delta = 1  # Scroll down
        elif hasattr(event, 'num') and event.num == 4 or hasattr(event, 'delta') and event.delta > 0:
            delta = -1  # Scroll up
            
        self.canvas.yview_scroll(delta, "units")
        return "break"  # Prevent propagation to parent widget
    
    def on_filter_changed(self, event=None):
        """Handle filter change events"""
        # Get filter values
        group_filter = self.group_var.get()
        semester_filter = self.semester_var.get()
        search_text = self.search_var.get().lower()
        favorites_only = self.show_favorites_var.get()
        
        # Apply filters
        self.filtered_courses = []
        for course in self.courses:
            # Check if course has required attributes
            if not hasattr(course, 'title'):
                continue
            
            # Check group filter
            if group_filter != "All" and course.group != group_filter:
                continue
                
            # Check semester filter
            if semester_filter != "All":
                if not hasattr(course, 'semester') or course.semester is None:
                    continue
                if semester_filter not in course.semester:
                    continue
                    
            # Check favorites filter
            if favorites_only and not (hasattr(course, 'favorite') and course.favorite):
                continue
                
            # Check search text
            if search_text:
                # Search in title, description, and module code
                title_match = search_text in course.title.lower()
                desc_match = hasattr(course, 'description') and search_text in course.description.lower()
                code_match = hasattr(course, 'module_code') and search_text in course.module_code.lower()
                group_match = hasattr(course, 'group') and search_text in course.group.lower()
                
                if not (title_match or desc_match or code_match or group_match):
                    continue
                    
            # If all filters passed, add to filtered list
            self.filtered_courses.append(course)
        
        # Display filtered courses
        self.display_courses()
    
    def clear_search(self):
        """Clear the search field and reset filters"""
        self.search_var.set("")
        self.group_var.set("All")
        self.semester_var.set("All")
        self.show_favorites_var.set(False)
        self.filtered_courses = self.courses
        self.display_courses()
    
    def toggle_group(self, group_name, content_frame, toggle_button):
        """Toggle visibility of courses in a group"""
        if self.expanded_groups.get(group_name, True):
            # Collapse group
            content_frame.pack_forget()
            toggle_button.config(text="►")  # Right-pointing triangle
            self.expanded_groups[group_name] = False
        else:
            # Expand group
            content_frame.pack(fill=tk.X, expand=True, padx=5)
            toggle_button.config(text="▼")  # Down-pointing triangle
            self.expanded_groups[group_name] = True
        
        # Update scroll region after toggle
        self.on_frame_configure()
    
    def display_courses(self):
        """Display the filtered courses, grouped by their categories"""
        # Clear the current display
        for widget in self.courses_frame.winfo_children():
            widget.destroy()
        
        # Group courses by their group
        grouped_courses = {}
        for course in self.filtered_courses:
            if not hasattr(course, 'group') or course.group is None:
                if "Uncategorized" not in grouped_courses:
                    grouped_courses["Uncategorized"] = []
                grouped_courses["Uncategorized"].append(course)
            else:
                if course.group not in grouped_courses:
                    grouped_courses[course.group] = []
                grouped_courses[course.group].append(course)
        
        # Display courses by group
        for group_name, courses in sorted(grouped_courses.items()):
            # Create group frame
            group_frame = ttk.Frame(self.courses_frame)
            group_frame.pack(fill=tk.X, expand=True, pady=(5, 0), padx=5)
            
            # Create header frame with toggle button
            header_frame = ttk.Frame(group_frame)
            header_frame.pack(fill=tk.X, expand=True)
            
            # Create a separate frame for the actual course blocks
            content_frame = ttk.Frame(group_frame)
            
            # Create toggle button
            is_expanded = self.expanded_groups.get(group_name, True)  # Default to expanded
            toggle_text = "▼" if is_expanded else "►"  # Down/right arrow
            toggle_button = ttk.Button(
                header_frame, 
                text=toggle_text, 
                width=2,
                command=lambda g=group_name, c=content_frame, b=None: self.toggle_group(g, c, b)
            )
            # Store button reference in the lambda to update later
            toggle_button.configure(command=lambda g=group_name, c=content_frame, b=toggle_button: 
                                 self.toggle_group(g, c, b))
            toggle_button.pack(side=tk.LEFT, padx=(0, 5))
            
            # Group header label
            group_label = ttk.Label(
                header_frame, 
                text=f"{group_name} ({len(courses)} courses)",
                font=("Helvetica", 10, "bold")
            )
            group_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Add courses to the content frame
            for course in courses:
                # Check if this course is already assigned to a semester
                is_placed = hasattr(course, 'assigned_semester') and course.assigned_semester is not None
                
                # Create the course block
                course_block = CourseBlock(content_frame, course, self.drag_drop_manager, is_placed)
                course_block.pack(fill=tk.X, pady=2, padx=2)
            
            # Show content frame only if group is expanded
            if is_expanded:
                content_frame.pack(fill=tk.X, expand=True, padx=5)
            
            # Add a separator after each group
            ttk.Separator(self.courses_frame, orient='horizontal').pack(
                fill=tk.X, padx=5, pady=(5, 10), expand=True
            )
        
        # Update the scroll region
        self.on_frame_configure()
        
        # Re-bind mousewheel events to all new widgets
        self._bind_mousewheel_recursive(self.courses_frame)
    
    def update_filter_combos(self):
        """Update the values in the filter combo boxes"""
        groups = ["All"] + sorted(list(set(course.group for course in self.courses if course.group)))
        self.group_combo["values"] = groups
        
        semesters = ["All", "WiSe", "SoSe", "WiSe/SoSe"]
        self.semester_combo["values"] = semesters
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        self.on_filter_changed()