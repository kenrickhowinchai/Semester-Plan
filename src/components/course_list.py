import tkinter as tk
from tkinter import ttk

from components.course_block import CourseBlock


class CourseList(ttk.Frame):
    def __init__(self, parent, courses, drag_drop_manager, on_add_course=None):
        super().__init__(parent)

        self.courses = courses
        self.drag_drop_manager = drag_drop_manager
        self.on_add_course = on_add_course
        self.filtered_courses = courses
        self._expanded_groups = {}
        self.scale_factor = 1.0

        self.create_widgets()

    @property
    def expanded_groups(self):
        return self._expanded_groups

    @expanded_groups.setter
    def expanded_groups(self, value):
        self._expanded_groups = value

    def create_widgets(self):
        # --- Search bar ---------------------------------------------------
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=6, pady=(6, 2))

        ttk.Label(search_frame, text="Suche:").pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(search_frame, text="\u2715", width=3,
                   command=self.clear_search).pack(side=tk.LEFT)

        # --- Filters ------------------------------------------------------
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=6, pady=2)

        ttk.Label(filter_frame, text="Gruppe:").grid(row=0, column=0, padx=(0, 4))
        self.group_var = tk.StringVar(value="Alle")
        self.group_combo = ttk.Combobox(filter_frame, textvariable=self.group_var,
                                        state="readonly")
        self.group_combo.grid(row=0, column=1, padx=4, sticky="ew")

        ttk.Label(filter_frame, text="Semester:").grid(row=0, column=2, padx=(8, 4))
        self.semester_var = tk.StringVar(value="Alle")
        self.semester_combo = ttk.Combobox(filter_frame, textvariable=self.semester_var,
                                           state="readonly")
        self.semester_combo.grid(row=0, column=3, padx=4, sticky="ew")

        self.show_favorites_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="\u2605 Favoriten",
                        variable=self.show_favorites_var,
                        command=self.on_filter_changed).grid(
            row=0, column=4, padx=(8, 0))

        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)

        self.update_filter_combos()
        self.search_var.trace("w", self.on_search_changed)
        self.group_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        self.semester_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)

        # --- Add-course button --------------------------------------------
        if self.on_add_course:
            add_frame = ttk.Frame(self)
            add_frame.pack(fill=tk.X, padx=6, pady=(2, 4))
            ttk.Button(add_frame, text="\u2795  Kurs hinzuf\u00fcgen",
                       command=self.on_add_course).pack(fill=tk.X)

        # --- Scrollable course list ---------------------------------------
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.courses_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.courses_frame, anchor="nw")

        self.courses_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.bind_mousewheel()

        self._expanded_groups = {}
        self.filtered_courses = self.courses.copy()
        self.display_courses()

    # ------------------------------------------------------------------
    #  Canvas / scroll helpers
    # ------------------------------------------------------------------
    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event=None):
        if event:
            self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mousewheel(self):
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.courses_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.courses_frame.bind("<Button-4>", self._on_mousewheel)
        self.courses_frame.bind("<Button-5>", self._on_mousewheel)
        self._bind_mousewheel_recursive(self.courses_frame)

    def _bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_mousewheel(self, event):
        delta = 0
        if (hasattr(event, 'num') and event.num == 5) or (hasattr(event, 'delta') and event.delta < 0):
            delta = 1
        elif (hasattr(event, 'num') and event.num == 4) or (hasattr(event, 'delta') and event.delta > 0):
            delta = -1
        self.canvas.yview_scroll(delta, "units")
        return "break"

    # ------------------------------------------------------------------
    #  Filtering
    # ------------------------------------------------------------------
    def on_filter_changed(self, event=None):
        group_f = self.group_var.get()
        sem_f = self.semester_var.get()
        search = self.search_var.get().lower()
        fav = self.show_favorites_var.get()

        self.filtered_courses = []
        for c in self.courses:
            if not hasattr(c, 'title'):
                continue
            if group_f not in ("Alle", "All") and c.group != group_f:
                continue
            if sem_f not in ("Alle", "All"):
                if not getattr(c, 'semester', None) or sem_f not in c.semester:
                    continue
            if fav and not getattr(c, 'favorite', False):
                continue
            if search:
                haystack = " ".join([
                    c.title.lower(),
                    getattr(c, 'description', '').lower(),
                    getattr(c, 'module_code', '').lower(),
                    getattr(c, 'group', '').lower()])
                if search not in haystack:
                    continue
            self.filtered_courses.append(c)
        self.display_courses()

    def clear_search(self):
        self.search_var.set("")
        self.group_var.set("Alle")
        self.semester_var.set("Alle")
        self.show_favorites_var.set(False)
        self.filtered_courses = self.courses
        self.display_courses()

    # ------------------------------------------------------------------
    #  Display
    # ------------------------------------------------------------------
    def toggle_group(self, group_name, content_frame, toggle_button):
        if self.expanded_groups.get(group_name, True):
            content_frame.pack_forget()
            toggle_button.config(text="\u25b6")
            self.expanded_groups[group_name] = False
        else:
            content_frame.pack(fill=tk.X, expand=True, padx=4)
            toggle_button.config(text="\u25bc")
            self.expanded_groups[group_name] = True
        self.on_frame_configure()

    def display_courses(self):
        for w in self.courses_frame.winfo_children():
            w.destroy()

        grouped = {}
        for c in self.filtered_courses:
            g = getattr(c, 'group', None) or "Unkategorisiert"
            grouped.setdefault(g, []).append(c)

        for group_name, courses in sorted(grouped.items()):
            group_frame = ttk.Frame(self.courses_frame)
            group_frame.pack(fill=tk.X, expand=True, pady=(4, 0), padx=4)

            header = ttk.Frame(group_frame)
            header.pack(fill=tk.X, expand=True)

            content_frame = ttk.Frame(group_frame)

            is_exp = self.expanded_groups.get(group_name, True)
            toggle_btn = ttk.Button(header, text="\u25bc" if is_exp else "\u25b6",
                                    width=2)
            toggle_btn.configure(
                command=lambda g=group_name, cf=content_frame, b=toggle_btn:
                    self.toggle_group(g, cf, b))
            toggle_btn.pack(side=tk.LEFT, padx=(0, 4))

            ttk.Label(header, text=f"{group_name} ({len(courses)})",
                      font=("Segoe UI", 9, "bold")).pack(
                side=tk.LEFT, fill=tk.X, expand=True)

            for c in courses:
                is_placed = getattr(c, 'assigned_semester', None) is not None
                cb = CourseBlock(content_frame, c, self.drag_drop_manager, is_placed)
                cb.pack(fill=tk.X, pady=2, padx=2)

            if is_exp:
                content_frame.pack(fill=tk.X, expand=True, padx=4)

            ttk.Separator(self.courses_frame, orient='horizontal').pack(
                fill=tk.X, padx=4, pady=(4, 8), expand=True)

        self.on_frame_configure()
        self._bind_mousewheel_recursive(self.courses_frame)

    def update_filter_combos(self):
        groups = ["Alle"] + sorted({c.group for c in self.courses if c.group})
        self.group_combo["values"] = groups
        self.semester_combo["values"] = ["Alle", "WiSe", "SoSe", "WiSe/SoSe"]

    def on_search_changed(self, *args):
        self.on_filter_changed()

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------
    def apply_scaling(self, scale_factor):
        def update_font(widget):
            try:
                cf = widget.cget("font")
                if cf:
                    if isinstance(cf, (tuple, list)) and len(cf) >= 2:
                        fam, sz = cf[0], cf[1]
                        ns = max(8, int(sz * scale_factor))
                        nf = (fam, ns) + (cf[2:] if len(cf) > 2 else ())
                        widget.configure(font=nf)
                    elif isinstance(cf, str):
                        parts = cf.split()
                        if len(parts) >= 2:
                            try:
                                parts[1] = str(max(8, int(int(parts[1]) * scale_factor)))
                                widget.configure(font=" ".join(parts))
                            except ValueError:
                                pass
            except tk.TclError:
                pass
            try:
                for ch in widget.winfo_children():
                    update_font(ch)
            except tk.TclError:
                pass
        update_font(self)

    def set_scale_factor(self, scale_factor):
        self.scale_factor = scale_factor
