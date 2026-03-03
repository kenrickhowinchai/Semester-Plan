import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from components.course_block import CourseBlock


class SemesterFrame(tk.Frame):
    def __init__(self, parent, title, max_credits=30, drag_drop_manager=None):
        # Store base dimensions for scaling
        self.base_padx = 4
        self.base_pady = 6
        self.base_borderwidth = 1

        super().__init__(parent, padx=self.base_padx, pady=self.base_pady,
                         relief=tk.GROOVE, borderwidth=self.base_borderwidth,
                         bg="#FAFAFA")
        self.title = title
        self.max_credits = max_credits
        self.courses = []
        self.total_credits = 0
        self.drag_drop_manager = drag_drop_manager
        self.course_blocks = {}
        self.scale_factor = 1.0

        # Register as a drop target
        if self.drag_drop_manager:
            self.drag_drop_manager.register_drop_target(self)

        # --- Header area --------------------------------------------------
        header_bg = "#E8EAF6"  # Subtle indigo tint
        header_frame = tk.Frame(self, bg=header_bg, padx=6, pady=4)
        header_frame.pack(fill=tk.X)

        self.title_label = tk.Label(
            header_frame, text=title,
            font=("Segoe UI", 11, "bold"), bg=header_bg, fg="#263238")
        self.title_label.pack(side=tk.LEFT)

        self.credits_label = tk.Label(
            header_frame, text="0/30 LP",
            font=("Segoe UI", 10), bg=header_bg, fg="#1565C0")
        self.credits_label.pack(side=tk.RIGHT)

        # --- Scrollable course area ---------------------------------------
        self.course_frame = ttk.Frame(self)
        self.course_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self.base_canvas_width = 160
        self.base_canvas_height = 500
        self.canvas = tk.Canvas(self.course_frame, highlightthickness=0,
                                bg="#FAFAFA")

        self.scrollbar = ttk.Scrollbar(self.course_frame, orient="vertical",
                                       command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.course_container = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.course_container, anchor="nw",
            tags="course_container")

        self.canvas.bind("<Configure>", self._configure_canvas)
        self.course_container.bind("<Configure>", self._configure_scroll_region)
        self._bind_mousewheel()
        self._setup_initial_scroll_region()

    # ------------------------------------------------------------------
    #  Scroll helpers
    # ------------------------------------------------------------------
    def _setup_initial_scroll_region(self):
        self.canvas.configure(scrollregion=(0, 0, 0, 1000))
        self.after(100, self._configure_scroll_region)

    def _bind_mousewheel(self):
        def _on_mousewheel(event):
            if hasattr(event, 'delta'):
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
            return "break"

        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Button-4>", _on_mousewheel)
        self.canvas.bind("<Button-5>", _on_mousewheel)
        self.course_container.bind("<MouseWheel>", _on_mousewheel)
        self.course_container.bind("<Button-4>", _on_mousewheel)
        self.course_container.bind("<Button-5>", _on_mousewheel)

    def _configure_canvas(self, event):
        self.canvas.itemconfig("course_container", width=event.width)

    def _configure_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ------------------------------------------------------------------
    #  Course management
    # ------------------------------------------------------------------
    def add_course(self, course):
        """Add a course to this semester."""
        if hasattr(course, 'semester') and course.semester:
            from components.drag_drop_manager import is_compatible_semester
            if not is_compatible_semester(course.semester, self.title):
                messagebox.showwarning(
                    "Inkompatibles Semester",
                    f"Dieser Kurs ({course.title}) wird nur im "
                    f"{course.semester} angeboten.")
                return False

        if hasattr(course, 'assigned_semester') and course.assigned_semester is not None:
            try:
                course.assigned_semester.remove_course(course)
            except Exception:
                pass

        self.courses.append(course)
        course.assigned_semester = self

        course_block = CourseBlock(self.course_container, course,
                                  self.drag_drop_manager, in_semester=True)
        course_block.pack(fill=tk.X, pady=3, padx=2)

        if hasattr(self, 'scale_factor') and self.scale_factor != 1.0:
            if hasattr(course_block, 'set_scale_factor'):
                course_block.set_scale_factor(self.scale_factor)

        self.course_blocks[course] = course_block

        course_block.update_idletasks()

        # Mousewheel on course block
        def _on_mousewheel(event):
            if hasattr(event, 'delta'):
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
            return "break"

        course_block.bind("<MouseWheel>", _on_mousewheel)
        course_block.bind("<Button-4>", _on_mousewheel)
        course_block.bind("<Button-5>", _on_mousewheel)
        for child in course_block.winfo_children():
            child.bind("<MouseWheel>", _on_mousewheel)
            child.bind("<Button-4>", _on_mousewheel)
            child.bind("<Button-5>", _on_mousewheel)

        self.update_total_credits()
        self.course_container.update_idletasks()
        self._configure_scroll_region()

        self.after_idle(self.scroll_to_bottom)

        if (self.drag_drop_manager
                and hasattr(self.drag_drop_manager, 'app')
                and hasattr(self.drag_drop_manager.app, 'course_list')):
            self.drag_drop_manager.app.course_list.display_courses()

        if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
            self.drag_drop_manager.app.update_graduation_requirements()

        return True

    def remove_course(self, course):
        """Remove a course from this semester."""
        if course in self.courses:
            self.courses.remove(course)
            course.assigned_semester = None

            if course in self.course_blocks:
                self.course_blocks[course].destroy()
                del self.course_blocks[course]

            self.update_total_credits()
            self.after_idle(self._configure_scroll_region)

            if (self.drag_drop_manager
                    and hasattr(self.drag_drop_manager, 'app')
                    and hasattr(self.drag_drop_manager.app, 'course_list')):
                self.drag_drop_manager.app.course_list.display_courses()

            if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
                self.drag_drop_manager.app.update_graduation_requirements()
            return True
        return False

    # ------------------------------------------------------------------
    #  Credits display
    # ------------------------------------------------------------------
    def update_total_credits(self):
        self.total_credits = sum(c.credits for c in self.courses)
        self.update_credits_display()

    def update_credits_display(self):
        if self.total_credits >= 35:
            color = '#E65100'
            self.credits_label.config(
                text=f"{self.total_credits}/{self.max_credits} LP",
                fg=color, font=("Segoe UI", 10, "bold"), bg='#FFF3E0')
        elif self.total_credits >= 25:
            color = '#2E7D32'
            self.credits_label.config(
                text=f"{self.total_credits}/{self.max_credits} LP",
                fg=color, font=("Segoe UI", 10), bg='#E8F5E9')
        else:
            color = '#1565C0'
            self.credits_label.config(
                text=f"{self.total_credits}/{self.max_credits} LP",
                fg=color, font=("Segoe UI", 10), bg='#E3F2FD')

    def scroll_to_bottom(self):
        bbox = self.canvas.bbox("all")
        if bbox:
            _, _, _, scroll_height = bbox
            if scroll_height > self.canvas.winfo_height():
                self.canvas.yview_moveto(1.0)

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------
    def apply_scaling(self, scale_factor):
        base_width = 160
        new_width = int(base_width * scale_factor)
        self.canvas.configure(width=new_width)
        self.canvas.itemconfig(self.canvas_window, width=max(1, new_width - 4))

        try:
            self.title_label.configure(
                font=("Segoe UI", max(8, int(11 * scale_factor)), "bold"))
            self.credits_label.configure(
                font=("Segoe UI", max(8, int(10 * scale_factor))))
        except tk.TclError:
            pass

        for cb in self.course_blocks.values():
            if hasattr(cb, 'apply_scaling'):
                cb.apply_scaling(scale_factor)
        self.after_idle(self._configure_scroll_region)

    def set_scale_factor(self, scale_factor):
        self.scale_factor = scale_factor

        new_padx = max(1, int(self.base_padx * scale_factor))
        new_pady = max(1, int(self.base_pady * scale_factor))
        new_bw = max(1, int(self.base_borderwidth * scale_factor))
        self.configure(padx=new_padx, pady=new_pady, borderwidth=new_bw)

        # Smooth scaling — linear with a floor
        width_scale = max(0.5, scale_factor)
        new_width = max(80, int(self.base_canvas_width * width_scale))

        height_scale = max(0.7, scale_factor)
        new_height = max(300, int(self.base_canvas_height * height_scale))

        self.canvas.configure(width=new_width, height=new_height)
        self.canvas.itemconfig(self.canvas_window, width=max(1, new_width - 4))

        for widget, base_size, style in [
            (self.title_label, 11, "bold"),
            (self.credits_label, 10, ""),
        ]:
            try:
                new_size = max(7, int(base_size * scale_factor))
                if style:
                    widget.configure(font=("Segoe UI", new_size, style))
                else:
                    widget.configure(font=("Segoe UI", new_size))
            except tk.TclError:
                pass

        for cb in self.course_blocks.values():
            if hasattr(cb, 'set_scale_factor'):
                cb.set_scale_factor(scale_factor)

        self.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
