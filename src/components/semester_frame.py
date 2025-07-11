import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from components.course_block import CourseBlock

class SemesterFrame(tk.Frame):
    def __init__(self, parent, title, max_credits=30, drag_drop_manager=None):
        # Store base dimensions for scaling
        self.base_padx = 5
        self.base_pady = 10
        self.base_borderwidth = 2
        
        # Reduce padding to save space
        super().__init__(parent, padx=self.base_padx, pady=self.base_pady, relief=tk.RAISED, borderwidth=self.base_borderwidth)
        self.title = title
        self.max_credits = max_credits
        self.courses = []
        self.total_credits = 0
        self.drag_drop_manager = drag_drop_manager
        self.course_blocks = {}  # Keep track of course blocks
        
        # Register as a drop target
        if self.drag_drop_manager:
            self.drag_drop_manager.register_drop_target(self)
        
        # Create title label - use smaller font to save space
        self.title_label = tk.Label(self, text=title, font=("Helvetica", 11, "bold"))  # Reduced font size
        self.title_label.pack(fill=tk.X, pady=(0, 3))  # Reduced bottom padding
        
        # Create credits display - use smaller font
        self.credits_label = tk.Label(self, text=f"Credits: 0/{max_credits} LP")
        self.credits_label.pack(fill=tk.X, pady=(0, 3))  # Reduced bottom padding
        
        # Create scrollable frame using standard ttk scrolledframe approach
        self.course_frame = ttk.Frame(self)
        self.course_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar with smaller width
        self.base_canvas_width = 160  # Store base width for scaling
        self.base_canvas_height = 500  # Store base height for scaling
        self.canvas = tk.Canvas(self.course_frame, width=self.base_canvas_width, height=self.base_canvas_height)
        
        # Create scrollbar (always visible)
        self.scrollbar = ttk.Scrollbar(self.course_frame, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas to use the scrollbar - use direct set method, not our custom method
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the canvas FIRST, then the scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a frame to hold the courses
        self.course_container = ttk.Frame(self.canvas)
        
        # Add the course container to the canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.course_container,
            anchor="nw",
            width=self.base_canvas_width-4,
            tags="course_container"
        )
        
        # Configure resize handling
        self.canvas.bind("<Configure>", self._configure_canvas)
        self.course_container.bind("<Configure>", self._configure_scroll_region)
        
        # Configure mousewheel scrolling
        self._bind_mousewheel()
        
        # Set initial scroll region to make scrollbar appear
        self._setup_initial_scroll_region()

    def _setup_initial_scroll_region(self):
        """Set up an initial scroll region to make scrollbar always visible"""
        # Set a large enough scroll region initially
        self.canvas.configure(scrollregion=(0, 0, 0, 1000))
        
        # After the widget is fully created, update the scroll region properly
        self.after(100, self._configure_scroll_region)

    def _scroll_update(self, *args):
        """Custom scroll update that ensures scrollbar visibility"""
        # Apply scrollbar position
        self.scrollbar.set(*args)
        
        # Force the scrollbar to be visible when needed
        if float(args[0]) != 0.0 or float(args[1]) != 1.0:
            # Content needs scrolling
            self.scrollbar.grid()
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_mousewheel(self):
        """Bind mousewheel to canvas for scrolling"""
        def _on_mousewheel(event):
            # Simple scrolling function
            if hasattr(event, 'delta'):
                # Windows - positive delta = scroll up, negative = scroll down
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    # Linux - scroll up
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    # Linux - scroll down
                    self.canvas.yview_scroll(1, "units")
            return "break"
        
        # Remove the bind_all calls to avoid conflicts
        # Instead, bind to specific widgets
        
        # Bind to canvas
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Button-4>", _on_mousewheel)
        self.canvas.bind("<Button-5>", _on_mousewheel)
        
        # Bind to course container
        self.course_container.bind("<MouseWheel>", _on_mousewheel)
        self.course_container.bind("<Button-4>", _on_mousewheel)
        self.course_container.bind("<Button-5>", _on_mousewheel)
        
        # We'll also need to bind to each course block when they're added

    def _configure_canvas(self, event):
        """Update the canvas when it's resized"""
        # Update the width of the window inside the canvas
        self.canvas.itemconfig("course_container", width=event.width)

    def _configure_scroll_region(self, event=None):
        """Update the scroll region when the content changes"""
        # Update the scrollregion to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Force a refresh of the canvas
        self.canvas.update_idletasks()

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
        print(f"Creating course block for {course.title} in {self.title}")
        course_block = CourseBlock(self.course_container, course, self.drag_drop_manager)
        
        # Pack the course block
        course_block.pack(fill=tk.X, pady=3, padx=2)
        print(f"Packed course block, size: {course_block.winfo_reqwidth()}x{course_block.winfo_reqheight()}")
        
        # Apply current scale factor to the new course block if scaling is active
        if hasattr(self, 'scale_factor') and self.scale_factor != 1.0:
            print(f"Applying scale factor {self.scale_factor} to new course block")
            if hasattr(course_block, 'set_scale_factor'):
                course_block.set_scale_factor(self.scale_factor)
        
        # Store a reference to the block for removal
        self.course_blocks[course] = course_block
        
        print(f"Added course block for {course.title}, total blocks: {len(self.course_blocks)}")
        
        # Make sure the course block is visible
        course_block.update_idletasks()
        print(f"Course block actual size after update: {course_block.winfo_width()}x{course_block.winfo_height()}")
        
        # Add mousewheel scrolling to the course block
        def _on_mousewheel(event):
            if hasattr(event, 'delta'):
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
            return "break"
        
        # Bind mousewheel events for all platforms
        course_block.bind("<MouseWheel>", _on_mousewheel)  # Windows
        course_block.bind("<Button-4>", _on_mousewheel)    # Linux scroll up
        course_block.bind("<Button-5>", _on_mousewheel)    # Linux scroll down
        
        # Also bind to all child widgets of the course block
        for child in course_block.winfo_children():
            child.bind("<MouseWheel>", _on_mousewheel)
            child.bind("<Button-4>", _on_mousewheel)
            child.bind("<Button-5>", _on_mousewheel)
        
        # Update the total credits display
        self.update_total_credits()
        
        # Force update of the scroll region to include the new course
        self.course_container.update_idletasks()
        self._configure_scroll_region()
        
        # Ensure canvas window width is properly set after adding course
        if hasattr(self, 'canvas_window'):
            current_width = self.canvas.cget('width')
            # Convert to int if it's a string
            if isinstance(current_width, str):
                current_width = int(current_width)
            self.canvas.itemconfig(self.canvas_window, width=current_width-4)
            print(f"Updated canvas window width to {current_width-4} after adding course")
        
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
        
        # Use the new informative credit display (no restrictions)
        self.update_credits_display()
    
    def update_credits_display(self):
        """Update credits display with informative colors (no restrictions)"""
        if self.total_credits >= 35:
            # High credit load - orange info (not an error, just FYI)
            color = '#ff8c00'  # Orange
            self.credits_label.config(text=f"📊 {self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10, "bold"))
            self.credits_label.config(bg='#fff5e6')  # Light orange background
        elif self.total_credits >= 25:
            # Good range - green
            color = 'green'
            self.credits_label.config(text=f"✓ {self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10))
            self.credits_label.config(bg='#e0ffe0')  # Light green background
        else:
            # Under typical load - blue info
            color = '#1e88e5'  # Blue
            self.credits_label.config(text=f"ℹ️ {self.total_credits}/{self.max_credits} LP", fg=color, font=("Arial", 10))
            self.credits_label.config(bg='#e3f2fd')  # Light blue background

    def scroll_to_bottom(self):
        """Scroll to show the most recently added course"""
        # Get the current scrollregion
        _, _, _, scroll_height = self.canvas.bbox("all") if self.canvas.bbox("all") else (0, 0, 0, 0)
        
        if scroll_height > self.canvas.winfo_height():
            # Calculate position to show the bottom of the content
            # 1.0 means scroll all the way to the bottom
            self.canvas.yview_moveto(1.0)
            print(f"Scrolled to bottom - scroll height: {scroll_height}, visible: {self.canvas.winfo_height()}")

    def create_widgets(self):
        """Create the UI elements"""
        # Create a menu bar
        # ... existing menu code ...
        
        # Create main container as a PanedWindow for resizable sections
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left panel for course list
        left_panel = ttk.Frame(main_container)
        
        # Create course list
        self.course_list = CourseList(left_panel, self.courses, self.drag_drop_manager)
        self.course_list.pack(fill=tk.BOTH, expand=True)
        
        # Create right panel for semesters and requirements
        right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        
        # Add semester panel
        semester_panel = ttk.Frame(right_panel)
        
        # ... existing semester panel code ...
        
        # Add requirements panel (now in the vertical PanedWindow)
        self.requirements_panel = ttk.LabelFrame(right_panel, text="Graduation Requirements")
        
        # Create graduation requirements display
        self.graduation_requirements = GraduationRequirements(self.requirements_panel)
        self.graduation_requirements.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add both panels to the vertical PanedWindow
        right_panel.add(semester_panel, weight=3)  # 75% initial height
        right_panel.add(self.requirements_panel, weight=1)  # 25% initial height
        
        # Add both main panels to the horizontal PanedWindow
        main_container.add(left_panel, weight=1)
        main_container.add(right_panel, weight=3)
        
        # Set initial sash positions after a short delay to ensure widgets are fully loaded
        self.root.update_idletasks()
        self.root.after(100, lambda: main_container.sashpos(0, 280))  # Position horizontal sash
        
        # ... rest of the method ...

    def apply_scaling(self, scale_factor):
        """Apply scaling to this semester frame"""
        # Update canvas size
        base_width = 160
        new_width = int(base_width * scale_factor)
        self.canvas.configure(width=new_width)
        
        # Update canvas window width
        self.canvas.itemconfig(self.canvas_window, width=new_width-4)
        
        # Update fonts for all labels
        try:
            # Update title label font
            current_font = self.winfo_children()[0].cget("font")  # Title label
            if isinstance(current_font, (tuple, list)):
                family, size = current_font[0], current_font[1]
                new_size = max(8, int(size * scale_factor))
                new_font = (family, new_size, "bold")
                self.winfo_children()[0].configure(font=new_font)
            
            # Update credits label font
            current_font = self.winfo_children()[1].cget("font")  # Credits label
            if isinstance(current_font, (tuple, list)):
                family, size = current_font[0], current_font[1]
                new_size = max(8, int(size * scale_factor))
                new_font = (family, new_size)
                self.winfo_children()[1].configure(font=new_font)
        except (IndexError, tk.TclError):
            pass
        
        # Apply scaling to all course blocks
        for course_block in self.course_blocks.values():
            if hasattr(course_block, 'apply_scaling'):
                course_block.apply_scaling(scale_factor)
        
        # Update scroll region
        self.after_idle(self._configure_scroll_region)

    def set_scale_factor(self, scale_factor):
        """Update the semester frame based on scale factor"""
        self.scale_factor = scale_factor
        
        # Scale only the frame's padding and border (not the frame size itself)
        new_padx = max(1, int(self.base_padx * scale_factor))
        new_pady = max(1, int(self.base_pady * scale_factor))
        new_borderwidth = max(1, int(self.base_borderwidth * scale_factor))
        self.configure(padx=new_padx, pady=new_pady, borderwidth=new_borderwidth)
        
        # Only scale the CANVAS dimensions, not the frame itself
        # WIDTH: Scale EXTREMELY aggressively to fit many more columns when zooming out
        # HEIGHT: Keep nearly constant to maintain readability
        
        if scale_factor < 1.0:
            # When zooming out, width scales EXTREMELY aggressively
            width_scale = scale_factor ** 3.0  # EXTREMELY aggressive for zoom out
            new_width = max(30, int(self.base_canvas_width * width_scale))  # Can go VERY narrow
            
            # Height stays nearly constant - only minimal reduction
            height_scale = max(0.85, scale_factor ** 0.3)  # Very minimal height reduction
            new_height = max(400, int(self.base_canvas_height * height_scale))  # Keep height readable
        else:
            # When zooming in, width scales aggressively, height normally
            width_scale = scale_factor ** 1.5  # Aggressive width scaling
            new_width = int(self.base_canvas_width * width_scale)
            
            height_scale = scale_factor  # Normal height scaling
            new_height = int(self.base_canvas_height * height_scale)
        
        # Debug output (can be removed later)
        # print(f"Scaling: factor={scale_factor:.2f}, width_scale={width_scale:.3f}, new_width={new_width}, new_height={new_height}")
        
        self.canvas.configure(width=new_width, height=new_height)
        
        # Update the canvas window width to match the new canvas width
        self.canvas.itemconfig(self.canvas_window, width=new_width-4)
        
        # DO NOT set frame width - let it expand naturally with the canvas
        
        # Update the canvas window width to match the new canvas width
        self.canvas.itemconfig(self.canvas_window, width=new_width-4)
        
        # Update fonts for title and credits labels
        for widget, base_size, style in [
            (self.title_label, 11, "bold"),
            (self.credits_label, 9, "")
        ]:
            try:
                new_size = max(6, int(base_size * scale_factor))
                if style:
                    widget.configure(font=("Helvetica", new_size, style))
                else:
                    widget.configure(font=("Helvetica", new_size))
            except tk.TclError:
                pass
        
        # Update course blocks
        for course_block in self.course_blocks.values():
            if hasattr(course_block, 'set_scale_factor'):
                course_block.set_scale_factor(scale_factor)
        
        # Update layout
        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class GraduationRequirements(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a frame inside the canvas to hold the requirements
        self.content_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure resize handling
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        
        # Build the initial requirements UI
        self._build_requirements_ui()
        
        # Bind mousewheel scrolling
        self._bind_mousewheel()
    
    def _on_canvas_configure(self, event):
        """Update the content frame width when canvas resizes"""
        # Update the width of the inner frame to match the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_frame_configure(self, event):
        """Update the scroll region when the inner frame changes size"""
        # Update the scrollregion to encompass the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _bind_mousewheel(self):
        """Bind mousewheel to canvas for scrolling"""
        def _on_mousewheel(event):
            # Simple scrolling function
            if hasattr(event, 'delta'):
                # Windows - positive delta = scroll up, negative = scroll down
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    # Linux - scroll up
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    # Linux - scroll down
                    self.canvas.yview_scroll(1, "units")
            return "break"
        
        # Bind to canvas
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Button-4>", _on_mousewheel)
        self.canvas.bind("<Button-5>", _on_mousewheel)
        
        # Bind to content frame
        self.content_frame.bind("<MouseWheel>", _on_mousewheel)
        self.content_frame.bind("<Button-4>", _on_mousewheel)
        self.content_frame.bind("<Button-5>", _on_mousewheel)